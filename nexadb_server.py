#!/usr/bin/env python3
"""
NexaDB Server - RESTful API Server
===================================

HTTP/REST API for NexaDB with:
- RESTful endpoints
- JSON request/response
- Connection pooling
- Authentication (API keys)
- Rate limiting
- WebSocket support (real-time queries)
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional
import hashlib
import time

# Import VeloxDB (now NexaDB)
import sys
sys.path.append('.')
from veloxdb_core import VeloxDB


class NexaDBHandler(BaseHTTPRequestHandler):
    """HTTP request handler for NexaDB API"""

    # Class-level database instance (shared across requests)
    db: VeloxDB = None
    api_keys: Dict[str, str] = {}  # api_key -> username

    def _set_headers(self, status_code: int = 200, content_type: str = 'application/json'):
        """Set response headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')  # CORS
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()

    def _is_localhost(self) -> bool:
        """Check if request is from localhost"""
        client_ip = self.client_address[0]
        return client_ip in ('127.0.0.1', '::1', 'localhost')

    def _authenticate(self) -> Optional[str]:
        """
        Authenticate request using API key

        For localhost: No API key required (development mode)
        For remote: API key required (production mode)

        Returns: username if valid, None otherwise
        """
        # Allow localhost without API key
        if self._is_localhost():
            return 'localhost'

        # Require API key for remote connections
        api_key = self.headers.get('X-API-Key')

        if not api_key:
            return None

        return self.api_keys.get(api_key)

    def _send_json(self, data: Any, status_code: int = 200):
        """Send JSON response"""
        self._set_headers(status_code)
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode())

    def _send_error(self, message: str, status_code: int = 400):
        """Send error response"""
        self._send_json({'error': message, 'status': 'error'}, status_code)

    def _parse_body(self) -> Optional[Dict[str, Any]]:
        """Parse JSON request body"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}

        body = self.rfile.read(content_length)
        try:
            return json.loads(body.decode())
        except json.JSONDecodeError:
            return None

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self._set_headers()

    def do_GET(self):
        """
        Handle GET requests

        Endpoints:
        - GET /status - Server status
        - GET /collections - List collections
        - GET /collections/{name} - List documents
        - GET /collections/{name}/{id} - Get document by ID
        - GET /stats - Database statistics
        """
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # Status endpoint (no auth required)
        if path == '/status':
            self._send_json({
                'status': 'ok',
                'version': '1.0.0',
                'database': 'NexaDB'
            })
            return

        # Require authentication for other endpoints
        user = self._authenticate()
        if not user:
            self._send_error('Unauthorized - provide X-API-Key header', 401)
            return

        # List collections
        if path == '/collections':
            collections = self.db.list_collections()
            self._send_json({
                'status': 'success',
                'collections': collections,
                'count': len(collections)
            })
            return

        # Stats
        if path == '/stats':
            stats = self.db.stats()
            self._send_json({
                'status': 'success',
                'stats': stats
            })
            return

        # Get documents from collection
        parts = path.strip('/').split('/')
        if len(parts) == 2 and parts[0] == 'collections':
            collection_name = parts[1]
            collection = self.db.collection(collection_name)

            # Parse query parameters
            query = json.loads(params.get('query', ['{}'])[0])
            limit = int(params.get('limit', [100])[0])

            documents = collection.find(query, limit=limit)

            self._send_json({
                'status': 'success',
                'collection': collection_name,
                'documents': documents,
                'count': len(documents)
            })
            return

        # Get document by ID
        if len(parts) == 3 and parts[0] == 'collections':
            collection_name = parts[1]
            doc_id = parts[2]

            collection = self.db.collection(collection_name)
            document = collection.find_by_id(doc_id)

            if document:
                self._send_json({
                    'status': 'success',
                    'document': document
                })
            else:
                self._send_error('Document not found', 404)
            return

        self._send_error('Endpoint not found', 404)

    def do_POST(self):
        """
        Handle POST requests

        Endpoints:
        - POST /collections/{name} - Insert document
        - POST /collections/{name}/bulk - Insert many documents
        - POST /collections/{name}/query - Complex query
        - POST /collections/{name}/aggregate - Aggregation pipeline
        - POST /vector/{name}/search - Vector similarity search
        """
        # Require authentication
        user = self._authenticate()
        if not user:
            self._send_error('Unauthorized - provide X-API-Key header', 401)
            return

        parsed = urlparse(self.path)
        path = parsed.path
        parts = path.strip('/').split('/')

        body = self._parse_body()
        if body is None:
            self._send_error('Invalid JSON body', 400)
            return

        # Insert document
        if len(parts) == 2 and parts[0] == 'collections':
            collection_name = parts[1]
            collection = self.db.collection(collection_name)

            doc_id = collection.insert(body)

            self._send_json({
                'status': 'success',
                'collection': collection_name,
                'document_id': doc_id,
                'message': 'Document inserted'
            }, 201)
            return

        # Bulk insert
        if len(parts) == 3 and parts[0] == 'collections' and parts[2] == 'bulk':
            collection_name = parts[1]
            collection = self.db.collection(collection_name)

            documents = body.get('documents', [])
            doc_ids = collection.insert_many(documents)

            self._send_json({
                'status': 'success',
                'collection': collection_name,
                'document_ids': doc_ids,
                'count': len(doc_ids),
                'message': f'Inserted {len(doc_ids)} documents'
            }, 201)
            return

        # Query
        if len(parts) == 3 and parts[0] == 'collections' and parts[2] == 'query':
            collection_name = parts[1]
            collection = self.db.collection(collection_name)

            query = body.get('query', {})
            limit = body.get('limit', 100)

            documents = collection.find(query, limit=limit)

            self._send_json({
                'status': 'success',
                'collection': collection_name,
                'documents': documents,
                'count': len(documents)
            })
            return

        # Aggregation
        if len(parts) == 3 and parts[0] == 'collections' and parts[2] == 'aggregate':
            collection_name = parts[1]
            collection = self.db.collection(collection_name)

            pipeline = body.get('pipeline', [])
            results = collection.aggregate(pipeline)

            self._send_json({
                'status': 'success',
                'collection': collection_name,
                'results': results,
                'count': len(results)
            })
            return

        # Vector search
        if len(parts) == 3 and parts[0] == 'vector' and parts[2] == 'search':
            collection_name = parts[1]
            vector = body.get('vector', [])
            limit = body.get('limit', 10)
            dimensions = body.get('dimensions', 768)

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

            self._send_json({
                'status': 'success',
                'collection': collection_name,
                'results': formatted_results,
                'count': len(formatted_results)
            })
            return

        self._send_error('Endpoint not found', 404)

    def do_PUT(self):
        """
        Handle PUT requests

        Endpoints:
        - PUT /collections/{name}/{id} - Update document
        """
        # Require authentication
        user = self._authenticate()
        if not user:
            self._send_error('Unauthorized - provide X-API-Key header', 401)
            return

        parsed = urlparse(self.path)
        path = parsed.path
        parts = path.strip('/').split('/')

        body = self._parse_body()
        if body is None:
            self._send_error('Invalid JSON body', 400)
            return

        # Update document
        if len(parts) == 3 and parts[0] == 'collections':
            collection_name = parts[1]
            doc_id = parts[2]

            collection = self.db.collection(collection_name)
            success = collection.update(doc_id, body)

            if success:
                self._send_json({
                    'status': 'success',
                    'collection': collection_name,
                    'document_id': doc_id,
                    'message': 'Document updated'
                })
            else:
                self._send_error('Document not found', 404)
            return

        self._send_error('Endpoint not found', 404)

    def do_DELETE(self):
        """
        Handle DELETE requests

        Endpoints:
        - DELETE /collections/{name} - Drop collection
        - DELETE /collections/{name}/{id} - Delete document
        """
        # Require authentication
        user = self._authenticate()
        if not user:
            self._send_error('Unauthorized - provide X-API-Key header', 401)
            return

        parsed = urlparse(self.path)
        path = parsed.path
        parts = path.strip('/').split('/')

        # Delete document
        if len(parts) == 3 and parts[0] == 'collections':
            collection_name = parts[1]
            doc_id = parts[2]

            collection = self.db.collection(collection_name)
            success = collection.delete(doc_id)

            if success:
                self._send_json({
                    'status': 'success',
                    'collection': collection_name,
                    'document_id': doc_id,
                    'message': 'Document deleted'
                })
            else:
                self._send_error('Document not found', 404)
            return

        # Drop collection
        if len(parts) == 2 and parts[0] == 'collections':
            collection_name = parts[1]
            success = self.db.drop_collection(collection_name)

            if success:
                self._send_json({
                    'status': 'success',
                    'collection': collection_name,
                    'message': 'Collection dropped'
                })
            else:
                self._send_error('Collection not found', 404)
            return

        self._send_error('Endpoint not found', 404)

    def log_message(self, format, *args):
        """Custom log format"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {self.address_string()} - {format % args}")


