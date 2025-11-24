# NexaDB Client Guide

Complete guide to accessing NexaDB using different clients!

---

## 🎯 Three Ways to Use NexaDB

1. **Terminal CLI** - Interactive shell (like MongoDB shell)
2. **Web Admin UI** - Beautiful GUI (like phpMyAdmin)
3. **SDK/Code** - Python/JavaScript libraries

---

## 🖥️ Option 1: Terminal CLI (Interactive Shell)

### **Start CLI:**

```bash
cd /Users/krish/krishx/nexadb
python3 nexadb_cli.py
```

You'll see:
```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ███╗   ██╗███████╗██╗  ██╗ █████╗ ██████╗ ██████╗     ║
║   ████╗  ██║██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗██╔══██╗    ║
║   ██╔██╗ ██║█████╗   ╚███╔╝ ███████║██║  ██║██████╔╝    ║
║   ██║╚██╗██║██╔══╝   ██╔██╗ ██╔══██║██║  ██║██╔══██╗    ║
║   ██║ ╚████║███████╗██╔╝ ██╗██║  ██║██████╔╝██████╔╝    ║
║   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝     ║
║                                                           ║
║          Next-Generation Lightweight Database             ║
║                  Interactive CLI v1.0                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

✓ Connected to NexaDB v1.0.0
ℹ Server: localhost:6969

nexadb>
```

### **Basic Commands:**

```bash
# Show all collections
nexadb> show dbs

# Switch to a collection
nexadb> use users
✓ Switched to collection: users

# Insert a document
nexadb:users> db.insert({'name': 'Alice', 'age': 28, 'city': 'NYC'})
✓ Document inserted: a1b2c3d4e5f6

# Find all documents
nexadb:users> db.find({})
✓ Found 1 documents:
{
  "_id": "a1b2c3d4e5f6",
  "name": "Alice",
  "age": 28,
  "city": "NYC"
}

# Find with query
nexadb:users> db.find({'age': {'$gt': 25}})
✓ Found 1 documents:
...

# Find one document
nexadb:users> db.findOne({'name': 'Alice'})

# Update document
nexadb:users> db.update('a1b2c3d4e5f6', {'age': 29})
✓ Document updated: a1b2c3d4e5f6

# Delete document
nexadb:users> db.delete('a1b2c3d4e5f6')
✓ Document deleted: a1b2c3d4e5f6

# Count documents
nexadb:users> db.count()
✓ Total documents: 10

# Aggregation
nexadb:users> db.aggregate([{'$match': {'age': {'$gt': 25}}}, {'$group': {'_id': '$city', 'count': {'$sum': 1}}}])
✓ Aggregation results (2 documents):
[
  {"_id": "NYC", "count": 5},
  {"_id": "LA", "count": 3}
]

# Help
nexadb:users> help

# Exit
nexadb:users> exit
```

### **Advanced Usage:**

```bash
# Connect to custom server
python3 nexadb_cli.py --host myserver.com --port 6969 --api-key custom_key

# Command history (use arrow keys)
# Auto-completion (use Tab key)
```

---

## 🌐 Option 2: Web Admin UI (Beautiful GUI)

### **Step 1: Start Admin UI Server**

```bash
cd /Users/krish/krishx/nexadb
python3 nexadb_admin_server.py
```

You'll see:
```
======================================================================
NexaDB Admin UI Server Started
======================================================================
Host: 0.0.0.0
Port: 9999

🌐 Admin UI: http://localhost:9999

Make sure NexaDB server is running:
  python3 nexadb_server.py

Press Ctrl+C to stop
======================================================================
```

### **Step 2: Open Browser**

Open: **http://localhost:9999**

You'll see a beautiful purple gradient interface!

### **Features:**

#### **1. Connection Bar (Top)**
- Host: `localhost`
- Port: `6969`
- API Key: `b8c37e33faa946d43c2f6e5a0bc7e7e0`
- Click **Connect** → Status changes to "Connected to NexaDB"

#### **2. Sidebar (Left)**
- Shows all collections
- Click any collection to view documents
- Click **🔄 Refresh** to update list

#### **3. Toolbar (Top of content area)**
- **➕ Insert Document** - Add new document
- **🔍 Query** - Search with MongoDB-style queries
- **📊 Aggregate** - Run aggregation pipelines
- **📈 Stats** - View database statistics

#### **4. Document Cards**
Each document shows:
- Document ID
- Full JSON content (formatted)
- **✏️ Edit** button
- **🗑️ Delete** button

### **Workflows:**

#### **Insert Document:**
1. Click **➕ Insert Document**
2. Enter collection name: `users`
3. Enter JSON:
   ```json
   {
     "name": "Bob Smith",
     "age": 35,
     "email": "bob@example.com",
     "tags": ["developer", "python"]
   }
   ```
4. Click **Insert**
5. See success message: "Document inserted: xyz123"

#### **Query Documents:**
1. Select collection from sidebar
2. Click **🔍 Query**
3. Enter query:
   ```json
   {
     "age": {"$gt": 30},
     "tags": {"$in": ["python", "javascript"]}
   }
   ```
4. Set limit: `50`
5. Click **Execute**
6. Results appear as cards below

#### **Aggregation:**
1. Select collection
2. Click **📊 Aggregate**
3. Enter pipeline:
   ```json
   [
     {"$match": {"age": {"$gte": 30}}},
     {"$group": {
       "_id": "$city",
       "count": {"$sum": 1},
       "avg_age": {"$avg": "$age"}
     }},
     {"$sort": {"count": -1}},
     {"$limit": 10}
   ]
   ```
4. Click **Execute**
5. See aggregated results

