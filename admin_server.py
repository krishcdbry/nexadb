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

# Binary protocol constants
MAGIC = 0x4E455841
VERSION = 0x01
MSG_CONNECT = 0x01
MSG_QUERY_TOON = 0x0B
MSG_EXPORT_TOON = 0x0C
MSG_SUCCESS = 0x81

# Import TOON module
sys.path.append(os.path.dirname(__file__))
from toon_format import json_to_toon


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


class AdminRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with TOON API endpoints."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        # Serve admin panel at root
        if parsed_path.path == '/':
            self.path = '/nexadb_admin_modern.html'

        # API endpoint for TOON export
        if parsed_path.path == '/api/toon/export':
            self.handle_toon_export(parsed_path)
        else:
            # Serve static files
            super().do_GET()

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


def run_server(port=9999):
    """Run the admin HTTP server."""
    # Change to nexadb directory
    os.chdir(os.path.dirname(__file__))

    # Create server
    Handler = AdminRequestHandler

    with socketserver.TCPServer(("", port), Handler) as httpd:
        print("=" * 70)
        print("NexaDB Admin Server")
        print("=" * 70)
        print(f"Serving admin panel at: http://localhost:{port}")
        print(f"Admin panel: http://localhost:{port}/nexadb_admin_modern.html")
        print(f"TOON viewer: http://localhost:{port}/toon_viewer.html")
        print(f"\nBinary server: localhost:6970")
        print("=" * 70)
        print("\nPress Ctrl+C to stop")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            httpd.shutdown()


if __name__ == '__main__':
    port = 9999

    if '--port' in sys.argv:
        port_idx = sys.argv.index('--port')
        if port_idx + 1 < len(sys.argv):
            port = int(sys.argv[port_idx + 1])

    run_server(port)
