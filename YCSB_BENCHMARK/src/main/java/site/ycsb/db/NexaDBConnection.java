/**
 * NexaDB Binary Protocol Connection
 *
 * Implements the NexaDB binary protocol over TCP using MessagePack.
 * Thread-safe with automatic reconnection support.
 *
 * Protocol Format:
 * Header (12 bytes):
 *   - Magic: 0x4E455841 ("NEXA") - 4 bytes, big-endian
 *   - Version: 0x01 - 1 byte
 *   - Message Type: 0xXX - 1 byte
 *   - Flags: 0x0000 - 2 bytes
 *   - Payload Length: uint32 - 4 bytes, big-endian
 * Payload (N bytes):
 *   - MessagePack encoded data
 */
package site.ycsb.db;

import org.msgpack.core.MessagePack;
import org.msgpack.core.MessageBufferPacker;
import org.msgpack.core.MessageUnpacker;
import org.msgpack.value.Value;
import org.msgpack.value.MapValue;
import org.msgpack.value.ArrayValue;

import java.io.*;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.ByteBuffer;
import java.util.*;
import java.util.concurrent.locks.ReentrantLock;

public class NexaDBConnection implements AutoCloseable {

    // Protocol constants
    private static final int MAGIC = 0x4E455841;  // "NEXA"
    private static final byte VERSION = 0x01;
    private static final int HEADER_SIZE = 12;

    // Message types (Client → Server)
    public static final byte MSG_CONNECT = 0x01;
    public static final byte MSG_CREATE = 0x02;
    public static final byte MSG_READ = 0x03;
    public static final byte MSG_UPDATE = 0x04;
    public static final byte MSG_DELETE = 0x05;
    public static final byte MSG_QUERY = 0x06;
    public static final byte MSG_VECTOR_SEARCH = 0x07;
    public static final byte MSG_BATCH_WRITE = 0x08;
    public static final byte MSG_PING = 0x09;

    // Response types (Server → Client)
    public static final byte MSG_SUCCESS = (byte) 0x81;
    public static final byte MSG_ERROR = (byte) 0x82;
    public static final byte MSG_NOT_FOUND = (byte) 0x83;
    public static final byte MSG_PONG = (byte) 0x88;

    // Connection settings
    private final String host;
    private final int port;
    private final String username;
    private final String password;
    private final int timeout;
    private final int maxRetries;

    // Socket state
    private Socket socket;
    private DataInputStream input;
    private DataOutputStream output;
    private volatile boolean connected = false;
    private final ReentrantLock lock = new ReentrantLock();

    // Statistics
    private long queriesExecuted = 0;
    private long errorsEncountered = 0;

    public NexaDBConnection(String host, int port, String username, String password,
                            int timeout, int maxRetries) {
        this.host = host;
        this.port = port;
        this.username = username;
        this.password = password;
        this.timeout = timeout;
        this.maxRetries = maxRetries;
    }

    /**
     * Establish connection and authenticate.
     */
    public void connect() throws NexaDBException {
        lock.lock();
        try {
            if (connected) {
                return;
            }

            Exception lastError = null;
            for (int attempt = 0; attempt < maxRetries; attempt++) {
                try {
                    // Create socket
                    socket = new Socket(host, port);
                    socket.setSoTimeout(timeout);
                    socket.setTcpNoDelay(true);

                    input = new DataInputStream(new BufferedInputStream(socket.getInputStream()));
                    output = new DataOutputStream(new BufferedOutputStream(socket.getOutputStream()));

                    // Authenticate
                    authenticate();

                    connected = true;
                    return;

                } catch (Exception e) {
                    lastError = e;
                    closeQuietly();

                    if (attempt < maxRetries - 1) {
                        // Exponential backoff
                        try {
                            Thread.sleep((long) (100 * Math.pow(2, attempt)));
                        } catch (InterruptedException ie) {
                            Thread.currentThread().interrupt();
                            throw new NexaDBException("Connection interrupted", ie);
                        }
                    }
                }
            }

            errorsEncountered++;
            throw new NexaDBException("Failed to connect after " + maxRetries + " attempts", lastError);

        } finally {
            lock.unlock();
        }
    }

