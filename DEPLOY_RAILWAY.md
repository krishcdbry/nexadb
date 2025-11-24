# Deploy NexaDB to Railway

Deploy NexaDB to Railway with one click - includes automatic HTTPS, persistent storage, and easy scaling.

---

## 🚀 One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/yourusername/nexadb)

---

## 📋 Prerequisites

- Railway account (free tier: $5 credit/month)
- GitHub account

---

## Method 1: Deploy from GitHub (Recommended)

### Step 1: Prepare Repository

```bash
cd nexadb
git init
git add .
git commit -m "Initial commit"
git push origin main
```

### Step 2: Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `nexadb` repository
5. Click "Deploy Now"

Railway will automatically:
- ✅ Detect Python
- ✅ Install dependencies
- ✅ Start your server
- ✅ Assign a domain

### Step 3: Configure Build

Railway auto-detects, but you can customize with `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "echo 'No build needed'"
  },
  "deploy": {
    "startCommand": "python3 nexadb_server.py",
    "healthcheckPath": "/status",
    "healthcheckTimeout": 300
  }
}
```

### Step 4: Add Environment Variables

In Railway Dashboard → Variables:

```bash
NEXADB_HOST=0.0.0.0
NEXADB_PORT=$PORT
NEXADB_API_KEY=your-secure-api-key
```

**Note:** Railway provides `$PORT` automatically

---

## Method 2: Deploy via Railway CLI

### Step 1: Install Railway CLI

```bash
# macOS
brew install railway

# npm
npm install -g @railway/cli

# Or download from https://railway.app/cli
```

### Step 2: Login

```bash
railway login
```

### Step 3: Initialize Project

```bash
cd nexadb
railway init
```

### Step 4: Deploy

```bash
# Link to Railway project
railway link

# Deploy
railway up

# Add environment variables
railway variables set NEXADB_API_KEY=your-key

# Open in browser
railway open
```

---

## 📁 Project Structure

### Create `Procfile`

```
web: python3 nexadb_server.py
admin: python3 nexadb_admin_server.py
```

### Create `runtime.txt`

```
python-3.11
```

### Create `nixpacks.toml` (Optional)

```toml
[phases.setup]
nixPkgs = ["python311"]

[phases.install]
cmds = ["echo 'NexaDB has no dependencies'"]

[start]
cmd = "python3 nexadb_server.py"
```

---

## 💾 Persistent Storage

### Using Railway Volumes

```bash
# Create volume in Railway Dashboard
# Settings → Volumes → New Volume

# Name: nexadb-data
# Mount Path: /app/nexadb_data
```

Update `nexadb_server.py`:

```python
# Use mounted volume
data_dir = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', './nexadb_data')
server = NexaDBServer(data_dir=data_dir)
```

### Using Railway Database

Railway offers PostgreSQL, MySQL, Redis:

```bash
# Add PostgreSQL
railway add

# Select PostgreSQL

# Access with:
postgresql://$PGUSER:$PGPASSWORD@$PGHOST:$PGPORT/$PGDATABASE
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Set variables
railway variables set KEY=value

# List variables
railway variables

# Delete variable
railway variables delete KEY
```

### Custom Domain

```bash
# Add domain in Railway Dashboard
# Settings → Domains → Add Domain

# Enter your domain: nexadb.yourdomain.com
# Add DNS record: CNAME → your-app.railway.app
```

### Auto-Scaling

```bash
# Railway auto-scales based on load
# Configure in Dashboard → Settings → Scaling

# Min replicas: 1
# Max replicas: 10
# Target CPU: 80%
```

---

## 🔒 Security

### HTTPS (Automatic)

Railway provides free SSL certificates automatically.

### API Key Management

```bash
# Generate secure key
openssl rand -hex 32

# Set in Railway
railway variables set NEXADB_API_KEY=$(openssl rand -hex 32)
```

### Private Networking

```bash
# Enable private networking
# Dashboard → Settings → Networking → Private Network

# Access via: railway-service-name.railway.internal:6969
```

---

## 📊 Monitoring

### View Logs

```bash
# CLI
railway logs

# Follow logs
railway logs --follow

# Dashboard
# Project → Deployments → View Logs
```

