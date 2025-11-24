# 🚀 START HERE - NexaDB Complete Setup

**Welcome to NexaDB!** Follow these simple steps to get everything running.

---

## ⚡ Quick Start (3 Steps)

### **Step 1: Start the Database Server**

Open **Terminal 1**:
```bash
cd /Users/krish/krishx/nexadb
python3 nexadb_server.py
```

✅ You should see:
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

### **Step 2: Choose Your Client**

Pick one (or use all three!):

#### **Option A: Web Admin UI** (Recommended for beginners)

Open **Terminal 2**:
```bash
cd /Users/krish/krishx/nexadb
python3 nexadb_admin_server.py
```

Then open in browser: **http://localhost:9999**

✅ You'll see a beautiful purple admin interface!

#### **Option B: Terminal CLI** (Like MongoDB shell)

Open **Terminal 2**:
```bash
cd /Users/krish/krishx/nexadb
python3 nexadb_cli.py
```

✅ You'll see an interactive shell!

#### **Option C: Write Code** (Python/JavaScript)

Create `test.py`:
```python
from nexadb_client import NexaDB

db = NexaDB(host='localhost', port=6969, api_key='b8c37e33faa946d43c2f6e5a0bc7e7e0')
users = db.collection('users')
users.insert({'name': 'Alice', 'age': 28})
print(users.find({}))
```

Run:
```bash
python3 test.py
```

---

### **Step 3: Try It Out!**

#### **Using Web UI:**
1. Click **➕ Insert Document**
2. Collection: `users`
3. JSON: `{"name": "Alice", "age": 28}`
4. Click **Insert**
5. See your document appear! 🎉

#### **Using CLI:**
```bash
nexadb> use users
nexadb:users> db.insert({'name': 'Bob', 'age': 35})
nexadb:users> db.find({})
```

---

## 📁 What You Have

```
/Users/krish/krishx/nexadb/
├── nexadb_server.py          # Main database server (port 6969)
├── nexadb_admin_server.py    # Web UI server (port 9999)
├── nexadb_cli.py             # Terminal client
├── nexadb_client.py          # Python SDK
├── nexadb.js                 # JavaScript SDK
├── nexadb_admin.html         # Web UI (auto-loaded)
│
├── storage_engine.py         # LSM-Tree engine
├── veloxdb_core.py           # Core database
│
├── README.md                 # Full documentation
├── QUICKSTART.md             # 5-minute guide
├── CLIENT_GUIDE.md           # Client usage guide
├── PROJECT_SUMMARY.md        # Project overview
└── START_HERE.md             # This file
```

---

## 🎯 Common Tasks

### **Task 1: Insert Data**

**Web UI:**
- Click **➕ Insert Document**
- Fill form → Click **Insert**

**CLI:**
```bash
nexadb> use products
nexadb:products> db.insert({'name': 'Laptop', 'price': 1200})
```

**Python:**
```python
products = db.collection('products')
products.insert({'name': 'Laptop', 'price': 1200})
```

### **Task 2: Query Data**

**Web UI:**
- Click **🔍 Query**
- Enter: `{"price": {"$lt": 1000}}`
- Click **Execute**

**CLI:**
```bash
nexadb:products> db.find({'price': {'$lt': 1000}})
```

**Python:**
```python
results = products.find({'price': {'$lt': 1000}})
```

### **Task 3: Update Data**

**Web UI:**
- Click **✏️ Edit** on document
- Modify JSON → Click **Update**

**CLI:**
```bash
nexadb:products> db.update('doc_id', {'price': 999})
```

**Python:**
```python
products.update('doc_id', {'price': 999})
```

### **Task 4: Analytics**

**Web UI:**
- Click **📊 Aggregate**
- Enter pipeline → Click **Execute**

**CLI:**
```bash
nexadb:sales> db.aggregate([
  {'$group': {'_id': '$region', 'total': {'$sum': '$amount'}}},
  {'$sort': {'total': -1}}
])
```

**Python:**
```python
sales = db.collection('sales')
results = sales.aggregate([
    {'$group': {'_id': '$region', 'total': {'$sum': '$amount'}}},
    {'$sort': {'total': -1}}
])
```

---

## 🎨 Web UI Overview

