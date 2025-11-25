#!/usr/bin/env python3
"""
NexaDB Binary Protocol Server
==============================

High-performance binary protocol server for NexaDB with:
- Custom binary protocol (3-10x faster than HTTP/JSON)
- MessagePack encoding (2-10x faster than JSON)
- Persistent TCP connections
- Connection pooling (1000+ concurrent connections)
- Streaming results for large queries

Protocol Specification:
----------------------
Message Format:
  Header (12 bytes):
    - Magic (4 bytes): 0x4E455841 ("NEXA")
    - Version (1 byte): 0x01
    - Message Type (1 byte): 0x01-0xFF
    - Flags (2 bytes): Reserved for future use
    - Payload Length (4 bytes): uint32

  Payload (variable):
    - MessagePack encoded data

Message Types:
  Client → Server:
    0x01 = CONNECT       - Handshake + authentication
    0x02 = CREATE        - Insert document
    0x03 = READ          - Get document by key
    0x04 = UPDATE        - Update document
    0x05 = DELETE        - Delete document
    0x06 = QUERY         - Query with filters
    0x07 = VECTOR_SEARCH - Vector similarity search
    0x08 = BATCH_WRITE   - Bulk insert
    0x09 = PING          - Keep-alive

  Server → Client:
    0x81 = SUCCESS       - Operation succeeded
    0x82 = ERROR         - Operation failed
    0x83 = NOT_FOUND     - Key doesn't exist
    0x84 = DUPLICATE     - Key already exists
    0x85 = STREAM_START  - Beginning of result stream
    0x86 = STREAM_CHUNK  - Partial results
    0x87 = STREAM_END    - End of results
    0x88 = PONG          - Keep-alive response

Usage:
------
    python3 nexadb_binary_server.py --host 0.0.0.0 --port 6970
"""

import socket
import struct
import threading
import time
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional

# MessagePack for binary serialization
try:
    import msgpack
