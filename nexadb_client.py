#!/usr/bin/env python3
"""
NexaDB Production Client
========================

Enterprise-grade Python client for NexaDB with MySQL-level reliability.

Designed with the philosophy of Linux, MySQL, and PostgreSQL:
- Simple, elegant, bulletproof
- Production-ready error handling
- Automatic reconnection
- Connection pooling
- Thread-safe operations

Author: Anthropic Claude (inspired by Linus Torvalds & MySQL team)
License: MIT
"""

import socket
import struct
import threading
import time
import queue
from typing import Dict, Any, List, Optional, Tuple
from queue import Queue, Empty
import msgpack


# Protocol constants
MAGIC = 0x4E455841  # "NEXA"
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
MSG_QUERY_TOON = 0x0B
MSG_EXPORT_TOON = 0x0C
MSG_IMPORT_TOON = 0x0D
MSG_CREATE_USER = 0x0E
MSG_DELETE_USER = 0x0F
MSG_LIST_USERS = 0x10
MSG_CHANGE_PASSWORD = 0x11

# Extended operations (admin panel needs these)
MSG_LIST_COLLECTIONS = 0x20
MSG_DROP_COLLECTION = 0x21
MSG_COLLECTION_STATS = 0x22
MSG_GET_VECTORS = 0x23

# Change stream operations (MongoDB-style)
MSG_SUBSCRIBE_CHANGES = 0x30
MSG_UNSUBSCRIBE_CHANGES = 0x31

# Server → Client response types
MSG_SUCCESS = 0x81
MSG_ERROR = 0x82
MSG_NOT_FOUND = 0x83
MSG_DUPLICATE = 0x84
MSG_PONG = 0x88
MSG_CHANGE_EVENT = 0x90  # Server pushes change events


class NexaDBError(Exception):
    """Base exception for NexaDB errors."""
    pass


class ConnectionError(NexaDBError):
    """Connection-related errors."""
    pass


class AuthenticationError(NexaDBError):
    """Authentication failures."""
    pass


class OperationError(NexaDBError):
    """Operation failures."""
    pass


