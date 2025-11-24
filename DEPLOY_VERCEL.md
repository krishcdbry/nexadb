# Deploy NexaDB to Vercel

Complete guide for deploying NexaDB to Vercel serverless platform.

---

## 🚀 Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/nexadb)

---

## 📋 Prerequisites

- Vercel account (free tier available)
- GitHub account
- Git installed locally

---

## Method 1: Deploy via Vercel Dashboard (Easiest)

### Step 1: Prepare Your Repository

```bash
cd /Users/krish/krishx/nexadb

# Initialize git (if not already)
git init
git add .
git commit -m "Initial NexaDB setup"

# Create GitHub repo and push
git remote add origin https://github.com/yourusername/nexadb.git
git push -u origin main
```

### Step 2: Create `vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/server.py",
      "use": "@vercel/python"
    },
    {
      "src": "nexadb_admin_professional.html",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/",
      "dest": "/nexadb_admin_professional.html"
    },
    {
      "src": "/api/(.*)",
      "dest": "/api/server.py"
    },
    {
      "src": "/status",
      "dest": "/api/server.py"
    },
    {
      "src": "/collections/(.*)",
      "dest": "/api/server.py"
    }
  ],
  "env": {
    "NEXADB_API_KEY": "@nexadb-api-key"
  }
}
```

### Step 3: Create API Handler

Create `api/server.py`:

```python
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from nexadb_server import NexaDBHandler, NexaDBServer

class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""

    # Initialize NexaDB (shared across requests)
    if not hasattr(handler, '_nexadb_initialized'):
        server = NexaDBServer(data_dir='/tmp/nexadb_data')
        NexaDBHandler.db = server.db
        NexaDBHandler.api_keys = server.api_keys
        handler._nexadb_initialized = True

    def do_GET(self):
        # Delegate to NexaDB handler
        nexadb_handler = NexaDBHandler(self.request, self.client_address, self.server)
        nexadb_handler.path = self.path
        nexadb_handler.headers = self.headers
        nexadb_handler.do_GET()

        # Copy response
        self.send_response(nexadb_handler.status_code)
        for key, value in nexadb_handler.headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(nexadb_handler.response_body)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        nexadb_handler = NexaDBHandler(self.request, self.client_address, self.server)
        nexadb_handler.path = self.path
        nexadb_handler.headers = self.headers
        nexadb_handler.rfile = io.BytesIO(body)
        nexadb_handler.do_POST()

        self.send_response(nexadb_handler.status_code)
        for key, value in nexadb_handler.headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(nexadb_handler.response_body)
```

### Step 4: Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Production deployment
vercel --prod
```

**Or use Vercel Dashboard:**

1. Go to https://vercel.com/dashboard
2. Click "New Project"
3. Import your GitHub repository
4. Click "Deploy"

### Step 5: Configure Environment Variables

In Vercel Dashboard:

1. Go to Project → Settings → Environment Variables
2. Add:
   - `NEXADB_API_KEY` = your-secure-api-key
   - `NEXADB_DATA_DIR` = /tmp/nexadb_data

### Step 6: Access Your Deployment

```
https://your-project.vercel.app
```

---

## Method 2: Deploy via Vercel CLI

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Prepare Project

```bash
cd nexadb

# Create vercel.json (see above)

# Create requirements.txt
echo "# NexaDB has no dependencies" > requirements.txt
```

### Step 3: Deploy

```bash
# Development deployment
vercel

# Production deployment
vercel --prod

# With environment variables
vercel --prod \
  -e NEXADB_API_KEY=your-key \
  -e NEXADB_DATA_DIR=/tmp/nexadb_data
```

---

## ⚙️ Configuration

### Custom Domain

```bash
# Add custom domain
vercel domains add yourdomain.com

# Point domain
vercel alias set your-project.vercel.app yourdomain.com
```

### Environment Variables

```bash
# Add env variable
vercel env add NEXADB_API_KEY production

# List env variables
vercel env ls

# Remove env variable
vercel env rm NEXADB_API_KEY
```

### Serverless Function Config

Create `api/server.py` with config:

