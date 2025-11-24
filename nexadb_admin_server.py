#!/usr/bin/env python3
"""
NexaDB Admin UI Server
======================

Simple HTTP server to serve the NexaDB Admin web interface.

Usage:
    python3 nexadb_admin_server.py

Then open: http://localhost:9999
"""

import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

class AdminUIHandler(SimpleHTTPRequestHandler):
    """Custom handler to serve the admin UI"""

    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        super().end_headers()

    def do_GET(self):
        # Redirect root to professional admin UI
        if self.path == '/':
            self.path = '/nexadb_admin_professional.html'
        return super().do_GET()

    def log_message(self, format, *args):
        # Custom log format
        print(f"[ADMIN UI] {self.address_string()} - {format % args}")


def main():
    """Main entry point for nexadb-admin command"""
    import sys

    # Parse environment variables and command-line arguments
    host = os.getenv('ADMIN_HOST', '0.0.0.0')
    port = int(os.getenv('ADMIN_PORT', 9999))

    # Check for --help
    if '--help' in sys.argv or '-h' in sys.argv:
        print("NexaDB Admin UI - Professional web interface for NexaDB")
        print("\nUsage:")
        print("  nexadb-admin [options]")
        print("\nOptions:")
        print("  --host HOST        Host to bind to (default: 0.0.0.0)")
        print("  --port PORT        Port to listen on (default: 9999)")
        print("\nEnvironment Variables:")
        print("  ADMIN_HOST         Host to bind to")
        print("  ADMIN_PORT         Port to listen on")
        sys.exit(0)

    # Parse command-line arguments
    for i, arg in enumerate(sys.argv):
        if arg == '--host' and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == '--port' and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    server = HTTPServer((host, port), AdminUIHandler)

    print("="*70)
    print("NexaDB Admin UI Server Started")
    print("="*70)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print()
    print(f"Admin UI: http://localhost:{port}")
    print()
    print("Make sure NexaDB server is running:")
    print("  python3 nexadb_server.py")
    print()
    print("Press Ctrl+C to stop")
    print("="*70)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Admin UI server stopped")


if __name__ == '__main__':
    main()
