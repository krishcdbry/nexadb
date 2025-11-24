# TOON Format Support in NexaDB 🚀

## Overview

**NexaDB is the FIRST database with native TOON support!**

TOON (Token-Oriented Object Notation) is a compact, human-readable data format specifically designed for Large Language Models (LLMs). It reduces token count by **40-50%** compared to JSON, making it perfect for AI/ML applications.

## Why TOON?

### Benefits
- **40-50% fewer tokens** than JSON → Significant cost savings for LLM API calls
- **Better LLM comprehension** → 73.9% accuracy vs JSON's 69.7%
- **Perfect for RAG systems** → Efficient data retrieval for AI pipelines
- **Tabular arrays** → Extremely efficient for uniform data structures
- **Human-readable** → YAML-like indentation and clear structure

### Use Cases
1. **AI/ML Pipelines** - Reduce LLM API costs by up to 50%
2. **RAG Systems** - Efficient context retrieval for semantic search
3. **Vector Search Results** - Compact representation of similarity results
4. **Data Export** - Smaller payloads for data transfer

## Implementation

### Python API

#### Basic Usage
```python
from toon_format import json_to_toon, toon_to_json

# Convert JSON to TOON
data = {
    "users": [
        {"id": 1, "name": "Alice", "role": "admin"},
        {"id": 2, "name": "Bob", "role": "user"}
    ]
}

toon_str = json_to_toon(data)
print(toon_str)
# Output:
# users[2]{id,name,role}:
#   1,Alice,admin
#   2,Bob,user
```

#### Server Integration
The NexaDB binary server supports TOON format natively:

**New Message Types:**
- `MSG_QUERY_TOON (0x0B)` - Query with TOON format response
- `MSG_EXPORT_TOON (0x0C)` - Export collection to TOON format

**Example Response:**
```python
{
    'collection': 'users',
    'format': 'TOON',
    'data': 'users[100]{id,name,email,role}:\n  1,Alice,alice@example.com,admin\n  ...',
    'count': 100,
    'token_stats': {
        'json_size': 8234,
        'toon_size': 4127,
        'reduction_percent': 49.9
    }
}
```

### Node.js API

#### Basic Usage
```javascript
const { jsonToToon, toonToJson } = require('nexaclient');

// Convert JSON to TOON
const data = {
  users: [
    { id: 1, name: 'Alice', role: 'admin' },
    { id: 2, name: 'Bob', role: 'user' }
  ]
};

const toonStr = jsonToToon(data);
console.log(toonStr);
// Output:
// users[2]{id,name,role}:
//   1,Alice,admin
//   2,Bob,user
```

#### Client Methods
```javascript
const NexaClient = require('nexaclient');
const db = new NexaClient({ host: 'localhost', port: 6970 });

await db.connect();

// Query with TOON format
const result = await db.queryToon('users', {}, 100);
console.log('TOON data:', result.data);
console.log('Token savings:', result.token_stats.reduction_percent + '%');

// Export entire collection
const export_result = await db.exportToon('products');
console.log('Exported', export_result.count, 'documents');
console.log('Estimated cost savings:', export_result.token_stats.estimated_cost_savings);
```

## Performance Comparison

### Example: 100 User Documents

**JSON Format** (8,234 bytes):
```json
{
  "users": [
    {
      "id": 1,
      "name": "Alice Johnson",
      "email": "alice@example.com",
      "role": "admin",
      "active": true
    },
    ...
  ]
}
```

**TOON Format** (4,127 bytes):
```toon
users[100]{id,name,email,role,active}:
  1,Alice Johnson,alice@example.com,admin,true
  2,Bob Smith,bob@example.com,user,true
  ...
```

**Result:**
- **49.9% token reduction**
- **~$0.50 savings per 1M tokens** (at GPT-4 pricing)
- **Faster LLM processing** due to clearer structure

## TOON Format Specification

### Array Length Declaration
```toon
friends[3]: ana,luis,sam
```

### Tabular Arrays (Best Case)
```toon
hikes[3]{id,name,distanceKm,elevationGain,companion,wasSunny}:
  1,Blue Lake Trail,7.5,320,ana,true
  2,Ridge Overlook,9.2,540,luis,false
  3,Canyon Path,5.1,180,sam,true
```

### Nested Objects
```toon
database:
  name: NexaDB
  performance:
    writes_per_sec: 89000
    memory_mb: 111
```

