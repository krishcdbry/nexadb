# How to Build Your Own Database - Complete Guide

This document explains **exactly how NexaDB was built** so you can understand every component and build your own database.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       NexaDB Stack                          │
├─────────────────────────────────────────────────────────────┤
│  Client SDKs (Python, JavaScript)                           │
├─────────────────────────────────────────────────────────────┤
│  HTTP/REST API Server (nexadb_server.py)                    │
├─────────────────────────────────────────────────────────────┤
│  Database Core (veloxdb_core.py)                            │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ Collections  │ Vector Store │ Aggregation  │            │
│  └──────────────┴──────────────┴──────────────┘            │
├─────────────────────────────────────────────────────────────┤
│  Storage Engine (storage_engine.py)                         │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ WAL          │ MemTable     │ SSTables     │            │
│  └──────────────┴──────────────┴──────────────┘            │
├─────────────────────────────────────────────────────────────┤
│  Disk (Files)                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Component 1: Storage Engine (LSM-Tree)

**File:** `storage_engine.py` (600 lines)

### What It Does:
Handles **how data is physically stored on disk**.

### Key Data Structures:

#### 1. MemTable (In-Memory Sorted Map)
```python
class MemTable:
    def __init__(self, max_size=1MB):
        self.data = OrderedDict()  # Sorted key-value pairs
        self.size = 0

    def put(self, key, value):
        self.data[key] = value
        self.data = OrderedDict(sorted(self.data.items()))  # Keep sorted
        return self.size >= self.max_size  # True if full
```

**Why?**
- Writes are **instant** (in-memory)
- Auto-sorted for range queries
- Signals when full → flush to disk

#### 2. Write-Ahead Log (WAL)
```python
class WAL:
    def append(self, operation, key, value):
        # Format: [timestamp|operation|key|value]
        entry = struct.pack('Q', timestamp)  # 8 bytes
        entry += encode(operation)
        entry += encode(key)
        entry += encode(value)

        self.file.write(entry)
        os.fsync(self.file)  # Force write to disk
```

**Why?**
- **Crash recovery:** If server crashes, replay WAL to rebuild MemTable
- **Durability:** Write confirmed only after WAL write

#### 3. SSTable (Sorted String Table)
```python
class SSTable:
    @staticmethod
    def create(filepath, sorted_data):
        # Write data file
        for key, value in sorted_data:
            offset = file.tell()
            index[key] = offset  # Remember position
            file.write(encode(key, value))

        # Write index file (for fast lookups)
        pickle.dump(index, index_file)
```

**Format:**
```
data_file:
  [key_len|key|value_len|value][key_len|key|value_len|value]...

index_file:
  {'key1': offset1, 'key2': offset2, ...}
```

**Why?**
- **Immutable:** Never modified after creation
- **Indexed:** O(1) lookup using offset
- **Sorted:** Efficient range scans

#### 4. LSM Engine (Orchestrator)
```python
class LSMStorageEngine:
    def put(self, key, value):
        # 1. Write to WAL (durability)
        self.wal.append('PUT', key, value)

        # 2. Write to MemTable (fast access)
        needs_flush = self.memtable.put(key, value)

        # 3. Flush if MemTable full
        if needs_flush:
            self._flush_memtable()

    def get(self, key):
        # 1. Check MemTable first (newest data)
        value = self.memtable.get(key)
        if value:
            return value

        # 2. Check SSTables (newest to oldest)
        for sstable in reversed(self.sstables):
            value = sstable.get(key)
            if value:
                return value

        return None

    def _flush_memtable(self):
        # Convert MemTable → SSTable
        sstable = SSTable.create(path, self.memtable.data)
        self.sstables.append(sstable)

        # Clear MemTable and WAL
        self.memtable.clear()
        self.wal.clear()

    def _compact(self):
        # Merge all SSTables, remove duplicates and tombstones
        merged_data = {}
        for sstable in self.sstables:
            for key, value in sstable.all_items():
                merged_data[key] = value  # Latest wins

        # Create new compacted SSTable
        new_sstable = SSTable.create(path, merged_data)

        # Delete old SSTables
        for sstable in self.sstables:
            sstable.delete()

        self.sstables = [new_sstable]
```

### Flow Diagrams:

**Write Path:**
```
Client calls put('name', 'Alice')
    ↓
1. Append to WAL ────────────┐
   [timestamp|PUT|name|Alice] │
   fsync() ← Durability!      │
    ↓                         │
2. Insert to MemTable         │  If crash happens here,
   {'name': 'Alice'}          │  WAL can rebuild MemTable
    ↓                         │
3. Check if full              │
   size >= 1MB? ─────────────┘
    ↓ Yes
4. Flush to SSTable
   sstable_1234567890.data
   sstable_1234567890.index
    ↓
5. Clear MemTable & WAL
```

**Read Path:**
```
Client calls get('name')
    ↓
1. Check MemTable
   Found? → Return 'Alice'
    ↓ Not found
2. Check SSTable[0] (newest)
   Found? → Return value
    ↓ Not found
3. Check SSTable[1]
   ...
    ↓ Not found in any
Return None
```

