# NexaDB YCSB Benchmark

YCSB (Yahoo! Cloud Serving Benchmark) binding and benchmark suite for NexaDB.

## Overview

This directory contains a complete YCSB binding implementation for benchmarking NexaDB using the industry-standard Yahoo Cloud Serving Benchmark framework.

## Quick Start

### Prerequisites
- Java 8+
- Maven 3+
- NexaDB server running on port 6970

### Build
```bash
cd YCSB_BENCHMARK
mvn clean package -DskipTests
```

### Run Benchmark
```bash
# Run complete benchmark (load + run)
java -cp "target/classes:target/dependency/*" site.ycsb.Benchmark \
    -records 100000 -operations 100000 -threads 16 -workload a

# Load phase only
java -cp "target/classes:target/dependency/*" site.ycsb.Benchmark \
    -load -records 100000 -threads 16

# Run phase only (requires loaded data)
java -cp "target/classes:target/dependency/*" site.ycsb.Benchmark \
    -run -records 100000 -operations 100000 -threads 16 -workload c
```

## Benchmark Results (100K Records)

### Performance Summary

| Workload | Description | Throughput | P99 Latency |
|----------|-------------|------------|-------------|
| **Load** | Insert 100K records | 11,628 ops/sec | 4.6 ms |
| **A** | 50% Read / 50% Update | **33,830 ops/sec** | 1.7 ms |
| **B** | 95% Read / 5% Update | **34,341 ops/sec** | 1.7 ms |
| **C** | 100% Read | **29,913 ops/sec** | 2.4 ms |

### Comparison with Other Databases

| Database | Workload A | Workload C | P99 Latency |
|----------|------------|------------|-------------|
| **NexaDB** | 33,830 ops/sec | 29,913 ops/sec | 1.7 ms |
| MongoDB | 20-50K ops/sec | 50-100K ops/sec | 2-10 ms |
| Redis | 80-110K ops/sec | 80-110K ops/sec | 0.5-2 ms |
| Cassandra | 10-40K ops/sec | 20-50K ops/sec | 5-20 ms |

See [BENCHMARK_REPORT.md](./BENCHMARK_REPORT.md) for detailed analysis.

## YCSB Workloads

| Workload | Read/Write | Use Case |
|----------|------------|----------|
| A | 50/50 | Session store |
| B | 95/5 | Photo tagging |
| C | 100/0 | User profile cache |
| D | Read latest | Status updates |
| E | Scan | Threaded conversations |
| F | Read-modify-write | User database |

## Configuration

Edit `nexadb.properties`:

```properties
# Connection
nexadb.host=localhost
nexadb.port=6970
nexadb.username=root
nexadb.password=nexadb123

# Settings
nexadb.timeout=30000
nexadb.retries=3
nexadb.database=default
nexadb.debug=false
```

## Project Structure

```
YCSB_BENCHMARK/
├── pom.xml                          # Maven build file
├── nexadb.properties                # Configuration
├── BENCHMARK_REPORT.md              # Full benchmark report
├── README.md                        # This file
├── src/
│   ├── main/java/site/ycsb/
│   │   ├── db/
│   │   │   ├── NexaDBClient.java    # YCSB binding
│   │   │   ├── NexaDBConnection.java # Binary protocol
│   │   │   └── NexaDBException.java
│   │   ├── Benchmark.java           # Standalone benchmark
│   │   ├── DB.java                  # YCSB interface
│   │   ├── Status.java
│   │   ├── ByteIterator.java
│   │   └── StringByteIterator.java
│   └── test/java/site/ycsb/db/
│       └── NexaDBClientTest.java    # Integration tests
├── workloads/                       # YCSB workload configs
│   ├── workloada
│   ├── workloadb
│   ├── workloadc
│   ├── workloadd
│   ├── workloade
│   ├── workloadf
│   └── workload_nexadb
└── scripts/
    ├── run_benchmarks.sh            # Run all workloads
    └── scaling_test.sh              # Thread scaling tests
```

## Implementation Details

### Binary Protocol

The binding uses NexaDB's binary protocol (MessagePack over TCP) for optimal performance:
- Port: 6970
- Header: 12 bytes (Magic + Version + Type + Flags + Length)
- Payload: MessagePack encoded

### YCSB Operations Mapping

| YCSB Operation | NexaDB Message |
|----------------|----------------|
| insert | MSG_CREATE (0x02) |
| read | MSG_READ (0x03) |
| update | MSG_UPDATE (0x04) |
| delete | MSG_DELETE (0x05) |
| scan | MSG_QUERY (0x06) |

## Running Tests

```bash
# Connection test
java -cp "target/classes:target/dependency/*" site.ycsb.db.NexaDBClientTest

# Unit tests
mvn test
```

## License

Apache License 2.0