```python
# api/server.py
# Serverless function configuration
config = {
    "maxDuration": 60,  # Max execution time (seconds)
    "memory": 1024,     # Memory allocation (MB)
    "runtime": "python3.9"
}
```

---

## 🔒 Security

### API Key Setup

```bash
# Generate secure key
openssl rand -hex 16

# Add to Vercel
vercel env add NEXADB_API_KEY production
# Paste your key
```

### CORS Configuration

Update `api/server.py`:

```python
def send_cors_headers(self):
    self.send_header('Access-Control-Allow-Origin', 'https://yourdomain.com')
    self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
```

---

## 📊 Monitoring

### Vercel Analytics

```bash
# Enable analytics in vercel.json
{
  "analytics": {
    "enable": true
  }
}
```

### Logs

```bash
# View logs
vercel logs

# Follow logs
vercel logs --follow

# Filter by function
vercel logs api/server.py
```

---

## 💾 Data Persistence

**Important:** Vercel serverless functions use `/tmp` directory which is ephemeral.

### Solutions:

**1. Use External Database (Recommended)**

```python
# Use MongoDB, PostgreSQL, or Redis
# for persistent storage backend
```

**2. Use Vercel KV (Redis)**

```bash
# Install Vercel KV
vercel kv create nexadb-storage

# Use in code
from vercel_kv import KV
kv = KV()
```

**3. Use Cloudflare R2 / AWS S3**

```python
import boto3
s3 = boto3.client('s3')
# Store SSTables in S3
```

---

## 🚀 Performance Optimization

### Edge Functions

```json
{
  "functions": {
    "api/server.py": {
      "runtime": "edge",
      "regions": ["iad1", "sfo1"]
    }
  }
}
```

### Caching

```json
{
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "s-maxage=60, stale-while-revalidate"
        }
      ]
    }
  ]
}
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

---

## 🐛 Troubleshooting

### Function Timeout

```json
{
  "functions": {
    "api/**/*.py": {
      "maxDuration": 60
    }
  }
}
```

### Memory Limit

```json
{
  "functions": {
    "api/**/*.py": {
      "memory": 3008
    }
  }
}
```

### Cold Start Issues

```python
# Implement warmup endpoint
@app.route('/warmup')
def warmup():
    # Preload database
    return {'status': 'warm'}
```

---

## 📦 Complete Example

### File Structure

```
nexadb/
├── api/
│   └── server.py          # Vercel serverless function
├── public/
│   └── index.html         # Admin UI
├── veloxdb_core.py
├── storage_engine.py
├── nexadb_client.py
├── vercel.json            # Vercel configuration
├── requirements.txt       # Python dependencies
└── README.md
```

### Full `vercel.json`

```json
{
  "version": 2,
  "name": "nexadb",
  "builds": [
    {
      "src": "api/**/*.py",
      "use": "@vercel/python"
    },
    {
      "src": "public/**/*",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/",
      "dest": "/public/index.html"
    },
    {
      "src": "/api/(.*)",
      "dest": "/api/server.py"
    }
  ],
  "env": {
    "NEXADB_API_KEY": "@nexadb-api-key",
    "PYTHON_VERSION": "3.9"
  },
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.9",
      "maxDuration": 60,
      "memory": 1024
    }
  },
  "regions": ["iad1"],
  "analytics": {
    "enable": true
  }
}
```

---

## 💰 Pricing

### Vercel Free Tier

- ✅ 100 GB bandwidth/month
- ✅ 100 GB-hours serverless function execution
- ✅ Unlimited deployments
- ✅ SSL certificates
- ✅ Custom domains

### Pro Tier ($20/month)

- 1 TB bandwidth
- 1,000 GB-hours execution
- Team collaboration
- Advanced analytics

---

## 🎯 Next Steps

1. ✅ Deployed to Vercel
2. 🔒 Configure security
3. 🌐 Add custom domain
4. 📊 Enable analytics
5. 🔄 Setup CI/CD
6. 💾 Configure persistent storage

---

**Your NexaDB is now live on Vercel!**

Access it at: `https://your-project.vercel.app`

*Vercel Deployment Guide v1.0*