**Compaction (Background Thread):**
```
Every 10 seconds:
    ↓
Check if ≥3 SSTables exist
    ↓ Yes
Merge all SSTables:
  SSTable[0]: {'a': 1, 'b': 2}
  SSTable[1]: {'a': 3, 'c': 4}  ← 'a' updated
  SSTable[2]: {'d': TOMBSTONE}  ← 'd' deleted
    ↓
Merged result:
  {'a': 3, 'b': 2, 'c': 4}  ← 'd' removed, 'a' latest value
    ↓
Write new SSTable
Delete old SSTables
```

---

## 📄 Component 2: Document Database (veloxdb_core.py)

**File:** `veloxdb_core.py` (700 lines)

### What It Does:
Adds **JSON document support** on top of the storage engine.

### Key Classes:

#### 1. Document
```python
class Document:
    def __init__(self, data, doc_id=None):
        self.id = doc_id or sha256(timestamp)[:16]
        self.data = data
        self.created_at = now()
        self.updated_at = now()

    def to_dict(self):
        return {
            '_id': self.id,
            '_created_at': self.created_at,
            '_updated_at': self.updated_at,
            **self.data  # User's data
        }

    def to_bytes(self):
        return json.dumps(self.to_dict()).encode('utf-8')
```

**Why?**
- Auto-generates IDs (SHA-256 hash of timestamp)
- Adds timestamps for audit trail
- Serializes to bytes for storage

#### 2. Collection
```python
class Collection:
    def insert(self, data):
        doc = Document(data)

        # Store in engine with key: "collection:users:doc:a1b2c3"
        key = f"collection:{self.name}:doc:{doc.id}"
        self.engine.put(key, doc.to_bytes())

        return doc.id

    def find(self, query, limit=100):
        # Scan all documents in collection
        prefix = f"collection:{self.name}:doc:"
        all_docs = self.engine.range_scan(prefix, prefix + '\xff')

        results = []
        for _, doc_bytes in all_docs:
            doc = Document.from_bytes(doc_bytes)
            if self._match_query(doc.to_dict(), query):
                results.append(doc.to_dict())
                if len(results) >= limit:
                    break

        return results

    def _match_query(self, doc, query):
        for field, condition in query.items():
            value = doc.get(field)

            if isinstance(condition, dict):
                # Query operators
                for op, operand in condition.items():
                    if op == '$gt' and not (value > operand):
                        return False
                    if op == '$gte' and not (value >= operand):
                        return False
                    # ... more operators
            else:
                # Simple equality
                if value != condition:
                    return False

        return True
```

**Query Example:**
```python
# Query: Find users with age > 25 and name contains 'Alice'
query = {
    'age': {'$gt': 25},
    'name': {'$regex': 'Alice'}
}

users.find(query)
```

#### 3. Aggregation Pipeline
```python
def aggregate(self, pipeline):
    results = self.find(limit=1000000)  # Start with all docs

    for stage in pipeline:
        if '$match' in stage:
            # Filter documents
            results = [r for r in results if match(r, stage['$match'])]

        elif '$group' in stage:
            # Group by field
            groups = {}
            for doc in results:
                key = doc[stage['$group']['_id']]
                groups.setdefault(key, []).append(doc)

            # Apply aggregation functions
            results = []
            for key, docs in groups.items():
                results.append({
                    '_id': key,
                    'count': len(docs),
                    'sum': sum(d['amount'] for d in docs)
                })

        elif '$sort' in stage:
            # Sort by field
            field, direction = list(stage['$sort'].items())[0]
            results.sort(key=lambda x: x[field], reverse=(direction == -1))
```

**Example:**
```python
sales.aggregate([
    {'$match': {'region': 'North'}},         # Filter
    {'$group': {                              # Group by product
        '_id': '$product',
        'total': {'$sum': '$amount'}
    }},
    {'$sort': {'total': -1}},                # Sort descending
    {'$limit': 10}                            # Top 10
])
```

#### 4. Vector Collection (AI/ML)
```python
class VectorCollection:
    def insert(self, document, vector):
        # Insert document
        doc_id = self.collection.insert(document)

        # Store vector separately
        vector_key = f"vector:{self.name}:{doc_id}"
        self.engine.put(vector_key, json.dumps(vector))

        return doc_id

    def search(self, query_vector, limit=10):
        # Load all vectors
        all_vectors = self.engine.range_scan(f"vector:{self.name}:", ...)

        # Calculate cosine similarity
        similarities = []
        for vector_key, vector_bytes in all_vectors:
            vector = json.loads(vector_bytes)
            similarity = cosine_similarity(query_vector, vector)
            similarities.append((doc_id, similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Get top documents
        return similarities[:limit]

def cosine_similarity(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    mag1 = sqrt(sum(x * x for x in v1))
    mag2 = sqrt(sum(x * x for x in v2))
    return dot_product / (mag1 * mag2)
```

---

## 🌐 Component 3: HTTP Server (nexadb_server.py)

**File:** `nexadb_server.py` (400 lines)

### What It Does:
Provides **RESTful HTTP API** for remote access.

### Key Components:

