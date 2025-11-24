# Get Started with NexaDB

Choose how you want to install and use NexaDB - we support multiple methods!

---

## 🚀 Choose Your Installation Method

| Method | Best For | Time | Difficulty |
|--------|----------|------|-----------|
| [Download & Run](#1-download--run) | Quick testing | 1 min | Easy |
| [npm/npx](#2-npm--npx) | Node.js developers | 1 min | Easy |
| [pip](#3-pip-python) | Python developers | 2 min | Easy |
| [Docker](#4-docker) | Containers, production | 2 min | Easy |
| [Cloud Deploy](#5-cloud-platforms) | Hosting online | 5 min | Medium |

---

## 1. Download & Run

**Perfect for:** Testing, learning, quick demos

**Requirements:** Python 3.8+

```bash
# Create directory
mkdir nexadb && cd nexadb

# Download files
curl -O https://raw.githubusercontent.com/yourusername/nexadb/main/nexadb_server.py
curl -O https://raw.githubusercontent.com/yourusername/nexadb/main/veloxdb_core.py
curl -O https://raw.githubusercontent.com/yourusername/nexadb/main/storage_engine.py
curl -O https://raw.githubusercontent.com/yourusername/nexadb/main/nexadb_admin_server.py
curl -O https://raw.githubusercontent.com/yourusername/nexadb/main/nexadb_admin_professional.html

# Start server
python3 nexadb_server.py
```

**Access:** http://localhost:6969

📚 **Full Guide:** [INSTALLATION.md](INSTALLATION.md)

---

## 2. npm / npx

**Perfect for:** Node.js projects, JavaScript developers

**Requirements:** Node.js 14+, Python 3.8+

### Using npx (No Installation)

```bash
# Start server
npx nexadb-server

# Start admin UI (new terminal)
npx nexadb-admin
```

### Global Installation

```bash
# Install globally
npm install -g nexadb

# Use anywhere
nexadb-server
nexadb-admin
```

### In Your Project

```bash
# Install in project
npm install nexadb

# Add to package.json
{
  "scripts": {
    "db:start": "nexadb-server",
    "db:admin": "nexadb-admin"
  }
}

# Run
npm run db:start
```

**Access:** http://localhost:9999

📚 **Full Guide:** [INSTALL_NPM.md](INSTALL_NPM.md)

---

## 3. pip (Python)

**Perfect for:** Python projects, Django, Flask apps

**Requirements:** Python 3.8+

```bash
# Install via pip
pip install nexadb

# Start server
nexadb-server

# Start admin UI
nexadb-admin
```

### In Python Code

```python
from nexadb import NexaDB

# Connect
db = NexaDB(host='localhost', port=6969)

# Use collections
users = db.collection('users')
users.insert({'name': 'Alice', 'age': 28})

# Query
results = users.find({'age': {'$gt': 25}})
```

**Access:** http://localhost:6969

📚 **Full Guide:** [INSTALLATION.md](INSTALLATION.md)

---

## 4. Docker

**Perfect for:** Containers, production, microservices

**Requirements:** Docker 20+

### Using Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  nexadb:
    image: nexadb/nexadb:latest
    ports:
      - "6969:6969"
      - "9999:9999"
    volumes:
      - nexadb_data:/app/nexadb_data
    restart: unless-stopped

volumes:
  nexadb_data:
```

```bash
# Start
docker-compose up -d

# Stop
docker-compose down
```

### Using Docker CLI

```bash
# Pull image
docker pull nexadb/nexadb:latest

# Run
docker run -d \
  --name nexadb \
  -p 6969:6969 \
  -p 9999:9999 \
  -v nexadb_data:/app/nexadb_data \
  nexadb/nexadb:latest

# View logs
docker logs -f nexadb
```

**Access:** http://localhost:9999

📚 **Full Guide:** [DEPLOY_DOCKER.md](DEPLOY_DOCKER.md)

---

## 5. Cloud Platforms

**Perfect for:** Production hosting, scalability

### Vercel (Serverless)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Production
vercel --prod
```

📚 **Guide:** [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md)

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

📚 **Guide:** [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md)

### Render

```yaml
# render.yaml
services:
  - type: web
    name: nexadb
    env: python
    startCommand: python3 nexadb_server.py
    disk:
      name: nexadb-data
      mountPath: /data
      sizeGB: 10
```

Push to GitHub, connect to Render, deploy!

📚 **Guide:** [DEPLOY_RENDER.md](DEPLOY_RENDER.md)

### Other Platforms

- **Heroku:** [DEPLOY_HEROKU.md](DEPLOY_HEROKU.md)
- **DigitalOcean:** [DEPLOY_DIGITALOCEAN.md](DEPLOY_DIGITALOCEAN.md)
- **AWS:** [DEPLOY_AWS.md](DEPLOY_AWS.md)
- **Google Cloud:** [DEPLOY_GCP.md](DEPLOY_GCP.md)

---

## 🎯 What's Included

### Core Components

| Component | Description | Port |
|-----------|-------------|------|
| **NexaDB Server** | Database server with REST API | 6969 |
| **Admin UI** | Professional web interface | 9999 |
| **Python Client** | Official Python SDK | - |
| **Storage Engine** | LSM-Tree with WAL | - |

### Features

✅ **Zero Dependencies** - Pure Python standard library
✅ **Professional UI** - True black theme, vector icons
✅ **REST API** - Full HTTP/JSON API
✅ **Vector Search** - AI/ML embeddings support
✅ **Aggregation** - MongoDB-style pipelines
✅ **ACID Guarantees** - Write-ahead logging
✅ **Auto Compaction** - Background optimization
✅ **Crash Recovery** - WAL replay on restart

---

## 📊 Quick Comparison

| Method | Pros | Cons |
|--------|------|------|
| **Download** | ✅ Fastest<br>✅ No install<br>✅ Portable | ❌ Manual updates<br>❌ No auto-restart |
| **npm** | ✅ Auto-updates<br>✅ CLI tools<br>✅ PM2 support | ❌ Needs Node.js<br>❌ Two dependencies |
| **pip** | ✅ Python native<br>✅ Auto-updates<br>✅ Easy imports | ❌ Virtual env recommended |
| **Docker** | ✅ Isolated<br>✅ Reproducible<br>✅ Production-ready | ❌ Larger size<br>❌ Needs Docker |
| **Cloud** | ✅ Managed<br>✅ Scalable<br>✅ Auto-SSL | ❌ Costs money<br>❌ Platform-specific |

---

## 🎨 Professional Admin UI

Once installed, access the ultra-professional admin UI:

### Features

- **True Black Theme** - Pure #000000 for OLED displays
- **Vector Icons** - Professional SVG icons, no emojis
- **Theme Switching** - Dark (default) and light modes
- **Real-time Stats** - Live database metrics
- **Collection Management** - Create, read, update, delete
- **Query Builder** - Visual query constructor
- **Vector Search UI** - AI/ML similarity search
- **Code Syntax Highlighting** - Professional color schemes

### Screenshots

**Dark Theme (Default):**
- Pure black background (#000000)
- High contrast text (#ffffff)
- Blue accents (#3b82f6)
- Smooth animations

**Light Theme:**
- Clean white background (#ffffff)
- Subtle grays (#f9fafb)
- Same blue accents
- Perfect readability

📚 **Design Guide:** [PROFESSIONAL_DESIGN_SYSTEM.md](PROFESSIONAL_DESIGN_SYSTEM.md)

---

## 📖 Next Steps

### 1. Choose Installation Method
Pick from the options above based on your needs.

### 2. Start the Server
Follow the specific guide for your chosen method.

### 3. Open Admin UI
Visit http://localhost:9999 to see the professional interface.

### 4. Create Your First Collection
```python
from nexadb import NexaDB

db = NexaDB()
users = db.collection('users')
users.insert({'name': 'Your Name', 'email': 'you@example.com'})
```

### 5. Explore Features
- Try vector search for AI/ML
- Use aggregation pipelines
- Build real-time apps
- Scale to production

---

## 💡 Common Use Cases

### 1. Web Application Backend

```javascript
// Express.js + NexaDB
const axios = require('axios');

app.post('/api/users', async (req, res) => {
  const response = await axios.post(
    'http://localhost:6969/collections/users',
    req.body,
    { headers: { 'X-API-Key': API_KEY } }
  );
  res.json(response.data);
});
```

### 2. AI/ML Vector Search

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
products = db.vector_collection('products', dimensions=384)

# Insert with embeddings
products.insert(
    {'name': 'Laptop', 'price': 1200},
    vector=model.encode('laptop computer')
)

# Search
results = products.search(
    model.encode('portable workstation'),
    limit=10
)
```

### 3. Real-time Analytics

```python
# Aggregation pipeline
users.aggregate([
    {'$match': {'signup_date': {'$gte': '2024-01-01'}}},
    {'$group': {'_id': '$country', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
])
```

### 4. Document Storage

```python
# Store documents
docs = db.collection('documents')
docs.insert({
    'title': 'Meeting Notes',
    'content': 'Discussed Q4 goals...',
    'tags': ['meeting', 'planning'],
    'created_at': '2024-11-24'
})
```

---

## 🔗 All Documentation

| Guide | Description |
|-------|-------------|
| [README.md](README.md) | Project overview |
| [INSTALLATION.md](INSTALLATION.md) | Local installation |
| [INSTALL_NPM.md](INSTALL_NPM.md) | npm installation |
| [DEPLOY_DOCKER.md](DEPLOY_DOCKER.md) | Docker deployment |
| [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md) | Vercel serverless |
| [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md) | Railway hosting |
| [DEPLOY_RENDER.md](DEPLOY_RENDER.md) | Render deployment |
| [PROFESSIONAL_DESIGN_SYSTEM.md](PROFESSIONAL_DESIGN_SYSTEM.md) | UI design specs |
| [LAUNCH_PROFESSIONAL_UI.md](LAUNCH_PROFESSIONAL_UI.md) | UI quick start |

---

## ❓ Need Help?

- **GitHub Issues:** Report bugs or request features
- **Documentation:** Read the guides above
- **Examples:** Check `nexadb_client.py` for Python examples
- **Community:** Join our Discord/forum

---

## 🎯 Quick Decision Guide

**I want to...**

- ✅ **Try NexaDB now** → Download & Run
- ✅ **Use in Node.js project** → npm install
- ✅ **Use in Python project** → pip install
- ✅ **Deploy to production** → Docker or Cloud
- ✅ **Host on Vercel** → Deploy to Vercel
- ✅ **Use with containers** → Docker Compose
- ✅ **Test locally quickly** → npx nexadb-server

---

**Choose your path and get started in under 2 minutes!**

*Get Started Guide v1.0*
