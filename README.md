# NexaDB - High-Performance Database with Native TOON Support

<div align="center">

**The world's FIRST database with native TOON format support**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 14+](https://img.shields.io/badge/node-14+-green.svg)](https://nodejs.org/)

[Quick Start](#quick-start) • [Features](#features) • [Admin Panel](#admin-panel) • [TOON Format](#toon-format) • [API Reference](#api-reference)

</div>

---

## 🚀 What is NexaDB?

NexaDB is a **lightweight, high-performance database** with native support for the TOON (Token-Oriented Object Notation) format - reducing LLM token usage by 40-50%.

**Perfect for:**
- 🤖 AI/ML applications and RAG systems
- 📊 Real-time analytics and dashboards
- 🔌 Microservices and APIs
- 🌐 Edge computing and IoT
- 📱 Mobile and embedded apps
- 🎯 Rapid prototyping and MVPs

---

## ✨ Features

### 🚀 World's First Native TOON Support

**What is TOON?**
- Token-Oriented Object Notation format optimized for LLMs
- **40-50% fewer tokens** than JSON
- Reduces API costs for GPT-4, Claude, and other LLM services
- Perfect for RAG (Retrieval-Augmented Generation) systems

**TOON in NexaDB:**
- Native binary protocol support (MSG_QUERY_TOON, MSG_EXPORT_TOON, MSG_IMPORT_TOON)
- Built-in TOON serialization and parsing
- CLI tools for import/export
- Admin panel with TOON export and visualization
- Real-time token statistics

### ⚡ High-Performance Binary Protocol

- **3-10x faster** than HTTP/REST
- MessagePack-based encoding
- Persistent TCP connections
- Connection pooling with 1000+ concurrent connections
- Automatic reconnection and retry logic

### 📄 JSON Document Storage

- Schema-free documents
- MongoDB-style queries
- Aggregation pipelines
- Nested field support
- Auto-generated IDs and timestamps

### 💾 LSM-Tree Storage Engine

- Write-Ahead Log (WAL) for durability
- MemTable (in-memory sorted structure)
- SSTables (Sorted String Tables on disk)
- Automatic compaction
- Crash recovery

### 🎨 Modern Admin Panel

- Beautiful dark/light theme
- Real-time query editor with JSON/TOON toggle
- One-click TOON export with token statistics
- Collection management
- Document CRUD operations
- Performance monitoring

### 📦 Official SDKs

- **Python client** with TOON support
- **JavaScript/Node.js client** with TOON support
- TypeScript definitions included

---

## 🎯 Quick Start

### Installation via Homebrew (macOS/Linux)

```bash
# Add the tap
brew tap krishcdbry/nexadb

# Install NexaDB
brew install nexadb

# Start the server
nexadb start

# Access admin panel
open http://localhost:9999
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/krishcdbry/nexadb.git
cd nexadb

# Install Python dependencies
pip3 install msgpack

# Start binary server (port 6970)
python3 nexadb_binary_server.py --port 6970 &

# Start admin HTTP server (port 9999)
python3 admin_server.py --port 9999 &

# Access admin panel
open http://localhost:9999
```

---

## 🖥️ Admin Panel

Access the admin panel at `http://localhost:9999`

**Features:**
- 📊 Dashboard with real-time statistics
- 📚 Collection browser with document viewer
- 🔍 Query editor with JSON/TOON toggle
- 📤 One-click TOON export with token savings
- 📈 Performance monitoring
- 🎨 Beautiful dark/light themes
- 🖼️ Responsive design

**TOON Export:**
1. Select a collection
2. Click "Export TOON" button
3. View token reduction statistics (36-50%)
4. Copy TOON data or download as .toon file
5. Use in your LLM applications to save costs!

---

## 🎯 TOON Format

### What is TOON?

TOON (Token-Oriented Object Notation) is a compact data format optimized for Large Language Models:

**JSON Format (2,213 bytes):**
```json
[
  {"_id": "abc123", "name": "Alice", "email": "alice@example.com", "age": 28, "city": "San Francisco"},
  {"_id": "def456", "name": "Bob", "email": "bob@example.com", "age": 34, "city": "New York"},
  ...
]
```

**TOON Format (1,396 bytes - 36.9% reduction!):**
```toon
collection: test_users
documents[11]{_id,name,email,age,city,role}:
  abc123,Alice,alice@example.com,28,San Francisco,engineer
  def456,Bob,bob@example.com,34,New York,manager
  ...
count: 11
```

### Using TOON in NexaDB

**Export to TOON (CLI):**
```bash
python3 toon_cli.py export test_users output.toon
```

**Import from TOON (CLI):**
```bash
python3 toon_cli.py import input.toon new_collection
```

**Query in TOON format (Python):**
```python
from nexaclient import NexaClient

client = NexaClient(host='localhost', port=6970)
client.connect()

# Query and get TOON format response
toon_data, stats = client.query_toon('test_users', {}, limit=100)

print(f"TOON Data:\n{toon_data}")
print(f"Token Reduction: {stats['reduction_percent']}%")
print(f"Savings (1M calls): ${stats['reduction_percent'] * 10:.2f}")
```

**Export collection to TOON (Python):**
```python
toon_data, stats = client.export_toon('test_users')

# Save to file
with open('export.toon', 'w') as f:
    f.write(toon_data)

print(f"Exported with {stats['reduction_percent']}% token reduction!")
```

### TOON Benefits

- ✅ **40-50% fewer tokens** for LLM APIs
- ✅ **Lower costs** (GPT-4, Claude, etc.)
- ✅ **Faster processing** (less data to parse)
- ✅ **More context** fits in token limits
- ✅ **Perfect for RAG** systems

---

## 🔌 Python Client Usage

### Installation

```bash
# Install the NexaDB Python client
cd nexaclient/python
pip install -e .
```

### Basic Usage

```python
from nexaclient import NexaClient

# Connect to binary server
client = NexaClient(host='localhost', port=6970)
client.connect()

# Insert documents
doc_id = client.insert('users', {
    'name': 'Alice Johnson',
    'email': 'alice@example.com',
    'age': 28,
    'city': 'San Francisco'
})

# Query documents
results = client.find('users', {'age': {'$gt': 25}}, limit=10)
for doc in results:
    print(f"{doc['name']} - {doc['age']}")

# Update document
client.update('users', doc_id, {'age': 29})

# Delete document
client.delete('users', doc_id)

# Disconnect
client.disconnect()
```

### Aggregation

```python
# Group by city and count
pipeline = [
    {'$match': {'status': 'active'}},
    {'$group': {
        '_id': '$city',
        'count': {'$sum': 1},
        'avg_age': {'$avg': '$age'}
    }},
    {'$sort': {'count': -1}},
    {'$limit': 10}
]

results = client.aggregate('users', pipeline)
for result in results:
    print(f"{result['_id']}: {result['count']} users")
```

---

## 🔌 JavaScript/Node.js Client Usage

### Installation

```bash
npm install nexaclient
```

### Basic Usage

```javascript
const { NexaClient } = require('nexaclient');

async function main() {
    // Connect to binary server
    const client = new NexaClient({ host: 'localhost', port: 6970 });
    await client.connect();

    // Insert document
    const docId = await client.insert('users', {
        name: 'Alice Johnson',
        email: 'alice@example.com',
        age: 28,
        city: 'San Francisco'
    });

    // Query documents
    const results = await client.find('users', { age: { $gt: 25 } }, 10);
    results.forEach(doc => {
        console.log(`${doc.name} - ${doc.age}`);
    });

    // Update document
    await client.update('users', docId, { age: 29 });

    // Delete document
    await client.delete('users', docId);

    // Disconnect
    client.disconnect();
}

main();
```

### TOON Support

```javascript
// Query in TOON format
const { toonData, stats } = await client.queryToon('users', {}, 100);
console.log('Token Reduction:', stats.reduction_percent + '%');

// Export to TOON
const { toonData, stats } = await client.exportToon('users');
console.log('TOON Data:', toonData);
console.log('Savings (1M calls): $' + (stats.reduction_percent * 10).toFixed(2));
```

---

## 📊 Binary Protocol

NexaDB uses a custom binary protocol built on MessagePack for maximum performance.

### Message Types

```
0x01 - MSG_CONNECT       # Handshake
0x02 - MSG_INSERT        # Insert document
0x03 - MSG_FIND          # Query documents
0x04 - MSG_UPDATE        # Update document
0x05 - MSG_DELETE        # Delete document
0x06 - MSG_COUNT         # Count documents
0x07 - MSG_AGGREGATE     # Aggregation pipeline
0x08 - MSG_DROP          # Drop collection
0x09 - MSG_COLLECTIONS   # List collections
0x0A - MSG_STATS         # Server statistics

# TOON Protocol (World's First!)
0x0B - MSG_QUERY_TOON    # Query with TOON response
0x0C - MSG_EXPORT_TOON   # Export collection to TOON
0x0D - MSG_IMPORT_TOON   # Import TOON data

0x81 - MSG_SUCCESS       # Success response
0x82 - MSG_ERROR         # Error response
```

### Message Format

```
[Header: 12 bytes]
- Magic number: 0x4E455841 (4 bytes) "NEXA"
- Version: 0x01 (1 byte)
- Message type: 0xXX (1 byte)
- Flags: 0x00 (2 bytes)
- Payload length: (4 bytes)

[Payload: N bytes]
- MessagePack encoded data
```

---

## 🔍 Query Language

### Comparison Operators

```python
{'age': {'$eq': 25}}      # Equal to
{'age': {'$ne': 25}}      # Not equal to
{'age': {'$gt': 25}}      # Greater than
{'age': {'$gte': 25}}     # Greater than or equal
{'age': {'$lt': 25}}      # Less than
{'age': {'$lte': 25}}     # Less than or equal
```

### Array Operators

```python
{'tags': {'$in': ['python', 'javascript']}}    # Contains any
{'tags': {'$nin': ['java', 'c++']}}            # Contains none
```

### Text Operators

```python
{'name': {'$regex': 'John'}}                   # Regex match
```

### Logical Operators

```python
{
    '$and': [
        {'age': {'$gt': 25}},
        {'city': 'San Francisco'}
    ]
}

{
    '$or': [
        {'status': 'active'},
        {'premium': True}
    ]
}
```

### Nested Fields

```python
{'profile.age': {'$gt': 25}}                   # Access nested field
{'address.city': 'San Francisco'}              # Nested object
```

---

## 📈 Performance

### Benchmarks (MacBook Pro M1, 16GB RAM)

**Binary Protocol Performance:**
- Insert: **50,000 docs/sec**
- Find: **80,000 queries/sec**
- Update: **45,000 ops/sec**
- Aggregation: **20,000 docs/sec**

**TOON Format Performance:**
- Serialization: **100,000 docs/sec**
- Parsing: **80,000 docs/sec**
- Token reduction: **36-50%**

**Admin Panel:**
- Query execution: <100ms
- TOON export: <200ms for 10K docs
- Real-time updates: 60 FPS

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Admin Panel (HTTP)                    │
│              http://localhost:9999                      │
│  • Collection Browser  • Query Editor  • TOON Export   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Admin Server (Python HTTP)                 │
│                    Port 9999                            │
│  • Serves static files  • TOON export API              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│          Binary Protocol Server (Python)                │
│                    Port 6970                            │
│  • MessagePack protocol  • Connection pooling          │
│  • TOON support  • Aggregation pipeline                │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              LSM-Tree Storage Engine                    │
│  • WAL (Write-Ahead Log)  • MemTable (in-memory)       │
│  • SSTables (disk)  • Compaction  • Crash recovery    │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Production Files

```
nexadb/
├── nexadb_binary_server.py    # Binary protocol server (port 6970)
├── admin_server.py             # HTTP server for admin panel (port 9999)
├── nexadb_admin_modern.html    # Admin panel UI
├── storage_engine.py           # LSM-Tree storage engine
├── nexadb_cli.py               # Command-line interface
├── toon_format.py              # TOON serialization/parsing
├── toon_cli.py                 # TOON import/export CLI
├── setup.py                    # Package setup
├── logo-light.svg              # Admin panel logo (light)
├── logo-dark.svg               # Admin panel logo (dark)
├── README.md                   # This file
├── BENCHMARK_RESULTS.md        # Performance benchmarks
└── nexaclient/                 # Client SDKs
    ├── python/                 # Python client
    └── src/                    # JavaScript client
```

---

## 🛠️ Development

### Run Tests

```bash
# Start binary server
python3 nexadb_binary_server.py --port 6970

# Start admin server
python3 admin_server.py --port 9999

# Test TOON export
python3 toon_cli.py export test_users output.toon

# Test TOON import
python3 toon_cli.py import output.toon test_collection
```

### Configuration

**Binary Server:**
```python
python3 nexadb_binary_server.py --host 0.0.0.0 --port 6970
```

**Admin Server:**
```python
python3 admin_server.py --port 9999
```

---

## 🗺️ Roadmap

### ✅ Completed

- [x] LSM-Tree storage engine
- [x] Binary protocol with MessagePack
- [x] Connection pooling
- [x] JSON document storage
- [x] MongoDB-style queries
- [x] Aggregation pipeline
- [x] Python SDK
- [x] JavaScript/Node.js SDK
- [x] **Native TOON format support** 🎉
- [x] TOON CLI tools
- [x] Modern admin panel with TOON export
- [x] Query editor with JSON/TOON toggle
- [x] Homebrew distribution

### 🚧 In Progress

- [ ] Vector embeddings for AI/ML
- [ ] Full-text search
- [ ] Secondary indexes
- [ ] Replication

### 🔮 Future

- [ ] Sharding and clustering
- [ ] GraphQL API
- [ ] Time-series optimization
- [ ] Docker image
- [ ] Kubernetes operator

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

**Areas to contribute:**
- Performance optimizations
- Additional query operators
- Testing and benchmarks
- Documentation improvements
- Client SDKs for other languages

---

## 📞 Support

- **GitHub:** [github.com/krishcdbry/nexadb](https://github.com/krishcdbry/nexadb)
- **Issues:** [GitHub Issues](https://github.com/krishcdbry/nexadb/issues)
- **Twitter:** [@krishcdbry](https://twitter.com/krishcdbry)

---

<div align="center">

**🚀 The world's FIRST database with native TOON support!**

**Built by [Krish](https://github.com/krishcdbry)**

[⭐ Star on GitHub](https://github.com/krishcdbry/nexadb) • [📖 TOON Spec](https://github.com/toon-format/toon)

</div>