#### **Edit Document:**
1. Click **✏️ Edit** on any document card
2. Modify JSON (only editable fields shown)
3. Click **Update**
4. Document refreshes with new data

#### **Delete Document:**
1. Click **🗑️ Delete** on document card
2. Confirm deletion
3. Document removed from list

#### **View Stats:**
1. Click **📈 Stats**
2. See:
   - Total collections
   - Total keys
   - Number of SSTables
   - MemTable size
   - Full JSON statistics

---

## 📚 Option 3: SDK/Code (Python/JavaScript)

Already covered in main README! Quick recap:

### **Python:**
```python
from nexadb_client import NexaDB

db = NexaDB(host='localhost', port=6969, api_key='your_key')
users = db.collection('users')
users.insert({'name': 'Alice', 'age': 28})
```

### **JavaScript:**
```javascript
const { NexaDB } = require('./nexadb');
const db = new NexaDB({ host: 'localhost', port: 6969, apiKey: 'your_key' });
const users = db.collection('users');
await users.insert({ name: 'Alice', age: 28 });
```

---

## 🚀 Complete Workflow Example

### **Scenario: Build a Blog Application**

#### **1. Start Servers**

**Terminal 1** (Database):
```bash
python3 nexadb_server.py
```

**Terminal 2** (Admin UI):
```bash
python3 nexadb_admin_server.py
```

#### **2. Create Collections (via CLI)**

**Terminal 3**:
```bash
python3 nexadb_cli.py
```

```bash
nexadb> use posts
nexadb:posts> db.insert({'title': 'First Post', 'content': 'Hello World', 'author': 'Alice', 'published': true, 'tags': ['intro', 'welcome']})

nexadb:posts> use users
nexadb:users> db.insert({'username': 'alice', 'email': 'alice@example.com', 'role': 'admin'})

nexadb:users> use comments
nexadb:comments> db.insert({'post_id': 'abc123', 'author': 'Bob', 'text': 'Great post!', 'timestamp': '2024-01-15T10:30:00'})
```

#### **3. View in Admin UI**

1. Open http://localhost:9999
2. See sidebar with collections: `posts`, `users`, `comments`
3. Click **posts** → See all blog posts
4. Click **➕ Insert Document** → Add more posts
5. Click **🔍 Query** → Find published posts:
   ```json
   {"published": true}
   ```

#### **4. Build Application (Python)**

```python
from nexadb_client import NexaDB

db = NexaDB(host='localhost', port=6969, api_key='your_key')

# Get all published posts
posts = db.collection('posts')
published = posts.find({'published': True})

# Display in Flask/FastAPI
for post in published:
    print(f"Title: {post['title']}")
    print(f"Author: {post['author']}")
    print(f"Content: {post['content']}")
    print()

# Get comments for a post
comments = db.collection('comments')
post_comments = comments.find({'post_id': 'abc123'})

for comment in post_comments:
    print(f"{comment['author']}: {comment['text']}")
```

---

## 🎨 UI Screenshots (What You'll See)

### **Admin UI - Main Interface:**
```
┌─────────────────────────────────────────────────────────────┐
│  🚀 NexaDB Admin Console                                   │
│  Next-Generation Database Management Interface             │
├─────────────────────────────────────────────────────────────┤
│  localhost  6969  [API Key]  [Connect]  ✓ Connected       │
├──────────────┬──────────────────────────────────────────────┤
│ Collections  │  ➕ Insert  🔍 Query  📊 Aggregate  📈 Stats│
│              │                                              │
│ 📁 users    │  ┌────────────────────────────────────────┐ │
│ 📁 posts    │  │ ID: a1b2c3d4e5f6              ✏️  🗑️  │ │
│ 📁 comments │  │ {                                      │ │
│              │  │   "name": "Alice",                     │ │
│ 🔄 Refresh  │  │   "age": 28,                           │ │
│              │  │   "email": "alice@example.com"         │ │
│              │  │ }                                      │ │
│              │  └────────────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────────────┘
```

---

## 📋 Comparison: CLI vs Web UI vs SDK

| Feature | Terminal CLI | Web Admin UI | SDK (Code) |
|---------|-------------|--------------|------------|
| **Use Case** | Quick admin tasks | Visual management | Application integration |
| **Interface** | Text-based | Graphical | Programmatic |
| **Learning Curve** | Low | Very Low | Medium |
| **Speed** | Fast | Medium | Fastest |
| **Best For** | DevOps, Scripts | Non-technical users | Developers |
| **Multi-user** | ❌ | ✅ | ✅ |
| **Remote Access** | SSH only | Any browser | Any network |

---

## 🔧 Troubleshooting

### **CLI Won't Connect:**
```bash
# Check if server is running
lsof -i :6969

# Start server if not running
python3 nexadb_server.py
```

### **Web UI Shows "Disconnected":**
1. Make sure NexaDB server is running on port 6969
2. Check API key matches
3. Open browser console (F12) to see errors
4. Try clicking **Connect** again

### **Port Already in Use:**
```bash
# Admin UI (port 9999)
lsof -i :9999
kill -9 <PID>

# Database (port 6969)
lsof -i :6969
kill -9 <PID>
```

---

## 🎉 You Now Have 3 Powerful Clients!

**Choose the right tool for the job:**

- **CLI** → Quick admin tasks, scripting, SSH access
- **Web UI** → Visual exploration, demos, non-technical users
- **SDK** → Building applications, automation, integration

---

## 📚 Next Steps

1. **Try all three clients** - Get comfortable with each
2. **Build something** - Create a real application
3. **Customize** - Modify the web UI colors, add features
4. **Share** - Show others your database!

---

**Happy Database Management! 🚀💻**