class NexaDBConnection:
    """
    Single persistent connection to NexaDB.

    Thread-safe, automatically reconnects on failure.
    Designed like MySQL's connection handling.
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6970,
        username: str = 'root',
        password: str = 'nexadb123',
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize connection.

        Args:
            host: Server host
            port: Server port
            username: Username for authentication
            password: Password for authentication
            timeout: Socket timeout in seconds
            max_retries: Max reconnection attempts
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.max_retries = max_retries

        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.lock = threading.RLock()  # Re-entrant lock for thread safety

        # Statistics (like MySQL SHOW STATUS)
        self.stats = {
            'connections_made': 0,
            'queries_executed': 0,
            'errors_encountered': 0,
            'reconnections': 0
        }

    def connect(self) -> None:
        """
        Establish connection to server.

        Raises:
            ConnectionError: If connection fails after retries
            AuthenticationError: If authentication fails
        """
        with self.lock:
            if self.connected:
                return

            last_error = None
            for attempt in range(self.max_retries):
                try:
                    # Create socket
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.settimeout(self.timeout)
                    self.socket.connect((self.host, self.port))

                    # Authenticate
                    self._send_connect()

                    self.connected = True
                    self.stats['connections_made'] += 1

                    if attempt > 0:
                        self.stats['reconnections'] += 1
                        print(f"[RECONNECT] Successfully reconnected after {attempt} attempts")

                    return

                except Exception as e:
                    last_error = e
                    if self.socket:
                        try:
                            self.socket.close()
                        except:
                            pass
                        self.socket = None

                    if attempt < self.max_retries - 1:
                        # Exponential backoff: 0.1s, 0.2s, 0.4s, ...
                        sleep_time = 0.1 * (2 ** attempt)
                        time.sleep(sleep_time)

            # All retries failed
            self.stats['errors_encountered'] += 1
            raise ConnectionError(
                f"Failed to connect to NexaDB at {self.host}:{self.port} "
                f"after {self.max_retries} attempts: {last_error}"
            )

    def disconnect(self) -> None:
        """Close connection gracefully."""
        with self.lock:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                finally:
                    self.socket = None
                    self.connected = False

    def _ensure_connected(self) -> None:
        """Ensure connection is active, reconnect if needed."""
        if not self.connected:
            self.connect()

    def _send_connect(self) -> None:
        """Send authentication handshake."""
        response = self._send_message_internal(MSG_CONNECT, {
            'username': self.username,
            'password': self.password
        })

        if not response.get('authenticated'):
            raise AuthenticationError(f"Authentication failed for user '{self.username}'")

    def _send_message_internal(self, msg_type: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send binary message and receive response (internal, no locking).

        Args:
            msg_type: Message type code
            data: Message data

        Returns:
            Response data

        Raises:
            ConnectionError: If not connected
            OperationError: If server returns error
        """
        if not self.socket:
            raise ConnectionError("Not connected")

        # Encode payload with MessagePack
        payload = msgpack.packb(data, use_bin_type=True)

        # Build header (12 bytes)
        header = struct.pack(
            '>IBBHI',
            MAGIC,       # Magic (4 bytes)
            VERSION,     # Version (1 byte)
            msg_type,    # Message type (1 byte)
            0,           # Flags (2 bytes)
            len(payload) # Payload length (4 bytes)
        )

        # Send header + payload
        self.socket.sendall(header + payload)

        # Read response
        return self._read_response()

    def send_message(self, msg_type: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send binary message with automatic reconnection.

        Args:
            msg_type: Message type code
            data: Message data

        Returns:
            Response data

        Raises:
            ConnectionError: If connection fails
            OperationError: If operation fails
        """
        with self.lock:
            self._ensure_connected()

            # Try sending with automatic reconnection
            for attempt in range(self.max_retries):
                try:
                    result = self._send_message_internal(msg_type, data)
                    self.stats['queries_executed'] += 1
                    return result

                except (BrokenPipeError, OSError, ConnectionError) as e:
                    # Connection lost, try to reconnect
                    self.connected = False
                    if attempt < self.max_retries - 1:
                        print(f"[RECONNECT] Connection lost, attempting reconnect ({attempt + 1}/{self.max_retries})")
                        try:
                            self.connect()
                        except:
                            pass
                    else:
                        self.stats['errors_encountered'] += 1
                        raise ConnectionError(f"Operation failed after {self.max_retries} attempts: {e}")

            self.stats['errors_encountered'] += 1
            raise ConnectionError("Failed to send message after all retries")

    def _read_response(self) -> Dict[str, Any]:
        """
        Read binary response from server.

        Returns:
            Response data

        Raises:
            ConnectionError: If connection closed
            OperationError: If server returns error
        """
        # Read header (12 bytes)
        header = self._recv_exact(12)

        magic, version, msg_type, flags, payload_len = struct.unpack('>IBBHI', header)

        # Verify magic
        if magic != MAGIC:
            raise ValueError(f"Invalid protocol magic: {hex(magic)}")

        # Read payload
        payload = self._recv_exact(payload_len)

        # Decode MessagePack
        data = msgpack.unpackb(payload, raw=False)

        # Handle response type
        if msg_type == MSG_SUCCESS or msg_type == MSG_PONG or msg_type == MSG_CHANGE_EVENT:
            return data
        elif msg_type == MSG_ERROR:
            raise OperationError(data.get('error', 'Unknown error'))
        elif msg_type == MSG_NOT_FOUND:
            raise OperationError('Not found')
        else:
            raise ValueError(f"Unknown response type: {msg_type}")

    def _recv_exact(self, n: int) -> bytes:
        """
        Receive exactly n bytes from socket.

        Args:
            n: Number of bytes to read

        Returns:
            Bytes read

        Raises:
            ConnectionError: If connection closed
        """
        data = b''
        while len(data) < n:
            chunk = self.socket.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Connection closed by server")
            data += chunk
        return data

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class NexaClient:
    """
    Production-grade NexaDB client.

    Features:
    - MySQL-style connection management
    - Automatic reconnection
    - Thread-safe operations
    - Connection pooling ready
    - Comprehensive API coverage

    Usage:
        # Simple usage
        with NexaClient() as db:
            result = db.create('users', {'name': 'Alice'})
            users = db.query('users', {'age': {'$gt': 25}})

        # Advanced usage with connection pooling
        client = NexaClient(host='localhost', port=6970)
        client.connect()
        # ... use client ...
        client.disconnect()
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6970,
        username: str = 'root',
        password: str = 'nexadb123',
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize NexaDB client.

        Args:
            host: Server host (default: 'localhost')
            port: Server port (default: 6970)
            username: Username (default: 'root')
            password: Password (default: 'nexadb123')
            timeout: Connection timeout (default: 30s)
            max_retries: Max reconnection attempts (default: 3)
        """
        self.conn = NexaDBConnection(host, port, username, password, timeout, max_retries)

    def connect(self) -> None:
        """Connect to server."""
        self.conn.connect()

    def disconnect(self) -> None:
        """Disconnect from server."""
        self.conn.disconnect()

    def __enter__(self):
        """Context manager entry."""
        self.conn.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.conn.disconnect()

    # ============================================================================
    # CORE CRUD OPERATIONS
    # ============================================================================

    def create(self, collection: str, data: Dict[str, Any], database: Optional[str] = None) -> Dict[str, Any]:
        """
        Insert document into collection.

        Args:
            collection: Collection name
            data: Document data
            database: Optional database name (v3.0.0). If not specified, uses 'default'.

        Returns:
            {'collection': str, 'document_id': str, 'message': str}

        Example:
            >>> db.create('users', {'name': 'Alice', 'email': 'alice@example.com'})
            {'collection': 'users', 'document_id': 'abc123', 'message': 'Document inserted'}

            >>> # Create in specific database (v3.0.0)
            >>> db.create('orders', {'product': 'Widget'}, database='production')
            {'collection': 'orders', 'document_id': 'xyz789', 'message': 'Document inserted'}
        """
        message_data = {
            'collection': collection,
            'data': data
        }
        if database:
            message_data['database'] = database

        return self.conn.send_message(MSG_CREATE, message_data)

    def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.

        Args:
            collection: Collection name
            key: Document ID

        Returns:
            Document data or None if not found

        Example:
            >>> user = db.get('users', 'abc123')
            >>> print(user['name'])
            'Alice'
        """
        try:
            response = self.conn.send_message(MSG_READ, {
                'collection': collection,
                'key': key
            })
            return response.get('document')
        except OperationError as e:
            if 'Not found' in str(e):
                return None
            raise

    def update(self, collection: str, key: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update document.

        Args:
            collection: Collection name
            key: Document ID
            updates: Updates to apply

        Returns:
            Update result

        Example:
            >>> db.update('users', 'abc123', {'age': 30})
            {'collection': 'users', 'document_id': 'abc123', 'message': 'Document updated'}
        """
        return self.conn.send_message(MSG_UPDATE, {
            'collection': collection,
            'key': key,
            'updates': updates
        })

    def delete(self, collection: str, key: str) -> Dict[str, Any]:
        """
        Delete document.

        Args:
            collection: Collection name
            key: Document ID

        Returns:
            Delete result

        Example:
            >>> db.delete('users', 'abc123')
            {'collection': 'users', 'document_id': 'abc123', 'message': 'Document deleted'}
        """
        return self.conn.send_message(MSG_DELETE, {
            'collection': collection,
            'key': key
        })

    def query(
        self,
        collection: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents with filters.

        Args:
            collection: Collection name
            filters: Query filters (default: {})
            limit: Max results (default: 100)
            database: Optional database name (v3.0.0). If not specified, uses 'default'.

        Returns:
            List of matching documents

        Example:
            >>> users = db.query('users', {'age': {'$gte': 25}}, 10)
            >>> print(len(users))
            5

            >>> # Query from specific database (v3.0.0)
            >>> orders = db.query('orders', {}, database='production')
            >>> print(len(orders))
            42
        """
        message_data = {
            'collection': collection,
            'filters': filters or {},
            'limit': limit
        }
        if database:
            message_data['database'] = database

        response = self.conn.send_message(MSG_QUERY, message_data)
        return response.get('documents', [])

    def batch_write(self, collection: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk insert documents.

        Args:
            collection: Collection name
            documents: List of documents

        Returns:
            Insert result with document IDs

        Example:
            >>> docs = [{'name': 'Alice'}, {'name': 'Bob'}]
            >>> result = db.batch_write('users', docs)
            >>> print(f"Inserted {result['count']} documents")
        """
        return self.conn.send_message(MSG_BATCH_WRITE, {
            'collection': collection,
            'documents': documents
        })

    # ============================================================================
    # VECTOR OPERATIONS (AI/ML)
    # ============================================================================

    def vector_search(
        self,
        collection: str,
        vector: List[float],
        limit: int = 10,
        dimensions: int = 768,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Vector similarity search.

        Args:
            collection: Collection name
            vector: Query vector
            limit: Max results (default: 10)
            dimensions: Vector dimensions (default: 768)
            database: Optional database name (v3.0.0). If not specified, uses 'default'.

        Returns:
            List of similar documents with scores

        Example:
            >>> results = db.vector_search('embeddings', [0.1, 0.2, ...], limit=5)
            >>> for r in results:
            ...     print(f"Similarity: {r['similarity']}, Doc: {r['document']}")

            >>> # Search in specific database (v3.0.0)
            >>> results = db.vector_search('movies', [0.8, 0.2, 0.9, 0.1], limit=5, dimensions=4, database='vector_test')
            >>> print(f"Found {len(results)} similar movies")
        """
        message_data = {
            'collection': collection,
            'vector': vector,
            'limit': limit,
            'dimensions': dimensions
        }
        if database:
            message_data['database'] = database

        response = self.conn.send_message(MSG_VECTOR_SEARCH, message_data)
        return response.get('results', [])

    # ============================================================================
    # COLLECTION MANAGEMENT (like MySQL's SHOW TABLES, DROP TABLE)
    # ============================================================================

    def list_collections(self, database: Optional[str] = None) -> List[str]:
        """
        List all collections (like MySQL's SHOW TABLES).

        Args:
            database: Optional database name (v3.0.0). If not specified, uses 'default'.

        Returns:
            List of collection names

        Example:
            >>> collections = db.list_collections()
            >>> print(collections)
            ['users', 'products', 'orders']

            >>> # List collections in a specific database (v3.0.0)
            >>> collections = db.list_collections(database='production')
            >>> print(collections)
            ['orders', 'customers']
        """
        message_data = {}
        if database:
            message_data['database'] = database

        response = self.conn.send_message(MSG_LIST_COLLECTIONS, message_data)
        return response.get('collections', [])

    def drop_collection(self, name: str, database: Optional[str] = None) -> bool:
        """
        Drop entire collection (like MySQL's DROP TABLE).

        Args:
            name: Collection name
            database: Optional database name (v3.0.0). If not specified, uses 'default'.

        Returns:
            True if dropped successfully

        Example:
            >>> db.drop_collection('old_data')
            True

            >>> # Drop collection from specific database (v3.0.0)
            >>> db.drop_collection('temp_data', database='production')
            True
        """
        try:
            message_data = {
                'collection': name
            }
            if database:
                message_data['database'] = database

            response = self.conn.send_message(MSG_DROP_COLLECTION, message_data)
            return response.get('message') == 'Collection dropped'
        except OperationError:
            return False

    def get_vectors(self) -> Dict[str, Any]:
        """
        Get vector index statistics.

        Returns:
            {'total_vectors': int, 'collections': dict}

        Example:
            >>> vectors = db.get_vectors()
            >>> print(f"Total vectors: {vectors['total_vectors']}")
        """
        return self.conn.send_message(MSG_GET_VECTORS, {})

    # ============================================================================
    # DATABASE MANAGEMENT (v3.0.0 - Multi-Database Support)
    # ============================================================================

    def list_databases(self) -> List[str]:
        """
        List all databases (v3.0.0).

        Returns:
            List of database names

        Example:
            >>> databases = db.list_databases()
            >>> print(databases)
            ['default', 'production', 'staging']
        """
        response = self.conn.send_message(MSG_LIST_COLLECTIONS, {'database': True})
        return response.get('databases', [])

    def create_database(self, name: str) -> Dict[str, Any]:
        """
        Create new database (v3.0.0).

        Args:
            name: Database name

        Returns:
            Creation result

        Example:
            >>> db.create_database('production')
            {'database': 'production', 'message': 'Database created'}
        """
        return self.conn.send_message(MSG_CREATE, {
            'database': name,
            'create_database': True
        })

    def drop_database(self, name: str) -> bool:
        """
        Drop entire database (v3.0.0).

        Args:
            name: Database name

        Returns:
            True if dropped successfully

        Example:
            >>> db.drop_database('old_db')
            True
        """
        try:
            response = self.conn.send_message(MSG_DROP_COLLECTION, {
                'database': name,
                'drop_database': True
            })
            return response.get('success', False)
        except OperationError:
            return False

    def get_database_stats(self, name: str) -> Dict[str, Any]:
        """
        Get database statistics (v3.0.0).

        Args:
            name: Database name

        Returns:
            {'collections_count': int, 'documents_count': int, 'storage_bytes': int}

        Example:
            >>> stats = db.get_database_stats('production')
            >>> print(f"Collections: {stats['collections_count']}")
        """
        return self.conn.send_message(MSG_COLLECTION_STATS, {
            'database': name,
            'get_database_stats': True
        })

    # ============================================================================
    # TOON FORMAT (Token-Optimized Object Notation - 40-50% size reduction)
    # ============================================================================

    def query_toon(
        self,
        collection: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Query with TOON format response (40-50% token reduction for LLMs).

        Args:
            collection: Collection name
            filters: Query filters
            limit: Max results

        Returns:
            {'data': str, 'count': int, 'token_stats': dict}

        Example:
            >>> result = db.query_toon('users', {'age': {'$gt': 25}})
            >>> print(result['token_stats']['reduction_percent'])
            42.3%
        """
        return self.conn.send_message(MSG_QUERY_TOON, {
            'collection': collection,
            'filters': filters or {},
            'limit': limit
        })

    def export_toon(self, collection: str) -> Dict[str, Any]:
        """
        Export entire collection to TOON format.

        Args:
            collection: Collection name

        Returns:
            {'data': str, 'count': int, 'token_stats': dict}

        Example:
            >>> result = db.export_toon('users')
            >>> with open('users.toon', 'w') as f:
            ...     f.write(result['data'])
        """
        return self.conn.send_message(MSG_EXPORT_TOON, {
            'collection': collection
        })

    # ============================================================================
    # USER MANAGEMENT (like MySQL's CREATE USER, DROP USER)
    # ============================================================================

    def create_user(self, username: str, password: str, role: str = 'read') -> Dict[str, Any]:
        """
        Create new user (admin only).

        Args:
            username: Username
            password: Password
            role: Role (admin/write/read/guest)

        Returns:
            User creation result
        """
        return self.conn.send_message(MSG_CREATE_USER, {
            'username': username,
            'password': password,
            'role': role
        })

    def delete_user(self, username: str) -> Dict[str, Any]:
        """
        Delete user (admin only).

        Args:
            username: Username to delete

        Returns:
            Deletion result
        """
        return self.conn.send_message(MSG_DELETE_USER, {
            'username': username
        })

    def list_users(self) -> List[Dict[str, Any]]:
        """
        List all users (admin only).

        Returns:
            List of users
        """
        response = self.conn.send_message(MSG_LIST_USERS, {})
        return response.get('users', [])

    def change_password(self, username: str, new_password: str) -> Dict[str, Any]:
        """
        Change user password.

        Args:
            username: Username
            new_password: New password

        Returns:
            Change result
        """
        return self.conn.send_message(MSG_CHANGE_PASSWORD, {
            'username': username,
            'new_password': new_password
        })

    # ============================================================================
    # UTILITY OPERATIONS
    # ============================================================================

    def ping(self) -> Dict[str, Any]:
        """
        Ping server (health check / keep-alive).

        Returns:
            Pong response

        Example:
            >>> pong = db.ping()
            >>> print(pong['status'])
            'ok'
        """
        return self.conn.send_message(MSG_PING, {})

    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics (like MySQL's SHOW STATUS).

        Returns:
            Statistics dictionary
        """
        return self.conn.stats.copy()

    # ============================================================================
    # CHANGE STREAMS (MongoDB-style)
    # ============================================================================

    def watch(
        self,
        collection: Optional[str] = None,
        operations: Optional[List[str]] = None
    ):
        """
        Watch for database changes (MongoDB-style change streams).

        Args:
            collection: Optional collection name to watch (None = watch all collections)
            operations: Optional list of operations to watch (default: ['insert', 'update', 'delete'])

        Yields:
            Change events as they occur

        Example:
            >>> # Watch all changes on 'orders' collection
            >>> for change in client.watch('orders'):
            ...     print(f"Change: {change['operationType']}")

            >>> # Watch only inserts and updates
            >>> for change in client.watch('orders', operations=['insert', 'update']):
            ...     print(f"New/Updated order: {change}")
        """
        # Queue for receiving change events
        event_queue = queue.Queue()
        stop_watching = threading.Event()

        # Subscribe to changes
        subscribe_response = self.conn.send_message(MSG_SUBSCRIBE_CHANGES, {
            'collection': collection,
            'operations': operations or ['insert', 'update', 'delete']
        })

        if not subscribe_response.get('subscribed'):
            raise OperationError("Failed to subscribe to change stream")

        # Background thread to receive change events
        def receive_events():
            try:
                while not stop_watching.is_set():
                    # Read change event from server
                    try:
                        self.conn.socket.settimeout(1.0)  # 1 second timeout
                        event_data = self.conn._read_response()
                        event_queue.put(event_data)
                    except socket.timeout:
                        continue  # Check if we should stop
                    except Exception as e:
                        if not stop_watching.is_set():
                            event_queue.put(e)
                        break
            except Exception as e:
                event_queue.put(e)

        receiver_thread = threading.Thread(target=receive_events, daemon=True)
        receiver_thread.start()

        try:
            # Yield events as they arrive
            while True:
                try:
                    event = event_queue.get(timeout=1.0)
                    if isinstance(event, Exception):
                        raise event
                    yield event
                except queue.Empty:
                    continue

        finally:
            # Cleanup: Unsubscribe from changes
            stop_watching.set()
            receiver_thread.join(timeout=2.0)

            try:
                self.conn.send_message(MSG_UNSUBSCRIBE_CHANGES, {
                    'collection': collection
                })
            except:
                pass  # Ignore errors during cleanup

    def __repr__(self) -> str:
        """String representation."""
        status = "connected" if self.conn.connected else "disconnected"
        return f"NexaClient(host='{self.conn.host}', port={self.conn.port}, status='{status}')"


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def connect(
    host: str = 'localhost',
    port: int = 6970,
    username: str = 'root',
    password: str = 'nexadb123'
) -> NexaClient:
    """
    Quick connect helper (like MySQL's mysql.connector.connect()).

    Args:
        host: Server host
        port: Server port
        username: Username
        password: Password

    Returns:
        Connected client

    Example:
        >>> db = nexadb_client.connect()
        >>> db.create('users', {'name': 'Alice'})
    """
    client = NexaClient(host, port, username, password)
    client.connect()
    return client


if __name__ == '__main__':
    # Example usage
    print("="*70)
    print("NexaDB Production Client - Example Usage")
    print("="*70)

    try:
        # Connect
        with NexaClient() as db:
            # Ping server
            pong = db.ping()
            print(f"\n✅ Connected! Server responded: {pong}")

            # Create document
            user = db.create('test_users', {
                'name': 'Alice',
                'email': 'alice@example.com',
                'age': 28
            })
            print(f"\n✅ Created document: {user['document_id']}")

            # Query
            users = db.query('test_users', {}, limit=10)
            print(f"\n✅ Found {len(users)} users")

            # Clean up
            db.delete('test_users', user['document_id'])
            print(f"\n✅ Deleted document")

            # Show stats
            stats = db.get_stats()
            print(f"\n📊 Client Stats:")
            for key, value in stats.items():
                print(f"   {key}: {value}")

    except Exception as e:
        print(f"\n❌ Error: {e}")

    print("\n" + "="*70)