    /**
     * Send authentication handshake.
     */
    private void authenticate() throws NexaDBException {
        Map<String, Object> authData = new HashMap<>();
        authData.put("username", username);
        authData.put("password", password);

        try {
            Map<String, Object> response = sendMessageInternal(MSG_CONNECT, authData);

            Object authenticated = response.get("authenticated");
            if (authenticated == null || !(authenticated instanceof Boolean) || !(Boolean) authenticated) {
                throw new NexaDBException("Authentication failed for user: " + username);
            }
        } catch (IOException e) {
            throw new NexaDBException("Authentication failed: " + e.getMessage(), e);
        }
    }

    /**
     * Send message with automatic reconnection.
     */
    public Map<String, Object> sendMessage(byte msgType, Map<String, Object> data) throws NexaDBException {
        lock.lock();
        try {
            ensureConnected();

            for (int attempt = 0; attempt < maxRetries; attempt++) {
                try {
                    Map<String, Object> result = sendMessageInternal(msgType, data);
                    queriesExecuted++;
                    return result;

                } catch (IOException e) {
                    connected = false;
                    if (attempt < maxRetries - 1) {
                        try {
                            connect();
                        } catch (NexaDBException reconnectError) {
                            // Continue to next attempt
                        }
                    } else {
                        errorsEncountered++;
                        throw new NexaDBException("Operation failed after " + maxRetries + " attempts", e);
                    }
                }
            }

            throw new NexaDBException("Failed to send message");

        } finally {
            lock.unlock();
        }
    }

    /**
     * Internal send/receive implementation.
     */
    private Map<String, Object> sendMessageInternal(byte msgType, Map<String, Object> data)
            throws NexaDBException, IOException {

        // Encode payload with MessagePack
        byte[] payload = packMap(data);

        // Build and send header (12 bytes)
        ByteBuffer header = ByteBuffer.allocate(HEADER_SIZE);
        header.putInt(MAGIC);           // 4 bytes - magic
        header.put(VERSION);            // 1 byte - version
        header.put(msgType);            // 1 byte - message type
        header.putShort((short) 0);     // 2 bytes - flags
        header.putInt(payload.length);  // 4 bytes - payload length

        output.write(header.array());
        output.write(payload);
        output.flush();

        // Read response
        return readResponse();
    }

    /**
     * Read response from server.
     */
    private Map<String, Object> readResponse() throws NexaDBException, IOException {
        // Read header
        byte[] headerBytes = new byte[HEADER_SIZE];
        input.readFully(headerBytes);

        ByteBuffer header = ByteBuffer.wrap(headerBytes);
        int magic = header.getInt();
        byte version = header.get();
        byte msgType = header.get();
        short flags = header.getShort();
        int payloadLen = header.getInt();

        // Verify magic
        if (magic != MAGIC) {
            throw new NexaDBException("Invalid protocol magic: " + Integer.toHexString(magic));
        }

        // Read payload
        byte[] payload = new byte[payloadLen];
        input.readFully(payload);

        // Decode MessagePack
        Map<String, Object> response = unpackMap(payload);

        // Handle response type
        if (msgType == MSG_SUCCESS || msgType == MSG_PONG) {
            return response;
        } else if (msgType == MSG_ERROR) {
            String error = (String) response.getOrDefault("error", "Unknown error");
            throw new NexaDBException(error);
        } else if (msgType == MSG_NOT_FOUND) {
            throw new NexaDBException("Not found");
        } else {
            throw new NexaDBException("Unknown response type: " + msgType);
        }
    }

    /**
     * Pack a Map to MessagePack bytes.
     */
    private byte[] packMap(Map<String, Object> map) throws IOException {
        MessageBufferPacker packer = MessagePack.newDefaultBufferPacker();
        packValue(packer, map);
        return packer.toByteArray();
    }

