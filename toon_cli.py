#!/usr/bin/env python3
"""
NexaDB TOON CLI - Import/Export Tool
=====================================

Simple command-line tool for importing and exporting TOON format data.

Usage:
    # Export collection to TOON file
    python3 toon_cli.py export users users.toon

    # Import TOON file to collection
    python3 toon_cli.py import users.toon users

    # Import and replace existing data
    python3 toon_cli.py import users.toon users --replace
"""

import sys
import socket
import struct
import msgpack
import os

# Protocol constants
MAGIC = 0x4E455841
VERSION = 0x01
MSG_CONNECT = 0x01
MSG_EXPORT_TOON = 0x0C
MSG_IMPORT_TOON = 0x0D
MSG_SUCCESS = 0x81
MSG_ERROR = 0x82


def pack_message(msg_type, data):
    """Pack message into binary protocol format."""
    payload = msgpack.packb(data, use_bin_type=True)
    header = struct.pack('>IBBHI', MAGIC, VERSION, msg_type, 0, len(payload))
    return header + payload


def unpack_message(sock):
    """Receive and unpack binary message."""
    header_bytes = sock.recv(12)
    if len(header_bytes) < 12:
        raise Exception("Failed to read header")

    magic, version, msg_type, flags, payload_len = struct.unpack('>IBBHI', header_bytes)

    payload_bytes = b''
    while len(payload_bytes) < payload_len:
        chunk = sock.recv(payload_len - len(payload_bytes))
        if not chunk:
            raise Exception("Connection closed")
        payload_bytes += chunk

    payload = msgpack.unpackb(payload_bytes, raw=False)
    return msg_type, payload


def export_toon(collection, output_file, host='localhost', port=6970):
    """Export collection to TOON file."""
    print(f"Exporting collection '{collection}' to '{output_file}'...")

    # Connect
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    # Handshake
    connect_msg = pack_message(MSG_CONNECT, {'client': 'toon_cli', 'version': '1.0.0'})
    sock.sendall(connect_msg)
    msg_type, response = unpack_message(sock)

    if msg_type != MSG_SUCCESS:
        print(f"❌ Connection failed: {response}")
        return False

    # Export
    export_msg = pack_message(MSG_EXPORT_TOON, {'collection': collection})
    sock.sendall(export_msg)
    msg_type, response = unpack_message(sock)

    if msg_type == MSG_SUCCESS:
        toon_data = response.get('data', '')
        count = response.get('count', 0)
        stats = response.get('token_stats', {})

        # Write to file
        with open(output_file, 'w') as f:
            f.write(toon_data)

        print(f"✅ Exported {count} documents")
        print(f"   File: {output_file}")
        print(f"   Size: {len(toon_data)} bytes")
        print(f"   Token reduction: {stats.get('reduction_percent', 0)}%")
        return True
    else:
        error = response.get('error', 'Unknown error')
        print(f"❌ Export failed: {error}")
        return False


def import_toon(input_file, collection, replace=False, host='localhost', port=6970):
    """Import TOON file to collection."""
    print(f"Importing '{input_file}' to collection '{collection}'...")

    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return False

    # Read TOON file
    with open(input_file, 'r') as f:
        toon_data = f.read()

    # Connect
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    # Handshake
    connect_msg = pack_message(MSG_CONNECT, {'client': 'toon_cli', 'version': '1.0.0'})
    sock.sendall(connect_msg)
    msg_type, response = unpack_message(sock)

    if msg_type != MSG_SUCCESS:
        print(f"❌ Connection failed: {response}")
        return False

    # Import
    import_msg = pack_message(MSG_IMPORT_TOON, {
        'collection': collection,
        'toon_data': toon_data,
        'replace': replace
    })
    sock.sendall(import_msg)
    msg_type, response = unpack_message(sock)

    if msg_type == MSG_SUCCESS:
        imported = response.get('imported', 0)
        message = response.get('message', '')

        print(f"✅ {message}")
        print(f"   Imported: {imported} documents")
        if replace:
            print(f"   Mode: Replace (existing data deleted)")
        else:
            print(f"   Mode: Append (added to existing data)")
        return True
    else:
        error = response.get('error', 'Unknown error')
        print(f"❌ Import failed: {error}")
        return False


def print_usage():
    """Print usage information."""
    print("""
NexaDB TOON CLI - Import/Export Tool
=====================================

Usage:
    Export:
        python3 toon_cli.py export <collection> <output.toon>

    Import:
        python3 toon_cli.py import <input.toon> <collection>
        python3 toon_cli.py import <input.toon> <collection> --replace

Examples:
    # Export users collection to file
    python3 toon_cli.py export users users.toon

    # Import TOON file (append to existing data)
    python3 toon_cli.py import users.toon users

    # Import TOON file (replace existing data)
    python3 toon_cli.py import users.toon users --replace

Options:
    --replace    Delete existing data before import
    --host HOST  Server host (default: localhost)
    --port PORT  Server port (default: 6970)
    """)


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    # Parse options
    host = 'localhost'
    port = 6970
    replace = False

    if '--host' in sys.argv:
        host_idx = sys.argv.index('--host')
        if host_idx + 1 < len(sys.argv):
            host = sys.argv[host_idx + 1]

    if '--port' in sys.argv:
        port_idx = sys.argv.index('--port')
        if port_idx + 1 < len(sys.argv):
            port = int(sys.argv[port_idx + 1])

    if '--replace' in sys.argv:
        replace = True

    try:
        if command == 'export':
            if len(sys.argv) < 4:
                print("❌ Missing arguments")
                print("Usage: python3 toon_cli.py export <collection> <output.toon>")
                sys.exit(1)

            collection = sys.argv[2]
            output_file = sys.argv[3]

            success = export_toon(collection, output_file, host, port)
            sys.exit(0 if success else 1)

        elif command == 'import':
            if len(sys.argv) < 4:
                print("❌ Missing arguments")
                print("Usage: python3 toon_cli.py import <input.toon> <collection>")
                sys.exit(1)

            input_file = sys.argv[2]
            collection = sys.argv[3]

            success = import_toon(input_file, collection, replace, host, port)
            sys.exit(0 if success else 1)

        else:
            print(f"❌ Unknown command: {command}")
            print_usage()
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
