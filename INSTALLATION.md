# NexaDB Installation Guide

Complete guide for installing and running NexaDB on your local machine or in the cloud.

---

## 📥 Installation Options

Choose your preferred method:

1. [Download & Run (No Installation)](#method-1-download--run-no-installation) - **Recommended**
2. [Install via pip (Python Package)](#method-2-install-via-pip-python-package)
3. [Clone from GitHub](#method-3-clone-from-github)
4. [Docker](#method-4-docker)
5. [Cloud Deployment](#cloud-deployment)

---

## Method 1: Download & Run (No Installation)

**Perfect for:** Quick testing, development, portability

### Step 1: Download NexaDB

```bash
# Create a directory
mkdir nexadb
cd nexadb

# Download the files (choose one):

# Option A: Using curl
curl -O https://raw.githubusercontent.com/yourusername/nexadb/main/nexadb_server.py
curl -O https://raw.githubusercontent.com/yourusername/nexadb/main/veloxdb_core.py
curl -O https://raw.githubusercontent.com/yourusername/nexadb/main/storage_engine.py
curl -O https://raw.githubusercontent.com/yourusername/nexadb/main/nexadb_admin_professional.html
curl -O https://raw.githubusercontent.com/yourusername/nexadb/main/nexadb_admin_server.py

# Option B: Using wget
wget https://raw.githubusercontent.com/yourusername/nexadb/main/nexadb_server.py
wget https://raw.githubusercontent.com/yourusername/nexadb/main/veloxdb_core.py
wget https://raw.githubusercontent.com/yourusername/nexadb/main/storage_engine.py
wget https://raw.githubusercontent.com/yourusername/nexadb/main/nexadb_admin_professional.html
wget https://raw.githubusercontent.com/yourusername/nexadb/main/nexadb_admin_server.py
```

### Step 2: Requirements

**Python 3.8 or higher** - That's it! No other dependencies.

```bash
# Check Python version
python3 --version
# Should show: Python 3.8.0 or higher
```

### Step 3: Run NexaDB

```bash
# Terminal 1: Start the database server
python3 nexadb_server.py

# Terminal 2: Start the admin UI (optional)
python3 nexadb_admin_server.py
```

**Access:**
- Database API: http://localhost:6969
- Admin UI: http://localhost:9999

### Step 4: Test It

```python
# test_connection.py
from nexadb_client import NexaDB

db = NexaDB(host='localhost', port=6969, api_key='b8c37e33faa946d43c2f6e5a0bc7e7e0')
users = db.collection('users')
users.insert({'name': 'Alice', 'email': 'alice@example.com'})
print(users.find({}))
```

```bash
python3 test_connection.py
```

---

## Method 2: Install via pip (Python Package)

**Perfect for:** Python projects, easy updates

### Step 1: Install

```bash
pip install nexadb
```

### Step 2: Run

```bash
# Start server
nexadb-server

# Start admin UI (in another terminal)
nexadb-admin
```

### Step 3: Use in Your Project

```python
from nexadb import NexaDB

db = NexaDB()
users = db.collection('users')
users.insert({'name': 'Bob', 'age': 30})
```

---

## Method 3: Clone from GitHub

**Perfect for:** Development, contributing, customization

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/nexadb.git
cd nexadb
```

### Step 2: Run

```bash
# No installation needed!
python3 nexadb_server.py

# In another terminal
python3 nexadb_admin_server.py
```

### Step 3: Stay Updated

```bash
git pull origin main
```

---

## Method 4: Docker

**Perfect for:** Containerization, production, microservices

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  nexadb:
    image: nexadb/nexadb:latest
    ports:
      - "6969:6969"
      - "9999:9999"
    volumes:
      - nexadb_data:/app/nexadb_data
    environment:
      - NEXADB_HOST=0.0.0.0
      - NEXADB_PORT=6969
      - ADMIN_PORT=9999
    restart: unless-stopped

volumes:
  nexadb_data:
```

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f
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

# Check logs
docker logs -f nexadb

# Stop
docker stop nexadb
```

### Build Your Own Image

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy NexaDB files
COPY nexadb_server.py .
COPY veloxdb_core.py .
COPY storage_engine.py .
COPY nexadb_admin_professional.html .
COPY nexadb_admin_server.py .

# Create data directory
RUN mkdir -p /app/nexadb_data

# Expose ports
EXPOSE 6969 9999

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:6969/status')"

# Start both servers
CMD python3 nexadb_server.py & python3 nexadb_admin_server.py
```

```bash
# Build
docker build -t my-nexadb .

# Run
docker run -d -p 6969:6969 -p 9999:9999 my-nexadb
```

---

## Cloud Deployment

Deploy NexaDB to popular cloud platforms:

### [Vercel](DEPLOY_VERCEL.md)
### [Railway](DEPLOY_RAILWAY.md)
### [Render](DEPLOY_RENDER.md)
### [Heroku](DEPLOY_HEROKU.md)
### [DigitalOcean](DEPLOY_DIGITALOCEAN.md)
### [AWS](DEPLOY_AWS.md)
### [Google Cloud](DEPLOY_GCP.md)

---

## 🔧 Configuration

### Environment Variables

```bash
# Server settings
export NEXADB_HOST=0.0.0.0
export NEXADB_PORT=6969
export NEXADB_DATA_DIR=./nexadb_data

# Admin UI settings
export ADMIN_HOST=0.0.0.0
export ADMIN_PORT=9999

# Security
export NEXADB_API_KEY=your-custom-api-key
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=your-secure-password
```

### Configuration File

Create `nexadb.config.json`:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 6969,
    "data_dir": "./nexadb_data"
  },
  "admin": {
    "host": "0.0.0.0",
    "port": 9999,
    "enabled": true
  },
  "security": {
    "api_key": "your-custom-key",
    "require_auth": true
  },
  "storage": {
    "memtable_size_mb": 10,
    "compaction_interval_seconds": 10
  },
  "logging": {
    "level": "INFO",
    "file": "./nexadb.log"
  }
}
```

---

## 🔐 Security Setup

### Generate API Key

```bash
# Generate secure API key
python3 -c "import hashlib, secrets; print(hashlib.sha256(secrets.token_bytes(32)).hexdigest()[:32])"
```

### Enable Authentication

```python
# nexadb_server.py
server = NexaDBServer(
    host='0.0.0.0',
    port=6969,
    require_auth=True,
    api_keys={
        'your-api-key-here': 'admin',
        'client-key-123': 'client1'
    }
)
```

### SSL/TLS (HTTPS)

```python
# For production, use a reverse proxy (nginx/caddy)
# Or run with SSL:

import ssl
from http.server import HTTPServer

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('cert.pem', 'key.pem')

httpd = HTTPServer(('0.0.0.0', 6969), NexaDBHandler)
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
```

---

## 📦 System Requirements

### Minimum Requirements

- **OS:** Linux, macOS, Windows
- **Python:** 3.8 or higher
- **RAM:** 256 MB
- **Storage:** 100 MB (+ data)
- **CPU:** 1 core

### Recommended Requirements

- **OS:** Linux (Ubuntu 20.04+) or macOS
- **Python:** 3.10 or higher
- **RAM:** 2 GB
- **Storage:** 10 GB SSD
- **CPU:** 2+ cores

### For Production

- **RAM:** 4-16 GB
- **Storage:** 50+ GB SSD
- **CPU:** 4+ cores
- **Network:** 100+ Mbps
- **Backup:** Daily automated backups

---

## 🚀 Performance Tuning

### MemTable Size

Larger MemTable = fewer disk writes, more memory usage:

```python
# storage_engine.py
db = LSMStorageEngine(
    data_dir='./data',
    memtable_size=1024*1024*50  # 50 MB (default: 1 MB)
)
```

### Compaction Interval

```python
# Adjust in storage_engine.py
def _start_compaction_thread(self):
    def compaction_loop():
        while self.running:
            time.sleep(5)  # 5 seconds (default: 10)
            if len(self.sstables) >= 3:
                self._compact()
```

### File Descriptors (Linux)

```bash
# Increase file descriptor limit
ulimit -n 65536

# Make permanent in /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536
```

---

## 🔄 Backup & Restore

### Manual Backup

```bash
# Stop server first
# Then backup data directory
tar -czf nexadb_backup_$(date +%Y%m%d).tar.gz nexadb_data/
```

### Automated Backup (Cron)

```bash
# Add to crontab
0 2 * * * cd /path/to/nexadb && tar -czf backup_$(date +\%Y\%m\%d).tar.gz nexadb_data/
```

### Restore

```bash
# Stop server
# Extract backup
tar -xzf nexadb_backup_20241124.tar.gz
# Start server
python3 nexadb_server.py
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :6969
# Kill it
kill -9 <PID>

# Or use different port
python3 nexadb_server.py --port 6970
```

### Permission Denied

```bash
# Make scripts executable
chmod +x nexadb_server.py
chmod +x nexadb_admin_server.py

# Or run with python3
python3 nexadb_server.py
```

### Data Corruption

```bash
# NexaDB has automatic crash recovery
# Just restart the server
python3 nexadb_server.py
# WAL will be replayed automatically
```

### Out of Memory

```bash
# Reduce MemTable size
# Edit storage_engine.py
memtable_size=1024*1024  # 1 MB instead of 10 MB

# Or increase system RAM
# Or use swap space
```

---

## 📊 Monitoring

### Health Check Endpoint

```bash
curl http://localhost:6969/status

# Response:
{
  "status": "ok",
  "version": "1.0.0",
  "database": "NexaDB"
}
```

### Stats Endpoint

```bash
curl http://localhost:6969/stats

# Response:
{
  "memtable_size": 1024000,
  "num_sstables": 3,
  "total_keys": 15000,
  "data_dir": "./nexadb_data"
}
```

### Log Files

```bash
# Server logs
tail -f nexadb.log

# Filter errors only
grep ERROR nexadb.log
```

---

## 🔄 Upgrade Guide

### Upgrade Steps

```bash
# 1. Backup data
tar -czf backup.tar.gz nexadb_data/

# 2. Stop server
kill $(lsof -t -i:6969)

# 3. Download new version
curl -O https://raw.githubusercontent.com/yourusername/nexadb/main/nexadb_server.py

# 4. Start new version
python3 nexadb_server.py
```

### Rolling Updates (Zero Downtime)

```bash
# 1. Start new instance on different port
python3 nexadb_server.py --port 6970

# 2. Update load balancer/proxy
# Point traffic to port 6970

# 3. Stop old instance (port 6969)
# 4. Data sync (if needed)
```

---

## 📱 Client SDKs

### Python

```bash
pip install nexadb-client
```

```python
from nexadb import NexaDB
db = NexaDB(host='localhost', port=6969)
```

### JavaScript/Node.js

```bash
npm install nexadb-client
```

```javascript
const { NexaDB } = require('nexadb-client');
const db = new NexaDB({ host: 'localhost', port: 6969 });
```

### curl (REST API)

```bash
# Insert
curl -X POST http://localhost:6969/collections/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","age":28}'

# Query
curl http://localhost:6969/collections/users?query={}

# Delete
curl -X DELETE http://localhost:6969/collections/users/doc-id
```

---

## 🎯 Next Steps

1. ✅ **Installed NexaDB**
2. 📚 Read [Quick Start Guide](QUICKSTART.md)
3. 🎨 Open Admin UI: http://localhost:9999
4. 💻 Try the [Python Client](CLIENT_GUIDE.md)
5. 🚀 Deploy to [Cloud](DEPLOY_VERCEL.md)
6. 📖 Read [Full Documentation](README.md)

---

## 💬 Support

- **Issues:** GitHub Issues
- **Docs:** [README.md](README.md)
- **Discord:** Join our community
- **Email:** support@nexadb.io

---

**You're all set! Start building with NexaDB.**

*Installation Guide v1.0*