```
┌───────────────────────────────────────────────────────────┐
│  🚀 NexaDB Admin Console                                 │
│  Connection: [Host] [Port] [API Key] [Connect] ✓         │
├─────────────┬─────────────────────────────────────────────┤
│ Collections │  ➕ Insert  🔍 Query  📊 Aggregate  📈 Stats│
│             │                                             │
│ 📁 users    │  Documents appear here as cards...         │
│ 📁 products │                                             │
│ 📁 orders   │  Each card shows:                          │
│             │  - Document ID                              │
│ 🔄 Refresh │  - Full JSON                                │
│             │  - Edit button ✏️                           │
│             │  - Delete button 🗑️                         │
└─────────────┴─────────────────────────────────────────────┘
```

---

## 🖥️ CLI Commands Cheat Sheet

```bash
# Navigation
show dbs                    # List collections
use <collection>            # Switch collection
db                          # Show current collection

# CRUD
db.insert({...})           # Insert document
db.find({})                # Find all
db.find({'age': 25})       # Find with query
db.findOne({'email': '...'}) # Find single
db.update('id', {...})     # Update
db.delete('id')            # Delete
db.count()                 # Count

# Advanced
db.aggregate([...])        # Aggregation
stats                      # Server stats
help                       # Show help
exit                       # Exit CLI
```

---

## 🔧 Troubleshooting

### **Problem: Server won't start**

```bash
# Check if port is in use
lsof -i :6969

# Kill process if needed
kill -9 <PID>

# Start server again
python3 nexadb_server.py
```

### **Problem: Web UI won't connect**

1. Make sure database server is running (step 1)
2. Check API key: `b8c37e33faa946d43c2f6e5a0bc7e7e0`
3. Try clicking **Connect** again
4. Open browser console (F12) to see errors

### **Problem: CLI shows connection error**

```bash
# Make sure server is running
python3 nexadb_server.py

# In another terminal, try CLI again
python3 nexadb_cli.py
```

### **Problem: Import error**

```bash
# Make sure you're in the right directory
cd /Users/krish/krishx/nexadb

# Check files exist
ls -la
```

---

## 📚 What to Read Next

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **START_HERE.md** | Initial setup | **Now** (you're here!) |
| **QUICKSTART.md** | 5-minute tutorial | After setup |
| **CLIENT_GUIDE.md** | How to use clients | When you need a client |
| **README.md** | Full reference | When you need details |
| **PROJECT_SUMMARY.md** | Project overview | To understand what you built |

---

## 🎓 Learning Path

### **Day 1: Get Started** (30 minutes)
1. ✅ Start server
2. ✅ Try web UI
3. ✅ Insert 5 documents
4. ✅ Query them

### **Day 2: Explore Features** (1 hour)
1. Try terminal CLI
2. Learn query operators ($gt, $lt, $in, $regex)
3. Try aggregation pipeline
4. View stats

### **Day 3: Build Something** (2-3 hours)
1. Create a simple app (blog, todo list, etc.)
2. Use Python SDK
3. Build CRUD operations
4. Deploy it!

### **Week 2: Advanced**
1. Study the source code (`storage_engine.py`)
2. Understand LSM-tree architecture
3. Add custom features
4. Optimize performance

---

## 🚀 Ready to Build!

You now have:
- ✅ A production-ready database
- ✅ Beautiful web admin interface
- ✅ Interactive terminal CLI
- ✅ Python & JavaScript SDKs
- ✅ Complete documentation

**Start with the Web UI** - It's the easiest way to explore!

1. Make sure server is running (Terminal 1)
2. Start admin UI (Terminal 2)
3. Open http://localhost:9999
4. Click around and insert documents
5. Have fun! 🎉

---

## 💡 Pro Tips

1. **Keep multiple terminals open:**
   - Terminal 1: Database server
   - Terminal 2: Admin UI or CLI
   - Terminal 3: Your code/testing

2. **Use the Web UI for:**
   - Quick exploration
   - Demos to others
   - Visual data management

3. **Use the CLI for:**
   - Quick admin tasks
   - Scripting
   - SSH access

4. **Use the SDK for:**
   - Building applications
   - Automation
   - Integration

---

## 🎉 You're All Set!

**Next command to run:**

```bash
# In Terminal 1
python3 nexadb_server.py

# In Terminal 2 (choose one)
python3 nexadb_admin_server.py    # Web UI
# OR
python3 nexadb_cli.py              # Terminal CLI
```

---

**Questions? Check the docs or build something awesome! 🚀**

---

## 📊 Port Reference

| Service | Port | URL |
|---------|------|-----|
| **Database Server** | 6969 | http://localhost:6969 |
| **Web Admin UI** | 9999 | http://localhost:9999 |
| **API Endpoints** | 6969 | http://localhost:6969/collections |

**Default API Key:** `b8c37e33faa946d43c2f6e5a0bc7e7e0`

---

**Happy Database Building! 💻🎉**