    /**
     * Recursively pack a value.
     */
    @SuppressWarnings("unchecked")
    private void packValue(MessageBufferPacker packer, Object value) throws IOException {
        if (value == null) {
            packer.packNil();
        } else if (value instanceof String) {
            packer.packString((String) value);
        } else if (value instanceof Integer) {
            packer.packInt((Integer) value);
        } else if (value instanceof Long) {
            packer.packLong((Long) value);
        } else if (value instanceof Double) {
            packer.packDouble((Double) value);
        } else if (value instanceof Float) {
            packer.packFloat((Float) value);
        } else if (value instanceof Boolean) {
            packer.packBoolean((Boolean) value);
        } else if (value instanceof byte[]) {
            byte[] bytes = (byte[]) value;
            packer.packBinaryHeader(bytes.length);
            packer.writePayload(bytes);
        } else if (value instanceof Map) {
            Map<String, Object> map = (Map<String, Object>) value;
            packer.packMapHeader(map.size());
            for (Map.Entry<String, Object> entry : map.entrySet()) {
                packer.packString(entry.getKey());
                packValue(packer, entry.getValue());
            }
        } else if (value instanceof List) {
            List<?> list = (List<?>) value;
            packer.packArrayHeader(list.size());
            for (Object item : list) {
                packValue(packer, item);
            }
        } else {
            // Fallback to string representation
            packer.packString(value.toString());
        }
    }

    /**
     * Unpack MessagePack bytes to a Map.
     */
    private Map<String, Object> unpackMap(byte[] data) throws IOException {
        MessageUnpacker unpacker = MessagePack.newDefaultUnpacker(data);
        Value value = unpacker.unpackValue();
        return valueToMap(value);
    }

    /**
     * Convert MessagePack Value to Java Map.
     */
    private Map<String, Object> valueToMap(Value value) {
        if (!value.isMapValue()) {
            return new HashMap<>();
        }

        MapValue mapValue = value.asMapValue();
        Map<String, Object> result = new HashMap<>();

        for (Map.Entry<Value, Value> entry : mapValue.entrySet()) {
            String key = entry.getKey().asStringValue().asString();
            result.put(key, valueToObject(entry.getValue()));
        }

        return result;
    }

    /**
     * Convert MessagePack Value to Java Object.
     */
    private Object valueToObject(Value value) {
        if (value.isNilValue()) {
            return null;
        } else if (value.isBooleanValue()) {
            return value.asBooleanValue().getBoolean();
        } else if (value.isIntegerValue()) {
            return value.asIntegerValue().toLong();
        } else if (value.isFloatValue()) {
            return value.asFloatValue().toDouble();
        } else if (value.isStringValue()) {
            return value.asStringValue().asString();
        } else if (value.isBinaryValue()) {
            return value.asBinaryValue().asByteArray();
        } else if (value.isArrayValue()) {
            ArrayValue arrayValue = value.asArrayValue();
            List<Object> list = new ArrayList<>(arrayValue.size());
            for (Value item : arrayValue) {
                list.add(valueToObject(item));
            }
            return list;
        } else if (value.isMapValue()) {
            return valueToMap(value);
        }
        return value.toString();
    }

    private void ensureConnected() throws NexaDBException {
        if (!connected) {
            connect();
        }
    }

    private void closeQuietly() {
        try {
            if (input != null) input.close();
        } catch (Exception e) { /* ignore */ }
        try {
            if (output != null) output.close();
        } catch (Exception e) { /* ignore */ }
        try {
            if (socket != null) socket.close();
        } catch (Exception e) { /* ignore */ }

        input = null;
        output = null;
        socket = null;
        connected = false;
    }

    @Override
    public void close() {
        lock.lock();
        try {
            closeQuietly();
        } finally {
            lock.unlock();
        }
    }

    public boolean isConnected() {
        return connected;
    }

    public long getQueriesExecuted() {
        return queriesExecuted;
    }

    public long getErrorsEncountered() {
        return errorsEncountered;
    }
}
