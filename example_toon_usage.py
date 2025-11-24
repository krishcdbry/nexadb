#!/usr/bin/env python3
"""
Example: How to Use TOON Format with NexaDB
============================================

TOON is a serialization format for data transfer, not storage.
This example shows the correct workflow.
"""

import socket
import struct
import msgpack
from toon_format import json_to_toon, toon_to_json

# Protocol constants
MAGIC = 0x4E455841
VERSION = 0x01
MSG_CONNECT = 0x01
MSG_BATCH_WRITE = 0x08
MSG_QUERY_TOON = 0x0B
MSG_SUCCESS = 0x81


def pack_message(msg_type, data):
    """Pack message into binary protocol format."""
    payload = msgpack.packb(data, use_bin_type=True)
    header = struct.pack('>IBBHI', MAGIC, VERSION, msg_type, 0, len(payload))
    return header + payload


def unpack_message(sock):
    """Receive and unpack binary message."""
    header_bytes = sock.recv(12)
    magic, version, msg_type, flags, payload_len = struct.unpack('>IBBHI', header_bytes)

    payload_bytes = b''
    while len(payload_bytes) < payload_len:
        chunk = sock.recv(payload_len - len(payload_bytes))
        payload_bytes += chunk

    payload = msgpack.unpackb(payload_bytes, raw=False)
    return msg_type, payload


def main():
    print("=" * 70)
    print("TOON Format Usage with NexaDB")
    print("=" * 70)

    # Connect to server
    print("\n[1] Connecting to NexaDB...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 6970))

    # Handshake
    connect_msg = pack_message(MSG_CONNECT, {'client': 'example', 'version': '1.0.0'})
    sock.sendall(connect_msg)
    msg_type, response = unpack_message(sock)
    print(f"✅ Connected: {response.get('status')}")

    # STEP 1: Store data in JSON format (standard way)
    print("\n[2] Inserting data (as JSON/Python dict)...")

    # Your data as a Python dictionary (this is what you store)
    user_data = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "isActive": True,
        "roles": ["admin", "user"],
        "metadata": {
            "lastLogin": "2024-01-15T10:30:00Z",
            "loginCount": 42
        },
        "posts": [
            {
                "id": 101,
                "title": "Getting Started with TOON",
                "content": "TOON is a compact data format...",
                "tags": ["tutorial", "beginner"],
                "published": True
            }
        ]
    }

    # Insert as normal JSON/dict
    batch_msg = pack_message(MSG_BATCH_WRITE, {
        'collection': 'users',
        'documents': [user_data]
    })
    sock.sendall(batch_msg)
    msg_type, response = unpack_message(sock)
    print(f"✅ Inserted: {response.get('count')} document(s)")

    # STEP 2: Query and get results in TOON format (for LLM usage)
    print("\n[3] Querying with TOON format response...")

    toon_query_msg = pack_message(MSG_QUERY_TOON, {
        'collection': 'users',
        'filters': {},
        'limit': 100
    })
    sock.sendall(toon_query_msg)
    msg_type, response = unpack_message(sock)

    if msg_type == MSG_SUCCESS:
        toon_data = response.get('data', '')
        token_stats = response.get('token_stats', {})

        print("\n[TOON Format Output] (for LLM context)")
        print("-" * 70)
        print(toon_data)
        print("-" * 70)

        print(f"\n[Token Statistics]")
        print(f"JSON size: {token_stats.get('json_size')} bytes")
        print(f"TOON size: {token_stats.get('toon_size')} bytes")
        print(f"Reduction: {token_stats.get('reduction_percent')}%")
        print(f"\n💰 This TOON format is perfect for:")
        print("   - Sending to LLM APIs (GPT-4, Claude, etc.)")
        print("   - RAG system context windows")
        print("   - Reducing token costs by 40-50%")

    # STEP 3: Convert data to TOON locally (alternative approach)
    print("\n[4] Alternative: Convert data to TOON locally...")

    # You can also convert your data to TOON format locally
    toon_local = json_to_toon(user_data)

    print("\n[Local TOON Conversion]")
    print("-" * 70)
    print(toon_local)
    print("-" * 70)

    print("\n[Usage Example]")
    print("Send this TOON data to your LLM:")
    print(f'''
import openai

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {{"role": "system", "content": "You are a helpful assistant."}},
        {{"role": "user", "content": f"Based on this user data:\\n{{toon_local}}\\n\\nWhat can you tell me about this user?"}}
    ]
)

# TOON format saves 40-50% tokens = significant cost reduction!
    ''')

    sock.close()

    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    print("1. Store data: Use regular JSON/dict format")
    print("2. Query data: Request TOON format for LLM usage")
    print("3. Convert locally: Use json_to_toon() for any data")
    print("\n✅ TOON is a serialization format, not a storage format!")


if __name__ == '__main__':
    main()
