/**
 * NexaDB YCSB Binding
 *
 * YCSB binding for NexaDB NoSQL database using the binary protocol (MessagePack over TCP).
 *
 * Configuration properties:
 *   nexadb.host       - NexaDB server hostname (default: localhost)
 *   nexadb.port       - NexaDB binary protocol port (default: 6970)
 *   nexadb.username   - Username for authentication (default: root)
 *   nexadb.password   - Password for authentication (default: nexadb123)
 *   nexadb.timeout    - Connection timeout in ms (default: 30000)
 *   nexadb.retries    - Max retry attempts (default: 3)
 *   nexadb.database   - Database name for multi-db support (default: default)
 *   nexadb.debug      - Enable debug logging (default: false)
 */
package site.ycsb.db;

import site.ycsb.ByteIterator;
import site.ycsb.DB;
import site.ycsb.DBException;
import site.ycsb.Status;
import site.ycsb.StringByteIterator;

import java.util.*;

public class NexaDBClient extends DB {

    // Configuration property keys
    public static final String HOST_PROPERTY = "nexadb.host";
    public static final String PORT_PROPERTY = "nexadb.port";
    public static final String USERNAME_PROPERTY = "nexadb.username";
    public static final String PASSWORD_PROPERTY = "nexadb.password";
    public static final String TIMEOUT_PROPERTY = "nexadb.timeout";
    public static final String RETRIES_PROPERTY = "nexadb.retries";
    public static final String DATABASE_PROPERTY = "nexadb.database";
    public static final String DEBUG_PROPERTY = "nexadb.debug";

    // Default values
    public static final String DEFAULT_HOST = "localhost";
    public static final String DEFAULT_PORT = "6970";
    public static final String DEFAULT_USERNAME = "root";
    public static final String DEFAULT_PASSWORD = "nexadb123";
    public static final String DEFAULT_TIMEOUT = "30000";
    public static final String DEFAULT_RETRIES = "3";
    public static final String DEFAULT_DATABASE = "default";

    // NexaDB connection
    private NexaDBConnection connection;
    private String database;
    private boolean debug;

    /**
     * Initialize the NexaDB client connection.
     */
    @Override
    public void init() throws DBException {
        Properties props = getProperties();

        String host = props.getProperty(HOST_PROPERTY, DEFAULT_HOST);
        int port = Integer.parseInt(props.getProperty(PORT_PROPERTY, DEFAULT_PORT));
        String username = props.getProperty(USERNAME_PROPERTY, DEFAULT_USERNAME);
        String password = props.getProperty(PASSWORD_PROPERTY, DEFAULT_PASSWORD);
        int timeout = Integer.parseInt(props.getProperty(TIMEOUT_PROPERTY, DEFAULT_TIMEOUT));
        int retries = Integer.parseInt(props.getProperty(RETRIES_PROPERTY, DEFAULT_RETRIES));
        database = props.getProperty(DATABASE_PROPERTY, DEFAULT_DATABASE);
        debug = Boolean.parseBoolean(props.getProperty(DEBUG_PROPERTY, "false"));

        try {
            connection = new NexaDBConnection(host, port, username, password, timeout, retries);
            connection.connect();

            if (debug) {
                System.out.println("[NexaDB] Connected to " + host + ":" + port);
            }

        } catch (NexaDBException e) {
            throw new DBException("Failed to connect to NexaDB: " + e.getMessage(), e);
        }
    }

    /**
     * Read a single record from the database.
     *
     * @param table  The name of the table/collection
     * @param key    The record key to read
     * @param fields The fields to read, or null for all fields
     * @param result A map to populate with field/value pairs
     * @return Status.OK on success, Status.ERROR on failure, Status.NOT_FOUND if not exists
     */
    @Override
    public Status read(String table, String key, Set<String> fields,
                       Map<String, ByteIterator> result) {
        try {
            Map<String, Object> data = new HashMap<>();
            data.put("collection", table);
            data.put("key", key);
            if (database != null && !database.equals("default")) {
                data.put("database", database);
            }

            Map<String, Object> response = connection.sendMessage(NexaDBConnection.MSG_READ, data);

            @SuppressWarnings("unchecked")
            Map<String, Object> document = (Map<String, Object>) response.get("document");

            if (document == null) {
                return Status.NOT_FOUND;
            }

            // Convert document fields to ByteIterators
            if (fields == null) {
                // Return all fields
                for (Map.Entry<String, Object> entry : document.entrySet()) {
                    String fieldName = entry.getKey();
                    // Skip internal fields
                    if (!fieldName.startsWith("_")) {
                        result.put(fieldName, new StringByteIterator(
                                entry.getValue() != null ? entry.getValue().toString() : ""));
                    }
                }
            } else {
                // Return only requested fields
                for (String field : fields) {
                    Object value = document.get(field);
                    if (value != null) {
                        result.put(field, new StringByteIterator(value.toString()));
                    }
                }
            }

            if (debug) {
                System.out.println("[NexaDB] READ " + table + "/" + key + " -> " + result.size() + " fields");
            }

            return Status.OK;

        } catch (NexaDBException e) {
            if (e.getMessage() != null && e.getMessage().contains("Not found")) {
                return Status.NOT_FOUND;
            }
            if (debug) {
                System.err.println("[NexaDB] READ error: " + e.getMessage());
            }
            return Status.ERROR;
        }
    }