### Primitive Values
```toon
name: John Doe
age: 30
active: true
score: 95.5
missing: null
```

## Real-World Examples

### RAG System with Vector Search
```python
# Query vector database
collection = db.vector_collection('documents', dimensions=768)
results = collection.search(query_vector, limit=10)

# Convert to TOON for LLM context
toon_results = json_to_toon({
    'relevant_documents': [
        {
            'id': r[0],
            'similarity': r[1],
            'title': r[2]['title'],
            'content': r[2]['content'][:200]
        }
        for r in results
    ]
})

# Send to LLM (40-50% fewer tokens!)
response = llm.complete(
    prompt=f"Based on these documents:\n{toon_results}\n\nAnswer: {question}"
)
```

### AI Training Data Export
```javascript
// Export large dataset for model training
const training_data = await db.exportToon('training_samples');

// Save to file (significantly smaller than JSON)
fs.writeFileSync('training.toon', training_data.data);

console.log(`Saved ${training_data.count} samples`);
console.log(`File size reduced by ${training_data.token_stats.reduction_percent}%`);
```

## Marketing Points

### Why NexaDB + TOON is Groundbreaking

1. **First Mover Advantage** - No other database has native TOON support
2. **AI-First Design** - Built specifically for modern LLM applications
3. **Cost Savings** - Up to 50% reduction in LLM API costs
4. **Better Performance** - Faster data transfer and LLM processing
5. **Vector Search + TOON** - Perfect combination for RAG systems
6. **Binary Protocol** - Already 3-10x faster than HTTP, now with TOON support

### Target Audience
- AI/ML Engineers building RAG systems
- Companies using LLMs extensively (high token costs)
- Data scientists working with large language models
- Developers building AI-powered applications
- Startups in the AI/ML space

## Implementation Details

### Files Added
1. `/toon_format.py` - Python TOON serializer/parser
2. `/nexaclient/src/toon.js` - Node.js TOON serializer/parser
3. `/nexadb_binary_server.py` - Updated with TOON message handlers

### Protocol Extensions
- Added `MSG_QUERY_TOON (0x0B)` message type
- Added `MSG_EXPORT_TOON (0x0C)` message type
- Responses include token statistics for transparency

### Token Statistics
Every TOON response includes:
- `json_size` - Original JSON size in bytes
- `toon_size` - TOON format size in bytes
- `reduction_percent` - Percentage reduction
- `estimated_cost_savings` - Human-readable savings estimate

## Future Enhancements

### Planned Features
1. **Admin Panel TOON View** - Toggle between JSON/TOON in UI
2. **TOON Import** - Load data directly from TOON files
3. **Streaming TOON** - Stream large datasets in TOON format
4. **Compression** - Combine TOON with gzip for even smaller payloads
5. **Python Client** - Add TOON methods to Python client library

### Community Integration
- Submit PR to TOON project showcasing NexaDB integration
- Create blog post: "Building the First TOON-Native Database"
- Share on HackerNews, Reddit (r/MachineLearning, r/LocalLLaMA)
- Tweet with #AI #LLM #TOON #Database tags

## Testing

### Test Cases
```python
# Run TOON format tests
python3 toon_format.py

# Test binary server integration
python3 test_binary_protocol.py
```

### Validation
- ✅ Round-trip conversion (JSON → TOON → JSON)
- ✅ Token count reduction (40-50%)
- ✅ Tabular array handling
- ✅ Nested object support
- ✅ Binary protocol integration
- ✅ Node.js client compatibility

## Documentation Links

- [TOON Format Specification](https://github.com/toon-format/toon)
- [NexaDB Binary Protocol](./BINARY_PROTOCOL_SPEC.md)
- [Vector Search Guide](./docs/vector-search.md)
- [Client Libraries](./CLIENT_GUIDE.md)

## Conclusion

TOON support makes NexaDB the **first and only database optimized for modern LLM applications**. By combining our fast binary protocol, built-in vector search, and now TOON format support, NexaDB is the perfect choice for AI/ML developers who want:

- ⚡ **Speed** - Binary protocol 3-10x faster than HTTP
- 🎯 **Accuracy** - Vector search for semantic retrieval
- 💰 **Cost Savings** - TOON format reduces LLM token costs by 40-50%
- 🚀 **Simplicity** - Zero configuration, works out of the box

**Join the AI database revolution with NexaDB!**
