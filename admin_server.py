#!/usr/bin/env python3
"""
NexaDB Admin Server
===================

Serves the admin panel on HTTP with TOON export functionality.

Usage:
    python3 admin_server.py --port 9999
"""

import http.server
import socketserver
import json
import os
import sys
from urllib.parse import urlparse, parse_qs
import socket as sock
import struct
import msgpack
import uuid
import time
from http.cookies import SimpleCookie

# Binary protocol constants
MAGIC = 0x4E455841
VERSION = 0x01
MSG_CONNECT = 0x01
MSG_QUERY_TOON = 0x0B
MSG_EXPORT_TOON = 0x0C
MSG_SUCCESS = 0x81

# Import TOON module and auth
sys.path.append(os.path.dirname(__file__))
from toon_format import json_to_toon
from unified_auth import UnifiedAuthManager

# Session storage (in-memory for now)
SESSIONS = {}
SESSION_TIMEOUT = 24 * 60 * 60  # 24 hours


def pack_message(msg_type, data):
    """Pack message for binary protocol."""
    payload = msgpack.packb(data, use_bin_type=True)
    header = struct.pack('>IBBHI', MAGIC, VERSION, msg_type, 0, len(payload))
    return header + payload


def unpack_message(socket):
    """Unpack message from binary protocol."""
    header_bytes = socket.recv(12)
    magic, version, msg_type, flags, payload_len = struct.unpack('>IBBHI', header_bytes)

    payload_bytes = b''
    while len(payload_bytes) < payload_len:
        chunk = socket.recv(payload_len - len(payload_bytes))
        payload_bytes += chunk

    payload = msgpack.unpackb(payload_bytes, raw=False)
    return msg_type, payload


def create_session(username, role, api_key):
    """Create a new session."""
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        'username': username,
        'role': role,
        'api_key': api_key,
        'created_at': time.time(),
        'last_access': time.time()
    }
    return session_id


def get_session(session_id):
    """Get session data if valid."""
    if not session_id or session_id not in SESSIONS:
        return None

    session = SESSIONS[session_id]

    # Check if session expired
    if time.time() - session['last_access'] > SESSION_TIMEOUT:
        del SESSIONS[session_id]
        return None

    # Update last access time
    session['last_access'] = time.time()
    return session


def delete_session(session_id):
    """Delete a session."""
    if session_id in SESSIONS:
        del SESSIONS[session_id]


class AdminRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with TOON API endpoints and authentication."""

    auth = None  # Will be set in run_server

    def end_headers(self):
        # Add cache-control headers to prevent caching
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def get_session_from_cookie(self):
        """Extract session ID from cookie."""
        cookie_header = self.headers.get('Cookie')
        if not cookie_header:
            return None

        cookie = SimpleCookie()
        cookie.load(cookie_header)

        if 'nexadb_session' in cookie:
            return cookie['nexadb_session'].value

        return None

    def is_authenticated(self):
        """Check if request is authenticated."""
        session_id = self.get_session_from_cookie()
        session = get_session(session_id)
        return session is not None

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        # Serve admin panel - redirect root to login or dashboard
        if parsed_path.path == '/':
            if self.is_authenticated():
                self.send_response(302)
                self.send_header('Location', '/admin_panel/index.html')
                self.end_headers()
            else:
                self.send_response(302)
                self.send_header('Location', '/admin_panel/login.html')
                self.end_headers()
            return

        # Public paths that don't require authentication
        public_paths = [
            '/admin_panel/login.html',
            '/admin_panel/css/styles.css',
            '/admin_panel/js/auth.js',
            '/logo-light.svg',
            '/logo-dark.svg'
        ]

        # Check if this is a public path
        is_public = any(parsed_path.path == p for p in public_paths)

        # Protected paths (admin panel pages)
        protected_prefixes = [
            '/admin_panel/index.html',
            '/admin_panel/js/app.js'
        ]

        # Check if this is a protected path
        is_protected = any(parsed_path.path.startswith(prefix) or parsed_path.path == prefix.rstrip('/')
                          for prefix in protected_prefixes)

        # If /admin_panel/ without index.html, redirect to index.html if authenticated, else login
        if parsed_path.path == '/admin_panel/' or parsed_path.path == '/admin_panel':
            if self.is_authenticated():
                self.send_response(302)
                self.send_header('Location', '/admin_panel/index.html')
                self.end_headers()
            else:
                self.send_response(302)
                self.send_header('Location', '/admin_panel/login.html')
                self.end_headers()
            return

        # If it's a protected path and not authenticated, redirect to login
        if is_protected and not is_public and not self.is_authenticated():
            self.send_response(302)
            self.send_header('Location', '/admin_panel/login.html')
            self.end_headers()
            return

        # Block access to old admin panel
        if 'admin_modern' in parsed_path.path:
            self.send_error(404, "File not found")
            return

        # API endpoint for TOON export
        if parsed_path.path == '/api/toon/export':
            self.handle_toon_export(parsed_path)
        # Collections endpoint
        elif parsed_path.path == '/api/collections':
            self.handle_get_collections()
        # Vectors endpoint
        elif parsed_path.path == '/api/vectors':
            self.handle_get_vectors()
        # Session management endpoints
        elif parsed_path.path == '/api/auth/logout':
            self.handle_logout()
        else:
            # Serve static files
            super().do_GET()

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)

        # Login endpoint
        if parsed_path.path == '/api/auth/login':
            self.handle_login()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_login(self):
        """Handle login request."""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)

            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'Missing username or password'
                }).encode())
                return

            # Authenticate with unified auth manager
            user_info = self.auth.authenticate_password(username, password)

            if not user_info:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'Invalid username or password'
                }).encode())
                return

            # Create session
            session_id = create_session(
                user_info['username'],
                user_info['role'],
                user_info['api_key']
            )

            # Set session cookie
            cookie = SimpleCookie()
            cookie['nexadb_session'] = session_id
            cookie['nexadb_session']['path'] = '/'
            cookie['nexadb_session']['max-age'] = SESSION_TIMEOUT
            cookie['nexadb_session']['httponly'] = True

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', cookie['nexadb_session'].OutputString())
            self.end_headers()

            self.wfile.write(json.dumps({
                'success': True,
                'username': user_info['username'],
                'role': user_info['role'],
                'api_key': user_info['api_key']
            }).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': f'Server error: {str(e)}'
            }).encode())

    def handle_logout(self):
        """Handle logout request."""
        try:
            session_id = self.get_session_from_cookie()
            if session_id:
                delete_session(session_id)

            # Clear cookie
            cookie = SimpleCookie()
            cookie['nexadb_session'] = ''
            cookie['nexadb_session']['path'] = '/'
            cookie['nexadb_session']['max-age'] = 0

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', cookie['nexadb_session'].OutputString())
            self.end_headers()

            self.wfile.write(json.dumps({
                'success': True,
                'message': 'Logged out successfully'
            }).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': f'Server error: {str(e)}'
            }).encode())

    def handle_get_collections(self):
        """Handle GET /api/collections - fetch all collections from REST API."""
        try:
            import urllib.request
            import urllib.error

            # Fetch collections from REST API (port 6969)
            url = 'http://localhost:6969/collections'
            req = urllib.request.Request(url)

            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                self.wfile.write(json.dumps(data).encode())

        except urllib.error.URLError as e:
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'REST API not available',
                'details': str(e)
            }).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': f'Server error: {str(e)}'
            }).encode())

    def handle_get_vectors(self):
        """Handle GET /api/vectors - get vector index statistics."""
        try:
            from veloxdb_core import VeloxDB
            from collections import defaultdict

            # Initialize database to scan vectors
            data_dir = os.getenv('NEXADB_DATA_DIR', './nexadb_data')
            db = VeloxDB(data_dir)

            # Scan for all vectors
            vector_prefix = 'vector:'
            all_vectors = list(db.engine.range_scan(vector_prefix, vector_prefix + '\xff'))

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

            db.close()

            # Format response
            result = {
                'status': 'success',
                'total_vectors': len(all_vectors),
                'collections': dict(vector_data)
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': f'Server error: {str(e)}'
            }).encode())

    def handle_toon_export(self, parsed_path):
        """Handle TOON export API request."""
        try:
            # Parse query parameters
            params = parse_qs(parsed_path.query)
            collection = params.get('collection', [''])[0]

            if not collection:
                self.send_error(400, "Missing collection parameter")
                return

            # Connect to binary server
            client = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            client.connect(('localhost', 6970))

            # Handshake
            client.sendall(pack_message(MSG_CONNECT, {'client': 'admin_server'}))
            msg_type, response = unpack_message(client)

            # Export to TOON
            client.sendall(pack_message(MSG_EXPORT_TOON, {'collection': collection}))
            msg_type, response = unpack_message(client)

            client.close()

            if msg_type == MSG_SUCCESS:
                # Return TOON data as JSON response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                result = {
                    'success': True,
                    'toon_data': response.get('data', ''),
                    'token_stats': response.get('token_stats', {}),
                    'count': response.get('count', 0)
                }

                self.wfile.write(json.dumps(result).encode())
            else:
                self.send_error(500, f"Export failed: {response.get('error', 'Unknown error')}")

        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(port=9999, data_dir=None):
    """Run the admin HTTP server."""
    # Change to nexadb directory
    nexadb_dir = os.path.dirname(__file__) or '.'
    os.chdir(nexadb_dir)

    # Use same data directory as main server (./nexadb_data)
    # Check environment variable first for consistency with other servers
    if data_dir is None:
        data_dir = os.getenv('NEXADB_DATA_DIR')
        if data_dir is None:
            data_dir = os.path.join(nexadb_dir, 'nexadb_data')

    # Initialize unified auth manager
    auth = UnifiedAuthManager(data_dir=data_dir)
    AdminRequestHandler.auth = auth

    # Create server
    Handler = AdminRequestHandler

    with socketserver.TCPServer(("", port), Handler) as httpd:
        print("=" * 70)
        print("NexaDB Admin Server")
        print("=" * 70)
        print(f"Serving admin panel at: http://localhost:{port}")
        print(f"\n🎨 Admin Panel: http://localhost:{port}/admin_panel/")
        print(f"   Login: root / nexadb123")
        print(f"\n🔒 Server-side session authentication enabled")
        print(f"   Session timeout: {SESSION_TIMEOUT // 3600} hours")
        print(f"\nTOON viewer: http://localhost:{port}/toon_viewer.html")
        print(f"\nHTTP REST API: localhost:6969")
        print(f"Binary Protocol: localhost:6970")
        print("=" * 70)
        print("\nPress Ctrl+C to stop")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            httpd.shutdown()


if __name__ == '__main__':
    port = 9999
    data_dir = None

    if '--port' in sys.argv:
        port_idx = sys.argv.index('--port')
        if port_idx + 1 < len(sys.argv):
            port = int(sys.argv[port_idx + 1])

    if '--data-dir' in sys.argv:
        data_dir_idx = sys.argv.index('--data-dir')
        if data_dir_idx + 1 < len(sys.argv):
            data_dir = sys.argv[data_dir_idx + 1]

    run_server(port, data_dir)