    /**
     * Perform a range scan starting from a specific key.
     *
     * @param table       The name of the table/collection
     * @param startkey    The key to start scanning from
     * @param recordcount The number of records to return
     * @param fields      The fields to return, or null for all fields
     * @param result      A vector to populate with record maps
     * @return Status.OK on success, Status.ERROR on failure
     */
    @Override
    public Status scan(String table, String startkey, int recordcount,
                       Set<String> fields, Vector<HashMap<String, ByteIterator>> result) {
        try {
            // Use query with filter for range scan
            // NexaDB uses MongoDB-style queries
            Map<String, Object> filters = new HashMap<>();
            Map<String, Object> gteFilter = new HashMap<>();
            gteFilter.put("$gte", startkey);
            filters.put("_id", gteFilter);

            Map<String, Object> data = new HashMap<>();
            data.put("collection", table);
            data.put("filters", filters);
            data.put("limit", recordcount);
            if (database != null && !database.equals("default")) {
                data.put("database", database);
            }

            Map<String, Object> response = connection.sendMessage(NexaDBConnection.MSG_QUERY, data);

            @SuppressWarnings("unchecked")
            List<Map<String, Object>> documents = (List<Map<String, Object>>) response.get("documents");

            if (documents != null) {
                for (Map<String, Object> doc : documents) {
                    HashMap<String, ByteIterator> row = new HashMap<>();

                    if (fields == null) {
                        // Return all fields
                        for (Map.Entry<String, Object> entry : doc.entrySet()) {
                            String fieldName = entry.getKey();
                            if (!fieldName.startsWith("_")) {
                                row.put(fieldName, new StringByteIterator(
                                        entry.getValue() != null ? entry.getValue().toString() : ""));
                            }
                        }
                    } else {
                        // Return only requested fields
                        for (String field : fields) {
                            Object value = doc.get(field);
                            if (value != null) {
                                row.put(field, new StringByteIterator(value.toString()));
                            }
                        }
                    }

                    result.add(row);
                }
            }

            if (debug) {
                System.out.println("[NexaDB] SCAN " + table + " from " + startkey +
                        " limit " + recordcount + " -> " + result.size() + " records");
            }

            return Status.OK;

        } catch (NexaDBException e) {
            if (debug) {
                System.err.println("[NexaDB] SCAN error: " + e.getMessage());
            }
            return Status.ERROR;
        }
    }

    /**
     * Insert a new record into the database.
     *
     * @param table  The name of the table/collection
     * @param key    The record key
     * @param values A map of field/value pairs to insert
     * @return Status.OK on success, Status.ERROR on failure
     */
    @Override
    public Status insert(String table, String key, Map<String, ByteIterator> values) {
        try {
            // Convert ByteIterators to strings
            Map<String, Object> document = new HashMap<>();
            document.put("_id", key);  // Use YCSB key as document ID

            for (Map.Entry<String, ByteIterator> entry : values.entrySet()) {
                document.put(entry.getKey(), entry.getValue().toString());
            }

            Map<String, Object> data = new HashMap<>();
            data.put("collection", table);
            data.put("data", document);
            if (database != null && !database.equals("default")) {
                data.put("database", database);
            }

            connection.sendMessage(NexaDBConnection.MSG_CREATE, data);

            if (debug) {
                System.out.println("[NexaDB] INSERT " + table + "/" + key + " (" + values.size() + " fields)");
            }

            return Status.OK;

        } catch (NexaDBException e) {
            if (debug) {
                System.err.println("[NexaDB] INSERT error: " + e.getMessage());
            }
            return Status.ERROR;
        }
    }

    /**
     * Update an existing record in the database.
     *
     * @param table  The name of the table/collection
     * @param key    The record key
     * @param values A map of field/value pairs to update
     * @return Status.OK on success, Status.ERROR on failure
     */
    @Override
    public Status update(String table, String key, Map<String, ByteIterator> values) {
        try {
            // Convert ByteIterators to strings
            Map<String, Object> updates = new HashMap<>();
            for (Map.Entry<String, ByteIterator> entry : values.entrySet()) {
                updates.put(entry.getKey(), entry.getValue().toString());
            }

            Map<String, Object> data = new HashMap<>();
            data.put("collection", table);
            data.put("key", key);
            data.put("updates", updates);
            if (database != null && !database.equals("default")) {
                data.put("database", database);
            }

            connection.sendMessage(NexaDBConnection.MSG_UPDATE, data);

            if (debug) {
                System.out.println("[NexaDB] UPDATE " + table + "/" + key + " (" + values.size() + " fields)");
            }

            return Status.OK;

        } catch (NexaDBException e) {
            if (debug) {
                System.err.println("[NexaDB] UPDATE error: " + e.getMessage());
            }
            return Status.ERROR;
        }
    }

    /**
     * Delete a record from the database.
     *
     * @param table The name of the table/collection
     * @param key   The record key to delete
     * @return Status.OK on success, Status.ERROR on failure
     */
    @Override
    public Status delete(String table, String key) {
        try {
            Map<String, Object> data = new HashMap<>();
            data.put("collection", table);
            data.put("key", key);
            if (database != null && !database.equals("default")) {
                data.put("database", database);
            }

            connection.sendMessage(NexaDBConnection.MSG_DELETE, data);

            if (debug) {
                System.out.println("[NexaDB] DELETE " + table + "/" + key);
            }

            return Status.OK;

        } catch (NexaDBException e) {
            if (debug) {
                System.err.println("[NexaDB] DELETE error: " + e.getMessage());
            }
            return Status.ERROR;
        }
    }

    /**
     * Cleanup resources.
     */
    @Override
    public void cleanup() throws DBException {
        if (connection != null) {
            if (debug) {
                System.out.println("[NexaDB] Closing connection. Queries: " +
                        connection.getQueriesExecuted() + ", Errors: " +
                        connection.getErrorsEncountered());
            }
            connection.close();
        }
    }
}
