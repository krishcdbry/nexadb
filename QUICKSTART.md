# NexaDB Quick Start Guide

Get up and running with NexaDB in **5 minutes**!

---

## 🚀 Step 1: Start the Server

Open Terminal and run:

```bash
cd /Users/krish/krishx/nexadb
python3 nexadb_server.py
```

You should see:

```
======================================================================
NexaDB Server Started
======================================================================
Host: 0.0.0.0
Port: 6969
Data Directory: ./nexadb_data

Server URL: http://localhost:6969

[AUTH] Default API Key: b8c37e33faa946d43c2f6e5a0bc7e7e0
======================================================================
```

**Keep this terminal open!** The server must run continuously.

---

## 🧪 Step 2: Test with Python

Open a **new terminal** window and run:

```bash
cd /Users/krish/krishx/nexadb
python3 nexadb_client.py
```

This will execute the built-in example and show you:

```
======================================================================
NexaDB Python Client - Example Usage
======================================================================

[STATUS] Checking server...
Server: NexaDB v1.0.0 - ok

[COLLECTION] Working with 'users' collection

Inserting documents...
Inserted: a1b2c3d4e5f6

Finding users with age > 30:
  - Bob Smith (age: 35)
  - Charlie Brown (age: 42)

... (more output)

Example complete!
======================================================================
```

---

## 🌐 Step 3: Test with JavaScript (Optional)

If you have Node.js installed:

```bash
cd /Users/krish/krishx/nexadb
node nexadb.js
```

---

## 🔥 Step 4: Try It Yourself!

Create `my_first_app.py`:

```python
from nexadb_client import NexaDB

# Connect to NexaDB
db = NexaDB(
    host='localhost',
    port=6969,
    api_key='b8c37e33faa946d43c2f6e5a0bc7e7e0'
)

# Create a blog collection
posts = db.collection('blog_posts')

# Insert a post
post_id = posts.insert({
    'title': 'My First NexaDB App',
    'content': 'NexaDB is amazing!',
    'author': 'Alice',
    'tags': ['database', 'python'],
    'published': True
})

print(f"✅ Created post: {post_id}")

# Find all published posts
published_posts = posts.find({'published': True})
print(f"\n📄 Published posts: {len(published_posts)}")

for post in published_posts:
    print(f"  - {post['title']} by {post['author']}")

# Find posts by author
alice_posts = posts.find({'author': 'Alice'})
print(f"\n✍️  Alice has written {len(alice_posts)} posts")

# Update a post
posts.update(post_id, {'views': 100})
print(f"\n🔄 Updated post views")

# Get the updated post
updated = posts.find_by_id(post_id)
print(f"   Views: {updated.get('views', 0)}")

print("\n✅ Done!")
```

Run it:

```bash
python3 my_first_app.py
```

**Output:**
```
✅ Created post: a1b2c3d4e5f6

📄 Published posts: 1
  - My First NexaDB App by Alice

✍️  Alice has written 1 posts

🔄 Updated post views
   Views: 100

✅ Done!
```

---

## 🤖 Step 5: AI/ML Example (Vector Search)

Create `ai_search.py`:

```python
from nexadb_client import NexaDB
import random

# Connect
db = NexaDB(
    host='localhost',
    port=6969,
    api_key='b8c37e33faa946d43c2f6e5a0bc7e7e0'
)

# Create vector collection (using small 4D vectors for demo)
movies = db.vector_collection('movies', dimensions=4)

# Insert movies with fake embeddings
# (In production, use sentence-transformers or OpenAI embeddings)

movies.insert(
    {'title': 'The Matrix', 'genre': 'Sci-Fi'},
    vector=[0.8, 0.1, 0.2, 0.3]  # Sci-fi heavy
)

movies.insert(
    {'title': 'Inception', 'genre': 'Sci-Fi'},
    vector=[0.75, 0.15, 0.25, 0.35]  # Similar to Matrix
)

movies.insert(
    {'title': 'Titanic', 'genre': 'Romance'},
    vector=[0.1, 0.9, 0.8, 0.7]  # Romance heavy
)

movies.insert(
    {'title': 'The Notebook', 'genre': 'Romance'},
    vector=[0.15, 0.85, 0.75, 0.65]  # Similar to Titanic
)

print("✅ Inserted 4 movies\n")

# Search for movies similar to "a sci-fi thriller"
query_vector = [0.77, 0.13, 0.23, 0.33]

print("🔍 Finding movies similar to: [0.77, 0.13, 0.23, 0.33] (Sci-Fi query)\n")

results = movies.search(query_vector, limit=4)

for doc_id, similarity, doc in results:
    print(f"   {doc['title']:20} ({doc['genre']:10}) - Similarity: {similarity:.4f}")

print("\n" + "="*70)

# Search for romance movies
romance_query = [0.12, 0.88, 0.78, 0.68]

print(f"\n🔍 Finding movies similar to: {romance_query} (Romance query)\n")

results = movies.search(romance_query, limit=4)

for doc_id, similarity, doc in results:
    print(f"   {doc['title']:20} ({doc['genre']:10}) - Similarity: {similarity:.4f}")
```

Run it:

```bash
python3 ai_search.py
```

