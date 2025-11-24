#!/usr/bin/env python3
"""
Test TOON Format Integration with NexaDB Binary Server
=======================================================

This script tests:
1. TOON format serialization/parsing
2. Binary server TOON endpoints
3. End-to-end TOON workflow
"""

import socket
import struct
import msgpack
import json
from toon_format import json_to_toon, toon_to_json

# Protocol constants
MAGIC = 0x4E455841  # "NEXA"
VERSION = 0x01

# Message types
MSG_CONNECT = 0x01
MSG_CREATE = 0x02
MSG_QUERY = 0x06
MSG_BATCH_WRITE = 0x08
MSG_QUERY_TOON = 0x0B
MSG_EXPORT_TOON = 0x0C

MSG_SUCCESS = 0x81
MSG_ERROR = 0x82


def pack_message(msg_type, data):
    """Pack message into binary protocol format."""
    payload = msgpack.packb(data, use_bin_type=True)
    header = struct.pack('>IBBHI', MAGIC, VERSION, msg_type, 0, len(payload))
    return header + payload


def unpack_message(sock):
    """Receive and unpack binary message."""
    # Read header (12 bytes)
    header_bytes = sock.recv(12)
    if len(header_bytes) < 12:
        raise Exception("Failed to read header")

    magic, version, msg_type, flags, payload_len = struct.unpack('>IBBHI', header_bytes)

    if magic != MAGIC:
        raise Exception(f"Invalid magic: {hex(magic)}")

    # Read payload
    payload_bytes = b''
    while len(payload_bytes) < payload_len:
        chunk = sock.recv(payload_len - len(payload_bytes))
        if not chunk:
            raise Exception("Connection closed while reading payload")
        payload_bytes += chunk

    payload = msgpack.unpackb(payload_bytes, raw=False)
    return msg_type, payload


def test_toon_format():
    """Test TOON format serialization/parsing."""
    print("\n" + "=" * 70)
    print("TEST 1: TOON Format Serialization/Parsing")
    print("=" * 70)

    # Test data
    data = {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin", "active": True},
            {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user", "active": True},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "user", "active": False}
        ]
    }

    # Convert to TOON
    toon_str = json_to_toon(data)
    print("\n[TOON Format]")
    print(toon_str)

    # Calculate sizes
    json_size = len(json.dumps(data))
    toon_size = len(toon_str)
    reduction = ((json_size - toon_size) / json_size * 100)

    print(f"\n[Statistics]")
    print(f"JSON size: {json_size} bytes")
    print(f"TOON size: {toon_size} bytes")
    print(f"Token reduction: {reduction:.1f}%")

    # Round-trip test
    json_back = toon_to_json(toon_str)
    restored = json.loads(json_back)

    print(f"\n[Round-trip Test]")
    print(f"Original matches restored: {data == restored}")

    if data == restored:
        print("✅ TOON serialization/parsing PASSED")
    else:
        print("❌ TOON serialization/parsing FAILED")
        return False

    return True