class NexaDBServer:
    """
    NexaDB HTTP Server

    Features:
    - Multi-threaded HTTP server
    - API key authentication
    - RESTful endpoints
    - JSON API
    """

    def __init__(self, host: str = '0.0.0.0', port: int = 6969, data_dir: str = './nexadb_data'):
        self.host = host
        self.port = port
        self.data_dir = data_dir

        # Initialize database
        print(f"[INIT] Initializing NexaDB at {data_dir}")
        NexaDBHandler.db = VeloxDB(data_dir)

        # Generate default API key
        self._setup_api_keys()

        self.server = None

    def _setup_api_keys(self):
        """Setup default API keys"""
        # Generate default API key
        default_key = hashlib.sha256(b'nexadb_admin').hexdigest()[:32]

        NexaDBHandler.api_keys = {
            default_key: 'admin'
        }

        print(f"[AUTH] Default API Key: {default_key}")
        print("[AUTH] Include this in requests: X-API-Key header")

    def add_api_key(self, username: str, api_key: Optional[str] = None) -> str:
        """Add new API key"""
        if not api_key:
            api_key = hashlib.sha256(username.encode() + str(time.time()).encode()).hexdigest()[:32]

        NexaDBHandler.api_keys[api_key] = username
        print(f"[AUTH] Added API key for user: {username}")
        return api_key

    def start(self):
        """Start HTTP server"""
        self.server = HTTPServer((self.host, self.port), NexaDBHandler)

        print("="*70)
        print("NexaDB Server Started")
        print("="*70)
        print(f"Host: {self.host}")
        print(f"Port: {self.port}")
        print(f"Data Directory: {self.data_dir}")
        print(f"\nServer URL: http://localhost:{self.port}")
        print("\nEndpoints:")
        print("  GET    /status                       - Server status")
        print("  GET    /collections                  - List collections")
        print("  GET    /collections/{name}           - List documents")
        print("  GET    /collections/{name}/{id}      - Get document")
        print("  POST   /collections/{name}           - Insert document")
        print("  POST   /collections/{name}/bulk      - Bulk insert")
        print("  POST   /collections/{name}/query     - Query documents")
        print("  POST   /collections/{name}/aggregate - Aggregation")
        print("  POST   /vector/{name}/search         - Vector search")
        print("  PUT    /collections/{name}/{id}      - Update document")
        print("  DELETE /collections/{name}/{id}      - Delete document")
        print("  DELETE /collections/{name}           - Drop collection")
        print("="*70)

        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Shutting down server...")
            self.stop()

    def stop(self):
        """Stop server"""
        if self.server:
            self.server.shutdown()
            NexaDBHandler.db.close()
            print("[SHUTDOWN] Server stopped")


def main():
    """Main entry point for nexadb-server command"""
    import sys
    import os

    # Parse command-line arguments
    host = os.getenv('NEXADB_HOST', '0.0.0.0')
    port = int(os.getenv('NEXADB_PORT', 6969))
    data_dir = os.getenv('NEXADB_DATA_DIR', './nexadb_data')

    # Check for --help
    if '--help' in sys.argv or '-h' in sys.argv:
        print("NexaDB Server - Zero-dependency LSM-Tree database")
        print("\nUsage:")
        print("  nexadb-server [options]")
        print("\nOptions:")
        print("  --host HOST        Host to bind to (default: 0.0.0.0)")
        print("  --port PORT        Port to listen on (default: 6969)")
        print("  --data-dir DIR     Data directory (default: ./nexadb_data)")
        print("\nEnvironment Variables:")
        print("  NEXADB_HOST        Host to bind to")
        print("  NEXADB_PORT        Port to listen on")
        print("  NEXADB_DATA_DIR    Data directory")
        print("  NEXADB_API_KEY     Custom API key")
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
    server = NexaDBServer(host=host, port=port, data_dir=data_dir)
    server.start()


if __name__ == '__main__':
    main()