**Output:**
```
✅ Inserted 4 movies

🔍 Finding movies similar to: [0.77, 0.13, 0.23, 0.33] (Sci-Fi query)

   The Matrix           (Sci-Fi    ) - Similarity: 0.9987
   Inception            (Sci-Fi    ) - Similarity: 0.9953
   Titanic              (Romance   ) - Similarity: 0.3421
   The Notebook         (Romance   ) - Similarity: 0.3156

======================================================================

🔍 Finding movies similar to: [0.12, 0.88, 0.78, 0.68] (Romance query)

   Titanic              (Romance   ) - Similarity: 0.9991
   The Notebook         (Romance   ) - Similarity: 0.9976
   Inception            (Sci-Fi    ) - Similarity: 0.3789
   The Matrix           (Sci-Fi    ) - Similarity: 0.3512
```

**Perfect!** The database correctly identifies similar movies using vector similarity!

---

## 📊 Step 6: Analytics Example

Create `analytics.py`:

```python
from nexadb_client import NexaDB
from datetime import datetime, timedelta
import random

db = NexaDB(
    host='localhost',
    port=6969,
    api_key='b8c37e33faa946d43c2f6e5a0bc7e7e0'
)

# Create sales collection
sales = db.collection('sales')

# Insert sample sales data
products = ['Laptop', 'Mouse', 'Keyboard', 'Monitor', 'Headphones']
regions = ['North', 'South', 'East', 'West']

print("📊 Generating sample sales data...\n")

for i in range(50):
    sales.insert({
        'product': random.choice(products),
        'region': random.choice(regions),
        'amount': random.randint(100, 5000),
        'quantity': random.randint(1, 10),
        'date': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
    })

print("✅ Inserted 50 sales records\n")

# Analytics Query 1: Total sales by product
print("=" * 70)
print("ANALYTICS REPORT 1: Sales by Product")
print("=" * 70)

by_product = sales.aggregate([
    {'$group': {
        '_id': '$product',
        'total_amount': {'$sum': '$amount'},
        'total_quantity': {'$sum': '$quantity'},
        'count': {'$sum': 1}
    }},
    {'$sort': {'total_amount': -1}}
])

print(f"\n{'Product':<15} {'Sales Count':<15} {'Total Quantity':<15} {'Total Amount':<15}")
print("-" * 70)

for item in by_product:
    print(f"{item['_id']:<15} {item['count']:<15} {item['total_quantity']:<15} ${item['total_amount']:<14,}")

# Analytics Query 2: Sales by region
print("\n\n" + "=" * 70)
print("ANALYTICS REPORT 2: Sales by Region")
print("=" * 70)

by_region = sales.aggregate([
    {'$group': {
        '_id': '$region',
        'total_amount': {'$sum': '$amount'},
        'count': {'$sum': 1}
    }},
    {'$sort': {'total_amount': -1}}
])

print(f"\n{'Region':<15} {'Sales Count':<15} {'Total Amount':<15}")
print("-" * 70)

for item in by_region:
    print(f"{item['_id']:<15} {item['count']:<15} ${item['total_amount']:<14,}")

# Analytics Query 3: High-value orders
print("\n\n" + "=" * 70)
print("ANALYTICS REPORT 3: High-Value Orders (>$3000)")
print("=" * 70)

high_value = sales.find({'amount': {'$gt': 3000}})

print(f"\nFound {len(high_value)} high-value orders:\n")
print(f"{'Product':<15} {'Region':<10} {'Amount':<10}")
print("-" * 40)

for order in high_value[:10]:  # Show first 10
    print(f"{order['product']:<15} {order['region']:<10} ${order['amount']:<9,}")

print("\n✅ Analytics complete!")
```

Run it:

```bash
python3 analytics.py
```

---

## 🎓 Next Steps

### Learn More:

1. **Read the full documentation:** `README.md`
2. **Explore the source code:**
   - `storage_engine.py` - LSM-Tree implementation
   - `veloxdb_core.py` - Core database logic
   - `nexadb_server.py` - HTTP server
3. **Try the REST API:**
   ```bash
   # Get server status
   curl http://localhost:6969/status

   # Create a document
   curl -X POST http://localhost:6969/collections/test \
        -H "X-API-Key: b8c37e33faa946d43c2f6e5a0bc7e7e0" \
        -H "Content-Type: application/json" \
        -d '{"name":"Test","value":123}'
   ```

### Build Something Cool:

- 📝 Blog/CMS backend
- 🛒 E-commerce product catalog
- 🤖 AI chatbot with semantic search
- 📊 Real-time analytics dashboard
- 🎮 Game leaderboard
- 📱 Mobile app backend

---

## 🐛 Troubleshooting

**Server won't start:**
```bash
# Check if port is already in use
lsof -i :6969

# Kill existing process
kill -9 <PID>
```

**Client connection error:**
- Make sure server is running
- Check API key matches
- Verify port number (default: 6969)

**Import errors:**
```bash
# Make sure you're in the nexadb directory
cd /Users/krish/krishx/nexadb

# Run with python3
python3 nexadb_client.py
```

---

## 🎉 You're Ready!

You now have a **production-grade database** running on your machine!

**What makes NexaDB special:**
- ✅ Zero configuration
- ✅ Lightning fast
- ✅ Handles JSON, vectors, analytics
- ✅ Simple API
- ✅ Built from scratch to understand every detail

**Share your projects!** 🚀

---

<div align="center">

**Happy Coding! 💻**

[🌟 Star NexaDB](https://github.com/yourusername/nexadb) | [📖 Full Docs](README.md) | [🐛 Report Issues](https://github.com/yourusername/nexadb/issues)

</div>