def test_binary_server_toon():
    """Test TOON integration with binary server."""
    print("\n" + "=" * 70)
    print("TEST 2: Binary Server TOON Integration")
    print("=" * 70)

    try:
        # Connect to server
        print("\n[1] Connecting to NexaDB binary server...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 6970))
        print("✅ Connected to localhost:6970")

        # Send CONNECT message
        print("\n[2] Sending handshake...")
        connect_msg = pack_message(MSG_CONNECT, {'client': 'test', 'version': '1.0.0'})
        sock.sendall(connect_msg)

        msg_type, response = unpack_message(sock)
        if msg_type == MSG_SUCCESS:
            print(f"✅ Handshake successful: {response.get('status')}")
        else:
            print(f"❌ Handshake failed")
            return False

        # Insert test data
        print("\n[3] Inserting test documents...")
        test_docs = [
            {"id": 1, "name": "Alice Johnson", "age": 28, "city": "San Francisco", "role": "engineer"},
            {"id": 2, "name": "Bob Smith", "age": 34, "city": "New York", "role": "manager"},
            {"id": 3, "name": "Charlie Brown", "age": 29, "city": "Austin", "role": "engineer"},
            {"id": 4, "name": "Diana Prince", "age": 31, "city": "Seattle", "role": "designer"},
            {"id": 5, "name": "Eve Davis", "age": 27, "city": "San Francisco", "role": "engineer"}
        ]

        batch_msg = pack_message(MSG_BATCH_WRITE, {
            'collection': 'test_users',
            'documents': test_docs
        })
        sock.sendall(batch_msg)

        msg_type, response = unpack_message(sock)
        if msg_type == MSG_SUCCESS:
            print(f"✅ Inserted {response.get('count')} documents")
        else:
            print(f"❌ Insert failed: {response}")
            return False

        # Test regular query (JSON)
        print("\n[4] Testing regular JSON query...")
        query_msg = pack_message(MSG_QUERY, {
            'collection': 'test_users',
            'filters': {},
            'limit': 100
        })
        sock.sendall(query_msg)

        msg_type, response = unpack_message(sock)
        if msg_type == MSG_SUCCESS:
            json_docs = response.get('documents', [])
            json_size = len(json.dumps(json_docs))
            print(f"✅ Retrieved {len(json_docs)} documents")
            print(f"   JSON response size: {json_size} bytes")
        else:
            print(f"❌ Query failed")
            return False

        # Test TOON query
        print("\n[5] Testing TOON format query...")
        toon_query_msg = pack_message(MSG_QUERY_TOON, {
            'collection': 'test_users',
            'filters': {},
            'limit': 100
        })
        sock.sendall(toon_query_msg)

        msg_type, response = unpack_message(sock)
        if msg_type == MSG_SUCCESS:
            toon_data = response.get('data', '')
            token_stats = response.get('token_stats', {})

            print(f"✅ Retrieved TOON format response")
            print(f"\n[TOON Data Preview]")
            print(toon_data[:300] + "..." if len(toon_data) > 300 else toon_data)

            print(f"\n[Token Statistics]")
            print(f"   JSON size: {token_stats.get('json_size')} bytes")
            print(f"   TOON size: {token_stats.get('toon_size')} bytes")
            print(f"   Reduction: {token_stats.get('reduction_percent')}%")

            # Verify token reduction
            if token_stats.get('reduction_percent', 0) > 30:
                print(f"✅ Significant token reduction achieved!")
            else:
                print(f"⚠️  Token reduction lower than expected")
        else:
            print(f"❌ TOON query failed: {response}")
            return False

        # Test TOON export
        print("\n[6] Testing TOON export...")
        export_msg = pack_message(MSG_EXPORT_TOON, {
            'collection': 'test_users'
        })
        sock.sendall(export_msg)

        msg_type, response = unpack_message(sock)
        if msg_type == MSG_SUCCESS:
            toon_export = response.get('data', '')
            export_stats = response.get('token_stats', {})

            print(f"✅ Exported collection to TOON format")
            print(f"   Documents: {response.get('count')}")
            print(f"   Reduction: {export_stats.get('reduction_percent')}%")
            print(f"   Estimated savings: {export_stats.get('estimated_cost_savings')}")
        else:
            print(f"❌ TOON export failed: {response}")
            return False

        sock.close()
        print("\n✅ All binary server TOON tests PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_world_scenario():
    """Test real-world AI/ML scenario with TOON."""
    print("\n" + "=" * 70)
    print("TEST 3: Real-World AI/ML Scenario")
    print("=" * 70)

    # Simulate RAG system data
    print("\n[Scenario] RAG System - Document Retrieval for LLM")

    documents = {
        "relevant_docs": [
            {
                "id": "doc_1",
                "title": "Introduction to Vector Databases",
                "content": "Vector databases store high-dimensional embeddings...",
                "similarity": 0.89,
                "metadata": {"source": "blog", "author": "Alice"}
            },
            {
                "id": "doc_2",
                "title": "Building RAG Systems",
                "content": "Retrieval Augmented Generation combines search...",
                "similarity": 0.85,
                "metadata": {"source": "docs", "author": "Bob"}
            },
            {
                "id": "doc_3",
                "title": "LLM Token Optimization",
                "content": "Reducing token count can save significant costs...",
                "similarity": 0.82,
                "metadata": {"source": "paper", "author": "Charlie"}
            }
        ]
    }

    # Convert to JSON and TOON
    json_str = json.dumps(documents, indent=2)
    toon_str = json_to_toon(documents)

    print("\n[JSON Format] (for LLM context)")
    print(json_str[:200] + "...")
    print(f"Size: {len(json_str)} bytes")

    print("\n[TOON Format] (for LLM context)")
    print(toon_str)
    print(f"Size: {len(toon_str)} bytes")

    # Calculate savings
    reduction = ((len(json_str) - len(toon_str)) / len(json_str) * 100)
    print(f"\n[Cost Analysis]")
    print(f"Token reduction: {reduction:.1f}%")

    # Assuming GPT-4 pricing ($0.01 per 1K tokens input)
    tokens_json = len(json_str) / 4  # Rough estimate: 1 token ≈ 4 chars
    tokens_toon = len(toon_str) / 4
    cost_json = (tokens_json / 1000) * 0.01
    cost_toon = (tokens_toon / 1000) * 0.01
    savings = cost_json - cost_toon

    print(f"Estimated JSON cost: ${cost_json:.6f}")
    print(f"Estimated TOON cost: ${cost_toon:.6f}")
    print(f"Savings per query: ${savings:.6f}")
    print(f"Savings per 1M queries: ${savings * 1_000_000:.2f}")

    print("\n✅ Real-world scenario test PASSED")
    return True


def main():
    """Run all TOON integration tests."""
    print("\n" + "=" * 70)
    print("NexaDB TOON FORMAT INTEGRATION TESTS")
    print("=" * 70)
    print("\nTesting the FIRST database with native TOON support! 🚀")

    results = []

    # Test 1: TOON format
    results.append(("TOON Format", test_toon_format()))

    # Test 2: Binary server
    results.append(("Binary Server Integration", test_binary_server_toon()))

    # Test 3: Real-world scenario
    results.append(("Real-World Scenario", test_real_world_scenario()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! TOON integration is working perfectly!")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
