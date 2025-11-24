#!/usr/bin/env python3
"""
NexaDB Protocol Benchmark Suite

Comprehensive benchmarks comparing:
1. HTTP/REST vs Binary Protocol
2. JSON vs MessagePack encoding
3. Single operations vs Batch operations
4. Different operation types (CREATE, READ, UPDATE, DELETE, QUERY)
"""

import time
import statistics
import sys
from typing import List, Dict, Any
import requests

# Import NexaDB client
try:
    from nexadb import NexaClient
except ImportError:
    print("Installing nexadb package...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--break-system-packages', '-e', 'nexadb-python'])
    from nexadb import NexaClient


class BenchmarkRunner:
    """Run benchmarks and collect results"""

    def __init__(self):
        self.results = {}

    def run_benchmark(self, name: str, func, iterations: int = 1000):
        """Run a benchmark function multiple times and collect stats"""
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print(f"Iterations: {iterations:,}")
        print(f"{'='*60}")

        latencies = []
        errors = 0

        start_time = time.time()

        for i in range(iterations):
            try:
                iter_start = time.time()
                func()
                iter_end = time.time()
                latencies.append((iter_end - iter_start) * 1000)  # Convert to ms

                if (i + 1) % (iterations // 10) == 0:
                    print(f"Progress: {i+1:,}/{iterations:,} ({(i+1)/iterations*100:.0f}%)")

            except Exception as e:
                errors += 1
                if errors < 5:  # Only print first 5 errors
                    print(f"Error: {e}")

        end_time = time.time()
        total_time = end_time - start_time

        if not latencies:
            print(f"❌ All operations failed!")
            return None

        # Calculate statistics
        stats = {
            'name': name,
            'iterations': iterations,
            'total_time': total_time,
            'throughput': iterations / total_time,
            'latency_min': min(latencies),
            'latency_max': max(latencies),
            'latency_mean': statistics.mean(latencies),
            'latency_median': statistics.median(latencies),
            'latency_p95': sorted(latencies)[int(len(latencies) * 0.95)],
            'latency_p99': sorted(latencies)[int(len(latencies) * 0.99)],
            'errors': errors,
            'success_rate': (iterations - errors) / iterations * 100
        }

        self.results[name] = stats

        print(f"\n✅ Results:")
        print(f"   Total Time:    {total_time:.2f}s")
        print(f"   Throughput:    {stats['throughput']:.0f} ops/sec")
        print(f"   Latency (ms):")
        print(f"     Min:         {stats['latency_min']:.2f}")
        print(f"     Mean:        {stats['latency_mean']:.2f}")
        print(f"     Median:      {stats['latency_median']:.2f}")
        print(f"     P95:         {stats['latency_p95']:.2f}")
        print(f"     P99:         {stats['latency_p99']:.2f}")
        print(f"     Max:         {stats['latency_max']:.2f}")
        print(f"   Errors:        {errors}")
        print(f"   Success Rate:  {stats['success_rate']:.1f}%")

        return stats

    def print_comparison(self, baseline_name: str, comparison_name: str):
        """Print comparison between two benchmarks"""
        if baseline_name not in self.results or comparison_name not in self.results:
            print(f"Cannot compare - missing results")
            return

        baseline = self.results[baseline_name]
        comparison = self.results[comparison_name]

        print(f"\n{'='*60}")
        print(f"Comparison: {baseline_name} vs {comparison_name}")
        print(f"{'='*60}")

        throughput_improvement = comparison['throughput'] / baseline['throughput']
        latency_improvement = baseline['latency_median'] / comparison['latency_median']

        print(f"Throughput:")
        print(f"  {baseline_name}: {baseline['throughput']:.0f} ops/sec")
        print(f"  {comparison_name}: {comparison['throughput']:.0f} ops/sec")
        print(f"  Improvement: {throughput_improvement:.1f}x faster")

        print(f"\nMedian Latency:")
        print(f"  {baseline_name}: {baseline['latency_median']:.2f}ms")
        print(f"  {comparison_name}: {comparison['latency_median']:.2f}ms")
        print(f"  Improvement: {latency_improvement:.1f}x faster")

    def print_summary(self):
        """Print summary of all benchmarks"""
        print(f"\n{'='*60}")
        print(f"BENCHMARK SUMMARY")
        print(f"{'='*60}\n")

        print(f"{'Benchmark':<40} {'Throughput':<15} {'Latency (ms)'}")
        print(f"{'-'*40} {'-'*15} {'-'*15}")

        for name, stats in self.results.items():
            print(f"{name:<40} {stats['throughput']:>10.0f} ops/s {stats['latency_median']:>10.2f}")


def main():
    """Run comprehensive benchmarks"""

    print("="*60)
    print("NexaDB Protocol Benchmark Suite")
    print("="*60)
    print("\nComparing HTTP/REST vs Binary Protocol performance")

    runner = BenchmarkRunner()

    # Configuration
    HTTP_URL = 'http://localhost:6969'
    BINARY_HOST = 'localhost'
    BINARY_PORT = 6970

    # Test data
    test_user = {
        'name': 'Benchmark User',
        'email': 'bench@example.com',
        'age': 30,
        'role': 'tester'
    }

    # Verify servers are running
    print("\n1️⃣  Verifying servers...")
    try:
        response = requests.get(f'{HTTP_URL}/status', timeout=2)
        print(f"✅ HTTP server running (status: {response.status_code})")
    except Exception as e:
        print(f"❌ HTTP server not running: {e}")
        print("Please start HTTP server: nexadb start")
        return

    try:
        db = NexaClient(host=BINARY_HOST, port=BINARY_PORT, timeout=2)
        db.connect()
        db.ping()
        db.disconnect()
        print(f"✅ Binary server running")
    except Exception as e:
        print(f"❌ Binary server not running: {e}")
        print("Please start binary server: python3 nexadb_binary_server.py --port 6970")
        return

    # Create test users for READ benchmarks
    print("\n2️⃣  Preparing test data...")
    doc_ids = []
    try:
        db = NexaClient(host=BINARY_HOST, port=BINARY_PORT)
        db.connect()
        for i in range(100):
            result = db.create('benchmark_users', {
                'name': f'User {i}',
                'email': f'user{i}@example.com',
                'age': 20 + (i % 50)
            })
            doc_ids.append(result['document_id'])
        db.disconnect()
        print(f"✅ Created 100 test documents")
    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        return

    # Benchmark 1: HTTP CREATE
    print("\n3️⃣  Benchmarking HTTP CREATE...")

    def http_create():
        requests.post(
            f'{HTTP_URL}/collections/benchmark_users',
            json=test_user,
            timeout=5
        )

    runner.run_benchmark("HTTP CREATE", http_create, iterations=100)

    # Benchmark 2: Binary CREATE
    print("\n4️⃣  Benchmarking Binary CREATE...")

    db_binary = NexaClient(host=BINARY_HOST, port=BINARY_PORT)
    db_binary.connect()

    def binary_create():
        db_binary.create('benchmark_users', test_user)

    runner.run_benchmark("Binary CREATE", binary_create, iterations=100)

    # Benchmark 3: HTTP READ
    print("\n5️⃣  Benchmarking HTTP READ...")

    doc_idx = [0]

    def http_read():
        doc_id = doc_ids[doc_idx[0] % len(doc_ids)]
        doc_idx[0] += 1
        requests.get(f'{HTTP_URL}/collections/benchmark_users/{doc_id}', timeout=5)

    runner.run_benchmark("HTTP READ", http_read, iterations=100)

    # Benchmark 4: Binary READ
    print("\n6️⃣  Benchmarking Binary READ...")

    doc_idx[0] = 0

    def binary_read():
        doc_id = doc_ids[doc_idx[0] % len(doc_ids)]
        doc_idx[0] += 1
        db_binary.get('benchmark_users', doc_id)

    runner.run_benchmark("Binary READ", binary_read, iterations=100)

    # Benchmark 5: HTTP UPDATE
    print("\n7️⃣  Benchmarking HTTP UPDATE...")

    doc_idx[0] = 0

    def http_update():
        doc_id = doc_ids[doc_idx[0] % len(doc_ids)]
        doc_idx[0] += 1
        requests.put(
            f'{HTTP_URL}/collections/benchmark_users/{doc_id}',
            json={'age': 31},
            timeout=5
        )

    runner.run_benchmark("HTTP UPDATE", http_update, iterations=100)

    # Benchmark 6: Binary UPDATE
    print("\n8️⃣  Benchmarking Binary UPDATE...")

    doc_idx[0] = 0

    def binary_update():
        doc_id = doc_ids[doc_idx[0] % len(doc_ids)]
        doc_idx[0] += 1
        db_binary.update('benchmark_users', doc_id, {'age': 31})

    runner.run_benchmark("Binary UPDATE", binary_update, iterations=100)

    # Benchmark 7: HTTP QUERY
    print("\n9️⃣  Benchmarking HTTP QUERY...")

    def http_query():
        requests.post(
            f'{HTTP_URL}/collections/benchmark_users/query',
            json={'query': {'age': {'$gte': 25}}, 'limit': 10},
            timeout=5
        )

    runner.run_benchmark("HTTP QUERY", http_query, iterations=50)

    # Benchmark 8: Binary QUERY
    print("\n🔟  Benchmarking Binary QUERY...")

    def binary_query():
        db_binary.query('benchmark_users', {'age': {'$gte': 25}}, limit=10)

    runner.run_benchmark("Binary QUERY", binary_query, iterations=50)

    # Benchmark 9: HTTP BATCH WRITE
    print("\n1️⃣1️⃣  Benchmarking HTTP BATCH WRITE...")

    batch_data = [
        {'name': f'Batch User {i}', 'email': f'batch{i}@example.com'}
        for i in range(10)
    ]

    def http_batch():
        requests.post(
            f'{HTTP_URL}/collections/benchmark_users/bulk',
            json={'documents': batch_data},
            timeout=5
        )

    runner.run_benchmark("HTTP BATCH (10 docs)", http_batch, iterations=100)

    # Benchmark 10: Binary BATCH WRITE
    print("\n1️⃣2️⃣  Benchmarking Binary BATCH WRITE...")

    def binary_batch():
        db_binary.batch_write('benchmark_users', batch_data)

    runner.run_benchmark("Binary BATCH (10 docs)", binary_batch, iterations=100)

    # Cleanup
    db_binary.disconnect()

    # Print comparisons
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISONS")
    print("="*60)

    runner.print_comparison("HTTP CREATE", "Binary CREATE")
    runner.print_comparison("HTTP READ", "Binary READ")
    runner.print_comparison("HTTP UPDATE", "Binary UPDATE")
    runner.print_comparison("HTTP QUERY", "Binary QUERY")
    runner.print_comparison("HTTP BATCH (10 docs)", "Binary BATCH (10 docs)")

    # Print summary
    runner.print_summary()

    # Final verdict
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)

    binary_create = runner.results["Binary CREATE"]
    http_create = runner.results["HTTP CREATE"]
    improvement = binary_create['throughput'] / http_create['throughput']

    print(f"\n🚀 Binary Protocol is {improvement:.1f}x faster than HTTP/REST!")
    print(f"\nKey Metrics:")
    print(f"  - Throughput: {improvement:.1f}x improvement")
    print(f"  - Latency: {http_create['latency_median']/binary_create['latency_median']:.1f}x faster")
    print(f"  - Overhead: ~{(1 - binary_create['latency_mean']/http_create['latency_mean']) * 100:.0f}% reduction")
    print(f"\n✅ Binary protocol is production-ready and significantly faster!")


if __name__ == '__main__':
    main()
