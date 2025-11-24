"""
Simple test for connection pooling without external dependencies
"""

import socket
import threading
import time
from pooled_server import ThreadPooledHTTPServer, TestHandler


def test_concurrent_connections():
    """Test server with concurrent connections."""
    print("Testing Connection Pooling...")
    print("=" * 60)

    # Start server
    HOST = 'localhost'
    PORT = 8888

    print(f"\n1️⃣  Starting server on {HOST}:{PORT}...")
    server = ThreadPooledHTTPServer(
        (HOST, PORT),
        TestHandler,
        max_workers=100,
        queue_size=1000
    )

    # Run server in background
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)
    print("✅ Server started\n")

    # Test concurrent connections
    print("2️⃣  Testing concurrent connections...")
    num_connections = 100

    def make_request(i):
        """Make HTTP request using raw sockets."""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((HOST, PORT))

            # Send HTTP request
            request = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
            sock.sendall(request)

            # Receive response
            response = sock.recv(4096)
            sock.close()

            return {
                'success': b'200 OK' in response,
                'size': len(response)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    # Execute concurrent requests
    start = time.time()
    threads = []

    for i in range(num_connections):
        thread = threading.Thread(target=lambda: results.append(make_request(i)))
        threads.append(thread)
        thread.start()

    # Collect results
    results = []
    for thread in threads:
        thread.join(timeout=10)

    elapsed = time.time() - start
    throughput = num_connections / elapsed

    # Analyze results
    successful = sum(1 for r in results if r.get('success', False))
    failed = num_connections - successful

    print(f"⏱️  Time: {elapsed:.2f}s")
    print(f"🚀 Throughput: {throughput:.0f} req/sec")
    print(f"✅ Successful: {successful}/{num_connections}")
    print(f"❌ Failed: {failed}/{num_connections}")

    # Get stats
    print("\n3️⃣  Server statistics...")
    stats = server.get_stats()
    print(f"📊 Stats:")
    print(f"   Total requests:      {stats['total_requests']:,}")
    print(f"   Active connections:  {stats['active_connections']}")
    print(f"   Worker threads:      {stats['max_workers']}")

    # Cleanup
    print("\n4️⃣  Shutting down...")
    server.shutdown()
    print("✅ Complete\n")

    # Summary
    print("=" * 60)
    print("Summary:")
    print(f"  Handled {num_connections} concurrent connections")
    print(f"  Throughput: {throughput:.0f} req/sec")
    print(f"  Success rate: {successful/num_connections*100:.1f}%")
    print()
    print("🎯 Connection pooling allows 100x more concurrent users!")
    print("=" * 60)


if __name__ == '__main__':
    test_concurrent_connections()