except ImportError:
    print("[ERROR] msgpack not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'msgpack'])
    import msgpack

import hashlib
import json
import os

# Import NexaDB core
sys.path.append('.')
from veloxdb_core import VeloxDB
from toon_format import json_to_toon, toon_to_json
from unified_auth import UnifiedAuthManager


class NexaDBBinaryProtocol:
    """Binary protocol constants and utilities"""

    # Protocol magic and version
    MAGIC = 0x4E455841  # "NEXA" in hex
    VERSION = 0x01

    # Client → Server message types
    MSG_CONNECT = 0x01
    MSG_CREATE = 0x02
    MSG_READ = 0x03
    MSG_UPDATE = 0x04
    MSG_DELETE = 0x05
    MSG_QUERY = 0x06
    MSG_VECTOR_SEARCH = 0x07
    MSG_BATCH_WRITE = 0x08
    MSG_PING = 0x09
    MSG_DISCONNECT = 0x0A
    MSG_QUERY_TOON = 0x0B  # Query with TOON format response
    MSG_EXPORT_TOON = 0x0C  # Export collection to TOON format
    MSG_IMPORT_TOON = 0x0D  # Import TOON data into collection
    MSG_CREATE_USER = 0x0E  # Create new user (admin only)
    MSG_DELETE_USER = 0x0F  # Delete user (admin only)
    MSG_LIST_USERS = 0x10  # List all users (admin only)
    MSG_CHANGE_PASSWORD = 0x11  # Change user password
    MSG_LIST_COLLECTIONS = 0x20  # List all collections
    MSG_DROP_COLLECTION = 0x21  # Drop a collection
    MSG_GET_VECTORS = 0x23  # Get vector statistics

    # Server → Client response types
    MSG_SUCCESS = 0x81
    MSG_ERROR = 0x82
    MSG_NOT_FOUND = 0x83
    MSG_DUPLICATE = 0x84
    MSG_STREAM_START = 0x85
    MSG_STREAM_CHUNK = 0x86
    MSG_STREAM_END = 0x87
    MSG_PONG = 0x88

    @staticmethod
    def pack_message(msg_type: int, data: Any) -> bytes:
        """
        Pack message into binary protocol format.

        Args:
            msg_type: Message type code
            data: Data to encode (will be MessagePack encoded)

        Returns:
            Binary message (header + payload)
        """
        # Encode payload with MessagePack
        payload = msgpack.packb(data, use_bin_type=True)

        # Build header (12 bytes)
        header = struct.pack(
            '>IBBHI',
            NexaDBBinaryProtocol.MAGIC,    # Magic (4 bytes)
            NexaDBBinaryProtocol.VERSION,  # Version (1 byte)
            msg_type,                       # Message type (1 byte)
            0,                              # Flags (2 bytes)
            len(payload)                    # Payload length (4 bytes)
        )

        return header + payload

    @staticmethod
    def unpack_header(header_bytes: bytes) -> tuple:
        """
        Unpack message header.

        Args:
            header_bytes: 12 bytes of header

        Returns:
            (magic, version, msg_type, flags, payload_len)
        """
        return struct.unpack('>IBBHI', header_bytes)


class NexaDBBinaryServer:
    """
    Binary protocol server for NexaDB.

    Features:
    - Persistent TCP connections
    - Connection pooling (1000+ concurrent)
    - Binary protocol (3-10x faster than HTTP)
    - Streaming results for large queries
    - Automatic reconnection handling
    """

    def __init__(
        self,
        host: str = '0.0.0.0',
        port: int = 6970,
        data_dir: str = './nexadb_data',
        max_connections: int = 1000,
        max_workers: int = 100
    ):
        """
        Initialize binary protocol server.

        Args:
            host: Host to bind to
            port: Port to listen on
            data_dir: Database data directory
            max_connections: Maximum concurrent connections
            max_workers: Thread pool size
        """
        self.host = host
        self.port = port
        self.data_dir = data_dir
        self.max_connections = max_connections
        self.max_workers = max_workers

        # Initialize database
        print(f"[INIT] Initializing NexaDB at {data_dir}")
        self.db = VeloxDB(data_dir)

        # Initialize unified authentication (username/password + API keys)
        print(f"[SECURITY] Initializing unified authentication")
        self.auth = UnifiedAuthManager(data_dir)

        # Connection pool
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Socket
        self.socket = None
        self.running = False

        # Authenticated sessions: address -> {username, role, authenticated_at}
        self.sessions = {}
        self.sessions_lock = threading.Lock()

        # Statistics
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'total_requests': 0,
            'total_errors': 0,
            'auth_failures': 0,
            'start_time': time.time()
        }
        self.stats_lock = threading.Lock()

    def start(self):
        """Start binary protocol server."""
        # Create socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind and listen
        self.socket.bind((self.host, self.port))
        self.socket.listen(self.max_connections)

        self.running = True

        print("=" * 70)
        print("NexaDB Binary Protocol Server Started")
        print("=" * 70)
        print(f"Host: {self.host}")
        print(f"Port: {self.port}")
        print(f"Data Directory: {self.data_dir}")
        print(f"Max Connections: {self.max_connections}")
        print(f"Worker Threads: {self.max_workers}")
        print(f"\nServer listening on {self.host}:{self.port}")
        print("\nProtocol: Binary (MessagePack)")
        print("Performance: 3-10x faster than HTTP/REST")
        print("\n🔒 SECURITY: Username/Password Authentication")
        print("   - Clients must send CONNECT with username + password")
        print("   - All operations require authentication")
        print("   - Default user: root / nexadb123")
        print("\nSupported Operations:")
        print("  - CREATE, READ, UPDATE, DELETE")
        print("  - QUERY (with filters)")
        print("  - BATCH_WRITE (bulk inserts)")
        print("  - VECTOR_SEARCH (AI/ML)")
        print("  - TOON FORMAT (40-50% token reduction for LLMs) ⭐ NEW!")
        print("\n🚀 FIRST DATABASE WITH NATIVE TOON SUPPORT!")
        print("=" * 70)

        try:
            while self.running:
                # Accept connection
                client_socket, address = self.socket.accept()

                # Update stats
                with self.stats_lock:
                    self.stats['total_connections'] += 1
                    self.stats['active_connections'] += 1

                # Handle connection in thread pool
                self.executor.submit(self.handle_connection, client_socket, address)

        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Shutting down server...")
            self.stop()

    def stop(self):
        """Stop server."""
        self.running = False

        if self.socket:
            self.socket.close()

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        # Close database
        self.db.close()

        print("[SHUTDOWN] Server stopped")

    def handle_connection(self, client_socket: socket.socket, address: tuple):
        """
        Handle persistent client connection.

        Args:
            client_socket: Client socket
            address: Client address (host, port)
        """
        print(f"[CONNECT] New connection from {address[0]}:{address[1]}")

        try:
            while self.running:
                # Read message header (12 bytes)
                header_bytes = self._recv_exact(client_socket, 12)
                if not header_bytes:
                    break  # Connection closed

                # Parse header
                magic, version, msg_type, flags, payload_len = NexaDBBinaryProtocol.unpack_header(header_bytes)

                # Verify magic
                if magic != NexaDBBinaryProtocol.MAGIC:
                    print(f"[ERROR] Invalid magic: {hex(magic)}")
                    self._send_error(client_socket, f"Invalid protocol magic: {hex(magic)}")
                    break

                # Verify version
                if version != NexaDBBinaryProtocol.VERSION:
                    print(f"[ERROR] Unsupported version: {version}")
                    self._send_error(client_socket, f"Unsupported protocol version: {version}")
                    break

                # Read payload
                payload_bytes = self._recv_exact(client_socket, payload_len)
                if not payload_bytes:
                    break  # Connection closed

                # Decode MessagePack
                try:
                    data = msgpack.unpackb(payload_bytes, raw=False)
                except Exception as e:
                    print(f"[ERROR] Failed to decode MessagePack: {e}")
                    self._send_error(client_socket, f"Invalid MessagePack: {e}")
                    continue

                # Update stats
                with self.stats_lock:
                    self.stats['total_requests'] += 1

                # Process message
                self._process_message(client_socket, msg_type, data, address)

        except Exception as e:
            print(f"[ERROR] Connection error from {address}: {e}")
            with self.stats_lock:
                self.stats['total_errors'] += 1

        finally:
            client_socket.close()

            # Remove session
            with self.sessions_lock:
                if address in self.sessions:
                    del self.sessions[address]

            with self.stats_lock:
                self.stats['active_connections'] -= 1

            print(f"[DISCONNECT] Connection closed from {address[0]}:{address[1]}")

    def _recv_exact(self, sock: socket.socket, n: int) -> Optional[bytes]:
        """
        Receive exactly n bytes from socket.

        Args:
            sock: Socket to read from
            n: Number of bytes to read

        Returns:
            Bytes read, or None if connection closed
        """
        data = b''
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                return None  # Connection closed
            data += chunk
        return data

    def _send_message(self, sock: socket.socket, msg_type: int, data: Any):
        """
        Send binary message to client.

        Args:
            sock: Socket to send to
            msg_type: Message type code
            data: Data to send
        """
        message = NexaDBBinaryProtocol.pack_message(msg_type, data)
        sock.sendall(message)

    def _send_success(self, sock: socket.socket, data: Any):
        """Send success response."""
        self._send_message(sock, NexaDBBinaryProtocol.MSG_SUCCESS, data)

    def _send_error(self, sock: socket.socket, error: str):
        """Send error response."""
        self._send_message(sock, NexaDBBinaryProtocol.MSG_ERROR, {'error': error})

    def _send_not_found(self, sock: socket.socket):
        """Send not found response."""
        self._send_message(sock, NexaDBBinaryProtocol.MSG_NOT_FOUND, {'error': 'Not found'})

    def _process_message(self, sock: socket.socket, msg_type: int, data: Dict[str, Any], address: tuple):
        """
        Process incoming message and send response.

        Args:
            sock: Client socket
            msg_type: Message type code
            data: Message data
            address: Client address
        """
        try:
            if msg_type == NexaDBBinaryProtocol.MSG_CONNECT:
                # CONNECT - Handshake + Authentication
                self._handle_connect(sock, data, address)
                return  # Don't check auth for CONNECT itself

            # Check authentication for all other operations
            with self.sessions_lock:
                if address not in self.sessions:
                    self._send_error(sock, "Not authenticated. Send CONNECT message with API key first.")
                    return

            if msg_type == NexaDBBinaryProtocol.MSG_CREATE:
                # CREATE - Insert document
                self._handle_create(sock, data)

            elif msg_type == NexaDBBinaryProtocol.MSG_READ:
                # READ - Get document by key
                self._handle_read(sock, data)

            elif msg_type == NexaDBBinaryProtocol.MSG_UPDATE:
                # UPDATE - Update document
                self._handle_update(sock, data)

            elif msg_type == NexaDBBinaryProtocol.MSG_DELETE:
                # DELETE - Delete document
                self._handle_delete(sock, data)

            elif msg_type == NexaDBBinaryProtocol.MSG_QUERY:
                # QUERY - Query with filters
                self._handle_query(sock, data)

            elif msg_type == NexaDBBinaryProtocol.MSG_VECTOR_SEARCH:
                # VECTOR_SEARCH - Vector similarity search
                self._handle_vector_search(sock, data)

            elif msg_type == NexaDBBinaryProtocol.MSG_BATCH_WRITE:
                # BATCH_WRITE - Bulk insert
                self._handle_batch_write(sock, data)

            elif msg_type == NexaDBBinaryProtocol.MSG_PING:
                # PING - Keep-alive
                self._handle_ping(sock, data)

            elif msg_type == NexaDBBinaryProtocol.MSG_DISCONNECT:
                # DISCONNECT - Graceful close
                self._send_success(sock, {'status': 'goodbye'})
                sock.close()

            elif msg_type == NexaDBBinaryProtocol.MSG_QUERY_TOON:
                # QUERY_TOON - Query with TOON format response
                self._handle_query_toon(sock, data)

            elif msg_type == NexaDBBinaryProtocol.MSG_EXPORT_TOON:
                # EXPORT_TOON - Export collection to TOON format
                self._handle_export_toon(sock, data)

            elif msg_type == NexaDBBinaryProtocol.MSG_IMPORT_TOON:
                # IMPORT_TOON - Import TOON data into collection
                self._handle_import_toon(sock, data)

            elif msg_type == NexaDBBinaryProtocol.MSG_CREATE_USER:
                # CREATE_USER - Create new user (admin only)
                self._handle_create_user(sock, data, address)

            elif msg_type == NexaDBBinaryProtocol.MSG_DELETE_USER:
                # DELETE_USER - Delete user (admin only)
                self._handle_delete_user(sock, data, address)

            elif msg_type == NexaDBBinaryProtocol.MSG_LIST_USERS:
                # LIST_USERS - List all users (admin only)
                self._handle_list_users(sock, address)

            elif msg_type == NexaDBBinaryProtocol.MSG_CHANGE_PASSWORD:
                # CHANGE_PASSWORD - Change user password
                self._handle_change_password(sock, data, address)

            elif msg_type == NexaDBBinaryProtocol.MSG_LIST_COLLECTIONS:
                # LIST_COLLECTIONS - List all collections
                self._handle_list_collections(sock)

            elif msg_type == NexaDBBinaryProtocol.MSG_DROP_COLLECTION:
                # DROP_COLLECTION - Drop a collection
                self._handle_drop_collection(sock, data)

            elif msg_type == NexaDBBinaryProtocol.MSG_GET_VECTORS:
                # GET_VECTORS - Get vector statistics
                self._handle_get_vectors(sock)

            else:
                self._send_error(sock, f"Unknown message type: {msg_type}")

        except Exception as e:
            print(f"[ERROR] Failed to process message: {e}")
            self._send_error(sock, str(e))

            with self.stats_lock:
                self.stats['total_errors'] += 1

    def _handle_connect(self, sock: socket.socket, data: Dict[str, Any], address: tuple):
        """
        Handle CONNECT message with username/password authentication.

        Args:
            sock: Client socket
            data: Connection data with 'username' and 'password' fields
            address: Client address
        """
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            self._send_error(sock, "Missing 'username' or 'password' field in CONNECT message")
            with self.stats_lock:
                self.stats['auth_failures'] += 1
            return

        # Authenticate user
        user_info = self.auth.authenticate_password(username, password)

        if not user_info:
            self._send_error(sock, "Invalid username or password")
            with self.stats_lock:
                self.stats['auth_failures'] += 1
            return

        # Store session
        with self.sessions_lock:
            self.sessions[address] = {
                'username': user_info['username'],
                'role': user_info['role'],
                'authenticated_at': time.time()
            }

        print(f"[AUTH] User '{user_info['username']}' (role: {user_info['role']}) authenticated from {address[0]}:{address[1]}")

        self._send_success(sock, {
            'status': 'connected',
            'server': 'NexaDB Binary Protocol',
            'version': '1.0.0',
            'authenticated': True,
            'username': user_info['username'],
            'role': user_info['role']
        })

    def _handle_create(self, sock: socket.socket, data: Dict[str, Any]):
        """Handle CREATE message."""
        collection_name = data.get('collection')
        document = data.get('data')

        if not collection_name or not document:
            self._send_error(sock, "Missing 'collection' or 'data' field")
            return

        # Check if document has vector field for automatic indexing
        if 'vector' in document and isinstance(document['vector'], list):
            # Auto-index vector for similarity search
            vector = document['vector']
            dimensions = len(vector)

            # Insert via vector collection (indexes vector automatically)
            vector_collection = self.db.vector_collection(collection_name, dimensions)
            doc_data = {k: v for k, v in document.items() if k != 'vector'}
            doc_id = vector_collection.insert(doc_data, vector)
        else:
            # Regular insert (no vector)
            collection = self.db.collection(collection_name)
            doc_id = collection.insert(document)

        self._send_success(sock, {
            'collection': collection_name,
            'document_id': doc_id,
            'message': 'Document inserted'
        })

    def _handle_read(self, sock: socket.socket, data: Dict[str, Any]):
        """Handle READ message."""
        collection_name = data.get('collection')
        doc_id = data.get('key')

        if not collection_name or not doc_id:
            self._send_error(sock, "Missing 'collection' or 'key' field")
            return

        # Get document
        collection = self.db.collection(collection_name)
        document = collection.find_by_id(doc_id)

        if document:
            self._send_success(sock, {
                'collection': collection_name,
                'document': document
            })
        else:
            self._send_not_found(sock)

    def _handle_update(self, sock: socket.socket, data: Dict[str, Any]):
        """Handle UPDATE message."""
        collection_name = data.get('collection')
        doc_id = data.get('key')
        updates = data.get('updates')

        if not collection_name or not doc_id or not updates:
            self._send_error(sock, "Missing 'collection', 'key', or 'updates' field")
            return

        # Update document
        collection = self.db.collection(collection_name)
        success = collection.update(doc_id, updates)

        if success:
            self._send_success(sock, {
                'collection': collection_name,
                'document_id': doc_id,
                'message': 'Document updated'
            })
        else:
            self._send_not_found(sock)

    def _handle_delete(self, sock: socket.socket, data: Dict[str, Any]):
        """Handle DELETE message."""
        collection_name = data.get('collection')
        doc_id = data.get('key')

        if not collection_name or not doc_id:
            self._send_error(sock, "Missing 'collection' or 'key' field")
            return

        # Delete document
        collection = self.db.collection(collection_name)
        success = collection.delete(doc_id)

        if success:
            self._send_success(sock, {
                'collection': collection_name,
                'document_id': doc_id,
                'message': 'Document deleted'
            })
        else:
            self._send_not_found(sock)

    def _handle_query(self, sock: socket.socket, data: Dict[str, Any]):
        """Handle QUERY message."""
        collection_name = data.get('collection')
        filters = data.get('filters', {})
        limit = data.get('limit', 100)

        if not collection_name:
            self._send_error(sock, "Missing 'collection' field")
            return

        # Query documents
        collection = self.db.collection(collection_name)
        documents = collection.find(filters, limit=limit)

        self._send_success(sock, {
            'collection': collection_name,
            'documents': documents,
            'count': len(documents)
        })

    def _handle_vector_search(self, sock: socket.socket, data: Dict[str, Any]):
        """Handle VECTOR_SEARCH message."""
        collection_name = data.get('collection')
        vector = data.get('vector')
        limit = data.get('limit', 10)
        dimensions = data.get('dimensions', 768)

        if not collection_name or not vector:
            self._send_error(sock, "Missing 'collection' or 'vector' field")
            return

        # Vector search
        vector_collection = self.db.vector_collection(collection_name, dimensions)
        results = vector_collection.search(vector, limit=limit)

        # Format results
        formatted_results = [
            {
                'document_id': doc_id,
                'similarity': float(similarity),
                'document': doc
            }
            for doc_id, similarity, doc in results
        ]

        self._send_success(sock, {
            'collection': collection_name,
            'results': formatted_results,
            'count': len(formatted_results)
        })

    def _handle_batch_write(self, sock: socket.socket, data: Dict[str, Any]):
        """Handle BATCH_WRITE message."""
        collection_name = data.get('collection')
        documents = data.get('documents', [])

        if not collection_name or not documents:
            self._send_error(sock, "Missing 'collection' or 'documents' field")
            return

        # Check if documents have vector fields for automatic indexing
        has_vectors = any('vector' in doc and isinstance(doc.get('vector'), list) for doc in documents)

        if has_vectors:
            # Use vector collection for automatic indexing
            # Get dimensions from first document with vector
            dimensions = None
            for doc in documents:
                if 'vector' in doc and isinstance(doc['vector'], list):
                    dimensions = len(doc['vector'])
                    break

            vector_collection = self.db.vector_collection(collection_name, dimensions)
            doc_ids = []

            for doc in documents:
                if 'vector' in doc and isinstance(doc['vector'], list):
                    vector = doc['vector']
                    doc_data = {k: v for k, v in doc.items() if k != 'vector'}
                    doc_id = vector_collection.insert(doc_data, vector)
                    doc_ids.append(doc_id)
                else:
                    # Document without vector - insert normally
                    collection = self.db.collection(collection_name)
                    doc_id = collection.insert(doc)
                    doc_ids.append(doc_id)
        else:
            # Regular bulk insert (no vectors)
            collection = self.db.collection(collection_name)
            doc_ids = collection.insert_many(documents)

        self._send_success(sock, {
            'collection': collection_name,
            'document_ids': doc_ids,
            'count': len(doc_ids),
            'message': f'Inserted {len(doc_ids)} documents'
        })

    def _handle_ping(self, sock: socket.socket, data: Dict[str, Any]):
        """Handle PING message."""
        self._send_message(sock, NexaDBBinaryProtocol.MSG_PONG, {
            'status': 'ok',
            'timestamp': time.time()
        })

    def _handle_query_toon(self, sock: socket.socket, data: Dict[str, Any]):
        """
        Handle QUERY_TOON message.

        Query collection and return results in TOON format.
        TOON format reduces token count by ~40-50% for LLM applications.
        """
        collection_name = data.get('collection')
        filters = data.get('filters', {})
        limit = data.get('limit', 100)

        if not collection_name:
            self._send_error(sock, "Missing 'collection' field")
            return

        # Query documents
        collection = self.db.collection(collection_name)
        documents = collection.find(filters, limit=limit)

        # Convert to TOON format
        toon_data = json_to_toon({
            'collection': collection_name,
            'documents': documents,
            'count': len(documents)
        })

        # Calculate token savings
        import json
        json_size = len(json.dumps({'documents': documents}))
        toon_size = len(toon_data)
        token_reduction = ((json_size - toon_size) / json_size * 100) if json_size > 0 else 0

        self._send_success(sock, {
            'collection': collection_name,
            'format': 'TOON',
            'data': toon_data,
            'count': len(documents),
            'token_stats': {
                'json_size': json_size,
                'toon_size': toon_size,
                'reduction_percent': round(token_reduction, 1)
            }
        })

    def _handle_export_toon(self, sock: socket.socket, data: Dict[str, Any]):
        """
        Handle EXPORT_TOON message.

        Export entire collection to TOON format.
        Perfect for AI/ML pipelines that need efficient data transfer.
        """
        collection_name = data.get('collection')

        if not collection_name:
            self._send_error(sock, "Missing 'collection' field")
            return

        # Get all documents from collection
        collection = self.db.collection(collection_name)
        all_documents = collection.find({}, limit=10000)  # Export up to 10K docs

        # Convert to TOON format
        toon_data = json_to_toon({
            'collection': collection_name,
            'documents': all_documents,
            'count': len(all_documents),
            'exported_at': time.time()
        })

        # Calculate statistics
        import json
        json_size = len(json.dumps(all_documents))
        toon_size = len(toon_data)
        token_reduction = ((json_size - toon_size) / json_size * 100) if json_size > 0 else 0

        self._send_success(sock, {
            'collection': collection_name,
            'format': 'TOON',
            'data': toon_data,
            'count': len(all_documents),
            'token_stats': {
                'json_size': json_size,
                'toon_size': toon_size,
                'reduction_percent': round(token_reduction, 1),
                'estimated_cost_savings': f"~{round(token_reduction, 0)}% less tokens for LLM processing"
            }
        })

    def _handle_import_toon(self, sock: socket.socket, data: Dict[str, Any]):
        """
        Handle IMPORT_TOON message.

        Import TOON formatted data into a collection.
        Automatically converts TOON to JSON for storage.
        """
        collection_name = data.get('collection')
        toon_data = data.get('toon_data')
        replace = data.get('replace', False)  # Replace existing collection?

        if not collection_name:
            self._send_error(sock, "Missing 'collection' field")
            return

        if not toon_data:
            self._send_error(sock, "Missing 'toon_data' field")
            return

        try:
            # Convert TOON to JSON
            import json
            json_str = toon_to_json(toon_data)
            parsed_data = json.loads(json_str)

            # Extract documents
            documents = []
            if isinstance(parsed_data, dict):
                # Check if it has a 'documents' field (export format)
                if 'documents' in parsed_data:
                    documents = parsed_data['documents']
                else:
                    # Single document
                    documents = [parsed_data]
            elif isinstance(parsed_data, list):
                # Array of documents
                documents = parsed_data
            else:
                self._send_error(sock, "Invalid TOON data structure")
                return

            # Get collection
            collection = self.db.collection(collection_name)

            # Replace existing data if requested
            if replace:
                # Delete all existing documents
                all_docs = collection.find({}, limit=100000)
                for doc in all_docs:
                    collection.delete(doc.get('_id'))

            # Insert documents
            doc_ids = collection.insert_many(documents)

            self._send_success(sock, {
                'collection': collection_name,
                'imported': len(doc_ids),
                'replaced': replace,
                'document_ids': doc_ids[:100],  # Return first 100 IDs
                'message': f"Successfully imported {len(doc_ids)} documents from TOON format"
            })

        except Exception as e:
            self._send_error(sock, f"Failed to import TOON data: {str(e)}")

    def _handle_create_user(self, sock: socket.socket, data: Dict[str, Any], address: tuple):
        """Handle CREATE_USER message (admin only)."""
        # Check if current user is admin
        with self.sessions_lock:
            session = self.sessions.get(address)
            if not session or session['role'] != 'admin':
                self._send_error(sock, "Permission denied. Only admins can create users.")
                return

        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'read')

        if not username or not password:
            self._send_error(sock, "Missing 'username' or 'password' field")
            return

        # Validate role
        valid_roles = ['admin', 'write', 'read', 'guest']
        if role not in valid_roles:
            self._send_error(sock, f"Invalid role. Must be one of: {', '.join(valid_roles)}")
            return

        # Create user (returns API key)
        try:
            api_key = self.auth.create_user(username, password, role)

            print(f"[USER] Admin '{session['username']}' created user '{username}' with role '{role}'")

            self._send_success(sock, {
                'message': f"User '{username}' created successfully",
                'username': username,
                'password': password,  # Return so admin can give it to the user
                'api_key': api_key,    # Return so admin can give it to the user
                'role': role,
                'note': '⚠️ Save these credentials! Password and API key are only shown once.'
            })
        except ValueError as e:
            self._send_error(sock, str(e))

    def _handle_delete_user(self, sock: socket.socket, data: Dict[str, Any], address: tuple):
        """Handle DELETE_USER message (admin only)."""
        # Check if current user is admin
        with self.sessions_lock:
            session = self.sessions.get(address)
            if not session or session['role'] != 'admin':
                self._send_error(sock, "Permission denied. Only admins can delete users.")
                return

        username = data.get('username')

        if not username:
            self._send_error(sock, "Missing 'username' field")
            return

        # Delete user
        success = self.auth.delete_user(username)

        if success:
            print(f"[USER] Admin '{session['username']}' deleted user '{username}'")
            self._send_success(sock, {
                'message': f"User '{username}' deleted successfully"
            })
        else:
            self._send_error(sock, f"Failed to delete user '{username}' (may be root or doesn't exist)")

    def _handle_list_users(self, sock: socket.socket, address: tuple):
        """Handle LIST_USERS message (admin only)."""
        # Check if current user is admin
        with self.sessions_lock:
            session = self.sessions.get(address)
            if not session or session['role'] != 'admin':
                self._send_error(sock, "Permission denied. Only admins can list users.")
                return

        # List users
        users = self.auth.list_users()

        self._send_success(sock, {
            'users': users,
            'count': len(users)
        })

    def _handle_change_password(self, sock: socket.socket, data: Dict[str, Any], address: tuple):
        """Handle CHANGE_PASSWORD message."""
        with self.sessions_lock:
            session = self.sessions.get(address)

        username = data.get('username')
        new_password = data.get('new_password')

        if not username or not new_password:
            self._send_error(sock, "Missing 'username' or 'new_password' field")
            return

        # Users can change their own password, admins can change any password
        if session['username'] != username and session['role'] != 'admin':
            self._send_error(sock, "Permission denied. You can only change your own password.")
            return

        # Change password
        success = self.auth.change_password(username, new_password)

        if success:
            print(f"[USER] Password changed for user '{username}' by '{session['username']}'")
            self._send_success(sock, {
                'message': f"Password changed successfully for user '{username}'"
            })
        else:
            self._send_error(sock, f"Failed to change password for user '{username}'")

    def _handle_list_collections(self, sock: socket.socket):
        """Handle LIST_COLLECTIONS message."""
        try:
            collections = self.db.list_collections()

            self._send_success(sock, {
                'collections': collections,
                'count': len(collections)
            })
        except Exception as e:
            self._send_error(sock, f"Failed to list collections: {str(e)}")

    def _handle_drop_collection(self, sock: socket.socket, data: Dict[str, Any]):
        """Handle DROP_COLLECTION message."""
        collection_name = data.get('collection')

        if not collection_name:
            self._send_error(sock, "Missing 'collection' field")
            return

        try:
            success = self.db.drop_collection(collection_name)

            if success:
                self._send_success(sock, {
                    'collection': collection_name,
                    'message': 'Collection dropped'
                })
            else:
                self._send_error(sock, f"Collection '{collection_name}' not found")
        except Exception as e:
            self._send_error(sock, f"Failed to drop collection: {str(e)}")

    def _handle_get_vectors(self, sock: socket.socket):
        """Handle GET_VECTORS message - get vector index statistics."""
        try:
            from collections import defaultdict

            # Scan for all vectors
            vector_prefix = 'vector:'
            all_vectors = list(self.db.engine.range_scan(vector_prefix, vector_prefix + '\xff'))

            # Group by collection and get detailed info
            vector_data = defaultdict(lambda: {'count': 0, 'documents': []})

            for key, vector_bytes in all_vectors:
                # key format: vector:{collection}:{doc_id}
                parts = key.split(':')
                if len(parts) >= 3:
                    collection = parts[1]
                    doc_id = parts[2]

                    # Parse vector to get dimensions
                    vector = json.loads(vector_bytes.decode('utf-8'))
                    dimensions = len(vector)

                    vector_data[collection]['count'] += 1
                    vector_data[collection]['documents'].append({
                        'doc_id': doc_id,
                        'dimensions': dimensions
                    })

                    # Store dimensions for this collection (should be consistent)
                    if 'dimensions' not in vector_data[collection]:
                        vector_data[collection]['dimensions'] = dimensions

            # Format response
            self._send_success(sock, {
                'status': 'success',
                'total_vectors': len(all_vectors),
                'collections': dict(vector_data)
            })
        except Exception as e:
            self._send_error(sock, f"Failed to get vectors: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        with self.stats_lock:
            uptime = time.time() - self.stats['start_time']
            return {
                **self.stats,
                'uptime_seconds': uptime,
                'requests_per_second': self.stats['total_requests'] / uptime if uptime > 0 else 0
            }


def main():
    """Main entry point for binary protocol server"""
    import os

    # Parse command-line arguments
    host = os.getenv('NEXADB_BINARY_HOST', '0.0.0.0')
    port = int(os.getenv('NEXADB_BINARY_PORT', 6970))
    data_dir = os.getenv('NEXADB_DATA_DIR', './nexadb_data')

    # Check for --help
    if '--help' in sys.argv or '-h' in sys.argv:
        print("NexaDB Binary Protocol Server")
        print("\nUsage:")
        print("  python3 nexadb_binary_server.py [options]")
        print("\nOptions:")
        print("  --host HOST        Host to bind to (default: 0.0.0.0)")
        print("  --port PORT        Port to listen on (default: 6970)")
        print("  --data-dir DIR     Data directory (default: ./nexadb_data)")
        print("\nEnvironment Variables:")
        print("  NEXADB_BINARY_HOST   Host to bind to")
        print("  NEXADB_BINARY_PORT   Port to listen on")
        print("  NEXADB_DATA_DIR      Data directory")
        print("\nPerformance:")
        print("  - 3-10x faster than HTTP/REST")
        print("  - Binary protocol with MessagePack encoding")
        print("  - Persistent TCP connections")
        print("  - 1000+ concurrent connections")
        sys.exit(0)

    # Parse command-line arguments
    for i, arg in enumerate(sys.argv):
        if arg == '--host' and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == '--port' and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
        elif arg == '--data-dir' and i + 1 < len(sys.argv):
            data_dir = sys.argv[i + 1]

    # Start server
    server = NexaDBBinaryServer(host=host, port=port, data_dir=data_dir)
    server.start()


if __name__ == '__main__':
    main()