### Metrics

Railway Dashboard shows:
- CPU usage
- Memory usage
- Network traffic
- Request count
- Response times

### Alerts

Configure in Dashboard → Settings → Notifications:
- Deployment failures
- High memory usage
- Error rate spikes

---

## 🚀 Multiple Services

Deploy admin UI separately:

### Service 1: Database Server

`railway.json`:

```json
{
  "deploy": {
    "startCommand": "python3 nexadb_server.py"
  }
}
```

### Service 2: Admin UI

Create new service in same project:

```json
{
  "deploy": {
    "startCommand": "python3 nexadb_admin_server.py"
  }
}
```

Connect services via private networking.

---

## 🔄 CI/CD

Railway auto-deploys on git push to main branch.

### Manual Deployment

```bash
railway up --detach
```

### Deployment Triggers

```bash
# Deploy on push to specific branch
# Dashboard → Settings → Triggers

# Branch: production
# Auto-deploy: enabled
```

### Rollback

```bash
# Rollback to previous deployment
railway rollback
```

---

## 💰 Pricing

### Hobby Plan (Free $5/month credit)

- ✅ 512 MB RAM
- ✅ Shared CPU
- ✅ 1 GB storage
- ✅ Custom domains
- ✅ Automatic SSL

### Developer Plan ($5/month)

- 8 GB RAM
- 8 vCPU
- 100 GB storage
- Priority support

### Team Plan ($20/month)

- Team collaboration
- Private networking
- Advanced metrics
- SLA

---

## 🔗 Service Variables

Railway injects these automatically:

```bash
$PORT                    # Assigned port
$RAILWAY_ENVIRONMENT     # production/development
$RAILWAY_SERVICE_NAME    # Service name
$RAILWAY_PROJECT_ID      # Project ID
$RAILWAY_DEPLOYMENT_ID   # Deployment ID
```

Use in your code:

```python
import os

port = int(os.getenv('PORT', 6969))
environment = os.getenv('RAILWAY_ENVIRONMENT', 'development')

server = NexaDBServer(
    host='0.0.0.0',
    port=port
)
```

---

## 🔧 Advanced Configuration

### Health Checks

```python
# Add health check endpoint
@app.route('/health')
def health():
    return {'status': 'healthy', 'timestamp': time.time()}
```

### Graceful Shutdown

```python
import signal

def signal_handler(sig, frame):
    print('Shutting down gracefully...')
    server.stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
```

### Resource Limits

```json
{
  "deploy": {
    "numReplicas": 2,
    "sleepApplication": false,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## 🐛 Troubleshooting

### Build Failures

```bash
# Check build logs
railway logs --build

# Force rebuild
railway up --force
```

### Port Issues

Railway assigns `$PORT` dynamically:

```python
# WRONG
port = 6969

# CORRECT
port = int(os.getenv('PORT', 6969))
```

### Memory Errors

```bash
# Check memory usage
railway status

# Upgrade plan or optimize code
```

---

## 📦 Complete Example

### File Structure

```
nexadb/
├── nexadb_server.py
├── veloxdb_core.py
├── storage_engine.py
├── railway.json
├── Procfile
├── runtime.txt
└── README.md
```

### Full Configuration

**railway.json:**

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python3 nexadb_server.py",
    "healthcheckPath": "/status",
    "healthcheckTimeout": 300,
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

**Procfile:**

```
web: python3 nexadb_server.py
```

**runtime.txt:**

```
python-3.11
```

---

## 🎯 Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] Environment variables set
- [ ] Volume mounted for data
- [ ] Custom domain configured
- [ ] SSL certificate active
- [ ] Health checks passing
- [ ] Logs monitored
- [ ] Backups configured

---

## 🚀 Quick Commands

```bash
# Deploy
railway up

# View logs
railway logs -f

# Open dashboard
railway open

# Set variables
railway variables set API_KEY=xxx

# Check status
railway status

# Link service
railway link

# Restart service
railway restart
```

---

**Your NexaDB is now live on Railway!**

Access at: `https://your-project.railway.app`

*Railway Deployment Guide v1.0*