#### 1. Request Handler
```python
class NexaDBHandler(BaseHTTPRequestHandler):
    db = VeloxDB('./data')  # Shared database instance

    def do_POST(self):
        path = self.path  # /collections/users
        body = self._parse_json_body()

        if path == '/collections/users':
            # Insert document
            doc_id = self.db.collection('users').insert(body)
            self._send_json({
                'status': 'success',
                'document_id': doc_id
            })
```

#### 2. Authentication
```python
def _authenticate(self):
    api_key = self.headers.get('X-API-Key')
    if api_key not in self.api_keys:
        self._send_error('Unauthorized', 401)
        return False
    return True
```

#### 3. Endpoints
```python
# Collection operations
POST   /collections/{name}           → Insert
GET    /collections/{name}           → List
GET    /collections/{name}/{id}      → Get by ID
PUT    /collections/{name}/{id}      → Update
DELETE /collections/{name}/{id}      → Delete

# Querying
POST   /collections/{name}/query     → Complex query
POST   /collections/{name}/aggregate → Aggregation

# Vector search
POST   /vector/{name}/search         → Similarity search

# Admin
GET    /status                       → Server status
GET    /stats                        → Database stats
```

---

## 🐍 Component 4: Python Client SDK (nexadb_client.py)

**File:** `nexadb_client.py` (400 lines)

### What It Does:
Provides **easy-to-use Python API** for developers.

```python
class NexaDB:
    def __init__(self, host, port, api_key):
        self.base_url = f"http://{host}:{port}"
        self.api_key = api_key

    def collection(self, name):
        return CollectionClient(name, self.base_url, self.api_key)

class CollectionClient:
    def insert(self, document):
        response = requests.post(
            f"{self.base_url}/collections/{self.name}",
            json=document,
            headers={'X-API-Key': self.api_key}
        )
        return response.json()['document_id']

    def find(self, query, limit=100):
        params = {'query': json.dumps(query), 'limit': limit}
        response = requests.get(
            f"{self.base_url}/collections/{self.name}",
            params=params,
            headers={'X-API-Key': self.api_key}
        )
        return response.json()['documents']
```

**Usage:**
```python
db = NexaDB(host='localhost', port=6969, api_key='...')
users = db.collection('users')
users.insert({'name': 'Alice', 'age': 28})
results = users.find({'age': {'$gt': 25}})
```

---

## 🚀 How to Build Your Own Database

### Step 1: Storage Engine (Week 1-2)

**Start simple:**
```python
# v1: Append-only log
class SimpleDB:
    def put(self, key, value):
        self.file.write(f"{key}:{value}\n")

    def get(self, key):
        for line in self.file:
            k, v = line.split(':')
            if k == key:
                return v
        return None
```

**Add index:**
```python
# v2: In-memory index
class IndexedDB:
    def __init__(self):
        self.index = {}  # key -> offset

    def put(self, key, value):
        offset = self.file.tell()
        self.file.write(f"{key}:{value}\n")
        self.index[key] = offset

    def get(self, key):
        offset = self.index[key]
        self.file.seek(offset)
        line = self.file.readline()
        return line.split(':')[1]
```

**Add WAL:**
```python
# v3: Write-ahead log
class DurableDB:
    def put(self, key, value):
        # Write to WAL first
        self.wal.write(f"PUT:{key}:{value}\n")
        self.wal.flush()

        # Then write to data file
        self.data.write(f"{key}:{value}\n")
```

### Step 2: LSM-Tree (Week 3-4)

Implement:
- MemTable (sorted in-memory map)
- Flushing (MemTable → SSTable)
- Compaction (merge SSTables)

### Step 3: Document Layer (Week 5-6)

Add:
- JSON serialization
- Collections
- Query operators ($gt, $lt, $in, etc.)
- Indexes

### Step 4: Server (Week 7-8)

Create:
- HTTP server (Python: http.server, Node: express)
- RESTful endpoints
- Authentication

### Step 5: Client SDKs (Week 9-10)

Build:
- Python client
- JavaScript client
- TypeScript definitions

### Step 6: Advanced Features (Week 11-16)

Add:
- Vector search
- Full-text search
- Graph support
- Replication
- Sharding

---

## 📚 Recommended Reading

1. **"Database Internals"** by Alex Petrov
   - Deep dive into LSM-trees, B-trees, storage engines

2. **"Designing Data-Intensive Applications"** by Martin Kleppmann
   - Database architectures, replication, partitioning

3. **Source Code to Study:**
   - SQLite (simple, well-documented)
   - RocksDB (production LSM-tree)
   - Redis (in-memory data structures)
   - TinyDB (Python NoSQL)

---

## 🎯 Key Takeaways

**Building a database teaches:**
1. **Data structures:** B-trees, LSM-trees, hash tables
2. **Algorithms:** Sorting, compaction, query optimization
3. **Systems design:** Persistence, crash recovery, concurrency
4. **File I/O:** Binary formats, serialization, indexes
5. **Networking:** HTTP, TCP/IP, protocols
6. **API design:** RESTful APIs, query languages

**NexaDB is production-ready but simple enough to understand every line!**

---

**Now go build your own database! 🚀**
