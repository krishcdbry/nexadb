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
from unified_auth import UnifiedAuthManager


class NexaDBHandler(BaseHTTPRequestHandler):
    """HTTP request handler for NexaDB API"""

    # Class-level database instance (shared across requests)
    db: VeloxDB = None
    auth: UnifiedAuthManager = None  # Unified authentication manager
    api_keys: Dict[str, str] = {}  # api_key -> username (for backward compatibility)

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

    def _authenticate(self) -> Optional[Dict[str, Any]]:
        """
        Authenticate request using API key

        For localhost: No API key required (development mode) - but if API key is provided, use it!
        For remote: API key required (production mode)

        Returns: user info if valid, None otherwise
        """
        # Check for API key first (even for localhost)
        api_key = self.headers.get('X-API-Key')

        if api_key:
            # Use UnifiedAuthManager to validate API key
            if self.auth:
                return self.auth.authenticate_api_key(api_key)

            # Fallback to legacy api_keys dict
            username = self.api_keys.get(api_key)
            if username:
                return {'username': username, 'role': 'admin'}

        # Allow localhost without API key (for development only)
        if self._is_localhost() and not api_key:
            return {'username': 'localhost', 'role': 'admin'}

        return None

    def _send_json(self, data: Any, status_code: int = 200):
        """Send JSON response"""
        self._set_headers(status_code)
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode())

    def _send_error(self, message: str, status_code: int = 400):
        """Send error response"""
        self._send_json({'error': message, 'status': 'error'}, status_code)

    def _check_permission(self, user: Dict[str, Any], required_role: str) -> bool:
        """
        Check if user has required permission level.

        Role hierarchy: guest < read < write < admin

        Args:
            user: User info dict with 'role' key
            required_role: Minimum required role ('read', 'write', 'admin')

        Returns:
            True if user has permission, False otherwise
        """
        role_hierarchy = {
            'guest': 0,
            'read': 1,
            'write': 2,
            'admin': 3
        }

        user_level = role_hierarchy.get(user.get('role', 'guest'), 0)
        required_level = role_hierarchy.get(required_role, 3)

        return user_level >= required_level

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

    def _serve_admin_panel(self, path: str):
        """Serve admin panel static files"""
        import os

        # Remove /admin_panel prefix
        file_path = path.replace('/admin_panel', '', 1)

        # Default to index.html
        if file_path == '' or file_path == '/':
            file_path = '/index.html'

        # Construct full path
        admin_dir = os.path.join(os.path.dirname(__file__), 'admin_panel')
        full_path = os.path.join(admin_dir, file_path.lstrip('/'))

        # Security: Prevent directory traversal
        if not os.path.abspath(full_path).startswith(os.path.abspath(admin_dir)):
            self._send_error('Forbidden', 403)
            return

        # Check if file exists
        if not os.path.isfile(full_path):
            self._send_error('File not found', 404)
            return

        # Determine content type
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon'
        }

        _, ext = os.path.splitext(full_path)
        content_type = content_types.get(ext.lower(), 'text/plain')

        # Read and serve file
        try:
            with open(full_path, 'rb') as f:
                content = f.read()

            self._set_headers(200, content_type)
            self.wfile.write(content)
        except Exception as e:
            self._send_error(f'Error reading file: {str(e)}', 500)

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
        - GET /admin_panel/* - Serve admin panel files
        """
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # Serve admin panel files
        if path.startswith('/admin_panel'):
            self._serve_admin_panel(path)
            return

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

        # List users (admin only)
        if path == '/users':
            # Check if user is admin
            if user['role'] != 'admin':
                self._send_error('Permission denied. Only admins can list users.', 403)
                return

            if not self.auth:
                self._send_error('Authentication system not initialized', 500)
                return

            users_dict = self.auth.list_users()

            # Convert dict to array format for frontend
            users_array = []
            for username, user_data in users_dict.items():
                users_array.append({
                    'username': username,
                    'role': user_data.get('role', 'guest'),
                    'api_key': user_data.get('api_key_prefix', 'N/A'),
                    'created_at': user_data.get('created_at', 0),
                    'last_login': user_data.get('last_login')
                })

            self._send_json({
                'status': 'success',
                'users': users_array,
                'count': len(users_array)
            })
            return

        self._send_error('Endpoint not found', 404)

    def do_POST(self):
        """
        Handle POST requests

        Endpoints:
        - POST /auth/login - Login with username/password
        - POST /collections/{name} - Insert document
        - POST /collections/{name}/bulk - Insert many documents
        - POST /collections/{name}/query - Complex query
        - POST /collections/{name}/aggregate - Aggregation pipeline
        - POST /vector/{name}/search - Vector similarity search
        """
        parsed = urlparse(self.path)
        path = parsed.path
        parts = path.strip('/').split('/')

        body = self._parse_body()
        if body is None:
            self._send_error('Invalid JSON body', 400)
            return

        # Login endpoint (no authentication required)
        if path == '/auth/login':
            username = body.get('username')
            password = body.get('password')

            if not username or not password:
                self._send_error('Missing username or password', 400)
                return

            if not self.auth:
                self._send_error('Authentication system not initialized', 500)
                return

            # Authenticate with username/password
            user_info = self.auth.authenticate_password(username, password)

            if not user_info:
                self._send_error('Invalid username or password', 401)
                return

            # Return user info with API key
            self._send_json({
                'status': 'success',
                'message': 'Login successful',
                'username': user_info['username'],
                'role': user_info['role'],
                'api_key': user_info['api_key']
            })
            return

        # Require authentication for other endpoints
        user = self._authenticate()
        if not user:
            self._send_error('Unauthorized - provide X-API-Key header', 401)
            return

        # Insert document (requires write permission)
        if len(parts) == 2 and parts[0] == 'collections':
            # Check write permission
            if not self._check_permission(user, 'write'):
                self._send_error('Permission denied. Write access required to insert documents.', 403)
                return

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

        # Bulk insert (requires write permission)
        if len(parts) == 3 and parts[0] == 'collections' and parts[2] == 'bulk':
            # Check write permission
            if not self._check_permission(user, 'write'):
                self._send_error('Permission denied. Write access required to insert documents.', 403)
                return

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

        # Create user (admin only)
        if path == '/users/create':
            # Check if user is admin
            if user['role'] != 'admin':
                self._send_error('Permission denied. Only admins can create users.', 403)
                return

            username = body.get('username')
            password = body.get('password')
            role = body.get('role', 'read')

            if not username or not password:
                self._send_error('Missing username or password', 400)
                return

            try:
                api_key = self.auth.create_user(username, password, role)

                self._send_json({
                    'status': 'success',
                    'message': f"User '{username}' created successfully",
                    'username': username,
                    'password': password,  # Return so admin can give it to the user
                    'api_key': api_key,    # Return so admin can give it to the user
                    'role': role,
                    'note': '⚠️ Save these credentials! Password and API key are only shown once.'
                }, 201)
            except ValueError as e:
                self._send_error(str(e), 400)
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

        # Update document (requires write permission)
        if len(parts) == 3 and parts[0] == 'collections':
            # Check write permission
            if not self._check_permission(user, 'write'):
                self._send_error('Permission denied. Write access required to update documents.', 403)
                return

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

        # Update user (admin only)
        if len(parts) == 2 and parts[0] == 'users':
            # Check if user is admin
            if user['role'] != 'admin':
                self._send_error('Permission denied. Only admins can update users.', 403)
                return

            username = parts[1]

            if not self.auth:
                self._send_error('Authentication system not initialized', 500)
                return

            # Get update fields
            new_password = body.get('password')
            new_role = body.get('role')

            if not new_password and not new_role:
                self._send_error('Must provide password or role to update', 400)
                return

            try:
                self.auth.update_user(username, password=new_password, role=new_role)
                self._send_json({
                    'status': 'success',
                    'message': f"User '{username}' updated successfully",
                    'username': username
                })
            except ValueError as e:
                self._send_error(str(e), 404)
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

        # Delete document (requires write permission)
        if len(parts) == 3 and parts[0] == 'collections':
            # Check write permission
            if not self._check_permission(user, 'write'):
                self._send_error('Permission denied. Write access required to delete documents.', 403)
                return

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

        # Drop collection (requires admin permission - more destructive!)
        if len(parts) == 2 and parts[0] == 'collections':
            # Check admin permission for dropping entire collections
            if not self._check_permission(user, 'admin'):
                self._send_error('Permission denied. Admin access required to drop collections.', 403)
                return

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

        # Delete user (admin only)
        if len(parts) == 2 and parts[0] == 'users':
            # Check if user is admin
            if user['role'] != 'admin':
                self._send_error('Permission denied. Only admins can delete users.', 403)
                return

            username = parts[1]

            if not self.auth:
                self._send_error('Authentication system not initialized', 500)
                return

            try:
                self.auth.delete_user(username)
                self._send_json({
                    'status': 'success',
                    'message': f"User '{username}' deleted successfully",
                    'username': username
                })
            except ValueError as e:
                self._send_error(str(e), 400)
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

        # Initialize unified authentication
        print(f"[SECURITY] Initializing unified authentication")
        NexaDBHandler.auth = UnifiedAuthManager(data_dir)

        # Generate default API key (for backward compatibility)
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

        # ANSI Color codes
        RESET = '\033[0m'
        BOLD = '\033[1m'
        CYAN = '\033[96m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        MAGENTA = '\033[95m'
        BLUE = '\033[94m'
        WHITE = '\033[97m'

        # Beautiful startup banner
        print(f"\n{CYAN}{BOLD}")
        print("╔═══════════════════════════════════════════════════════════════════════╗")
        print("║                                                                       ║")
        print("║     ███╗   ██╗███████╗██╗  ██╗ █████╗ ██████╗ ██████╗               ║")
        print("║     ████╗  ██║██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗██╔══██╗              ║")
        print("║     ██╔██╗ ██║█████╗   ╚███╔╝ ███████║██║  ██║██████╔╝              ║")
        print("║     ██║╚██╗██║██╔══╝   ██╔██╗ ██╔══██║██║  ██║██╔══██╗              ║")
        print("║     ██║ ╚████║███████╗██╔╝ ██╗██║  ██║██████╔╝██████╔╝              ║")
        print("║     ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝               ║")
        print("║                                                                       ║")
        print(f"║            {WHITE}Database for AI Developers{CYAN}                             ║")
        print("║                                                                       ║")
        print("╚═══════════════════════════════════════════════════════════════════════╝")
        print(f"{RESET}")

        print(f"\n{GREEN}{BOLD}🚀 SERVER STATUS{RESET}")
        print(f"   {WHITE}├─{RESET} Status:        {GREEN}●{RESET} {BOLD}Online{RESET}")
        print(f"   {WHITE}├─{RESET} Host:          {YELLOW}{self.host}{RESET}")
        print(f"   {WHITE}├─{RESET} Port:          {YELLOW}{self.port}{RESET}")
        print(f"   {WHITE}└─{RESET} Data Dir:      {BLUE}{self.data_dir}{RESET}")

        print(f"\n{MAGENTA}{BOLD}🌐 ACCESS POINTS{RESET}")
        print(f"   {WHITE}├─{RESET} {BOLD}Main API:{RESET}      {CYAN}http://localhost:{self.port}{RESET}")
        print(f"   {WHITE}└─{RESET} {BOLD}Admin Panel:{RESET}   {GREEN}http://localhost:{self.port}/admin_panel/{RESET}")

        print(f"\n{YELLOW}{BOLD}🔐 DEFAULT CREDENTIALS{RESET}")
        print(f"   {WHITE}├─{RESET} Username:      {GREEN}root{RESET}")
        print(f"   {WHITE}└─{RESET} Password:      {GREEN}nexadb123{RESET}")

        print(f"\n{BLUE}{BOLD}📦 CONNECT TO NEXADB{RESET}")
        print(f"   {WHITE}├─{RESET} {BOLD}Python:{RESET}        {CYAN}pip install nexadb-python{RESET}")
        print(f"   {WHITE}├─{RESET} {BOLD}Node.js:{RESET}       {CYAN}npm install nexaclient{RESET}")
        print(f"   {WHITE}└─{RESET} {BOLD}Docs:{RESET}          {GREEN}https://nexadb.io/docs{RESET}")

        print(f"\n{CYAN}{BOLD}✨ FEATURES{RESET}")
        print(f"   {WHITE}├─{RESET} {GREEN}✓{RESET} HNSW Vector Search (200x faster)")
        print(f"   {WHITE}├─{RESET} {GREEN}✓{RESET} Enterprise Security (AES-256-GCM)")
        print(f"   {WHITE}├─{RESET} {GREEN}✓{RESET} Advanced Indexing (B-Tree, Hash)")
        print(f"   {WHITE}├─{RESET} {GREEN}✓{RESET} RBAC Authentication")
        print(f"   {WHITE}└─{RESET} {GREEN}✓{RESET} 20K reads/sec, <1ms lookups")

        print(f"\n{WHITE}{'─' * 75}{RESET}")
        print(f"{GREEN}{BOLD}   🎯 Server ready! Visit the admin panel to get started   {RESET}")
        print(f"{WHITE}{'─' * 75}{RESET}\n")
        print(f"{YELLOW}💡 Tip:{RESET} Press {BOLD}Ctrl+C{RESET} to stop the server\n")

        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print(f"\n{YELLOW}⚡ Shutting down server...{RESET}")
            self.stop()
            print(f"{GREEN}✓ Server stopped successfully{RESET}\n")

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
