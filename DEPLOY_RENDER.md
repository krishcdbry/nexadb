# Deploy NexaDB to Render

Deploy NexaDB to Render with automatic HTTPS, managed databases, and zero-downtime deployments.

---

## 🚀 One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/nexadb)

---

## 📋 Prerequisites

- Render account (free tier available)
- GitHub/GitLab account

---

## Method 1: Deploy from Dashboard

### Step 1: Create `render.yaml`

```yaml
services:
  - type: web
    name: nexadb-server
    env: python
    buildCommand: "echo 'No build needed'"
    startCommand: "python3 nexadb_server.py"
    envVars:
      - key: NEXADB_HOST
        value: 0.0.0.0
      - key: NEXADB_PORT
        value: 6969
      - key: NEXADB_API_KEY
        generateValue: true
      - key: PYTHON_VERSION
        value: 3.11.0

  - type: web
    name: nexadb-admin
    env: python
    buildCommand: "echo 'No build needed'"
    startCommand: "python3 nexadb_admin_server.py"
    envVars:
      - key: ADMIN_PORT
        value: 9999

databases:
  - name: nexadb-storage
    databaseName: nexadb
    user: nexadb
```

### Step 2: Connect Repository

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub/GitLab repository
4. Render auto-detects `render.yaml`
5. Click "Apply"

### Step 3: Configure

Render will:
- ✅ Build your service
- ✅ Deploy to managed infrastructure
- ✅ Assign HTTPS domain
- ✅ Enable auto-deploys

---

## Method 2: Manual Configuration

### Step 1: Create Web Service

1. Dashboard → New → Web Service
2. Connect repository
3. Configure:
   - **Name:** nexadb-server
   - **Environment:** Python 3
   - **Build Command:** (leave empty)
   - **Start Command:** `python3 nexadb_server.py`
   - **Instance Type:** Free

### Step 2: Environment Variables

Add in Environment tab:

```bash
NEXADB_HOST=0.0.0.0
NEXADB_PORT=10000
NEXADB_API_KEY=your-secure-key
PYTHON_VERSION=3.11.0
```

**Note:** Render uses port 10000 by default

### Step 3: Health Checks

```yaml
healthCheckPath: /status
```

---

## 💾 Persistent Storage

### Using Render Disks

```yaml
services:
  - type: web
    name: nexadb-server
    env: python
    startCommand: "python3 nexadb_server.py"
    disk:
      name: nexadb-data
      mountPath: /data
      sizeGB: 10
```

Update server to use mounted disk:

```python
import os
data_dir = os.getenv('NEXADB_DATA_DIR', '/data/nexadb_data')
server = NexaDBServer(data_dir=data_dir)
```

### Using Managed PostgreSQL

```yaml
databases:
  - name: nexadb-postgres
    databaseName: nexadb
    user: nexadb
    plan: starter
```

Access via connection string (auto-injected):

```python
import os
db_url = os.getenv('DATABASE_URL')
```

---

## 🔧 Advanced Configuration

### Full `render.yaml`

```yaml
services:
  # Main Database Server
  - type: web
    name: nexadb-server
    env: python
    region: oregon
    plan: starter
    buildCommand: "echo 'No dependencies'"
    startCommand: "python3 nexadb_server.py"
    healthCheckPath: /status
    disk:
      name: nexadb-storage
      mountPath: /data
      sizeGB: 10
    envVars:
      - key: NEXADB_HOST
        value: 0.0.0.0
      - key: NEXADB_PORT
        sync: false
        value: 10000
      - key: NEXADB_API_KEY
        generateValue: true
      - key: NEXADB_DATA_DIR
        value: /data/nexadb_data
      - key: PYTHON_VERSION
        value: 3.11.0

  # Admin UI (Optional)
  - type: web
    name: nexadb-admin
    env: python
    region: oregon
    plan: starter
    buildCommand: "echo 'No dependencies'"
    startCommand: "python3 nexadb_admin_server.py"
    envVars:
      - key: ADMIN_PORT
        value: 10000
      - key: NEXADB_SERVER_URL
        fromService:
          type: web
          name: nexadb-server
          envVarKey: RENDER_EXTERNAL_URL

databases:
  - name: nexadb-postgres
    databaseName: nexadb
    user: nexadb
    plan: starter
```

---

## 🔒 Security

### HTTPS (Automatic)

Render provides free SSL certificates for all services.

### Custom Domain

```bash
# Add custom domain in Render Dashboard
# Settings → Custom Domains → Add Custom Domain

# DNS Configuration:
# CNAME: nexadb → your-service.onrender.com
```

### Private Services

```yaml
services:
  - type: private
    name: nexadb-internal
    # Only accessible within Render network
```

### Environment Groups

Create reusable environment variable groups:

1. Dashboard → Environment Groups
2. Create group: "nexadb-config"
3. Add variables
4. Link to services

---

## 📊 Monitoring

### View Logs

```bash
# Real-time logs in dashboard
# Or use Render API

curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv-xxx/logs
```

### Metrics

Render Dashboard shows:
- CPU usage
- Memory usage
- Network traffic
- Response times
- Error rates

### Alerts

Configure in Settings → Notifications:
- Email alerts
- Slack integration
- Webhook notifications

---

## 🔄 Deployments

### Auto-Deploy

```yaml
services:
  - type: web
    autoDeploy: true
    branch: main
```

### Manual Deploy

```bash
# Trigger deploy via API
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv-xxx/deploys
```

### Zero-Downtime Deploys

Render performs rolling updates:
1. New version deployed
2. Health checks pass
3. Traffic switched
4. Old version shutdown

### Rollback

Dashboard → Deployments → Select previous → Rollback

---

## 🚀 Scaling

### Horizontal Scaling

```yaml
services:
  - type: web
    scaling:
      minInstances: 2
      maxInstances: 10
      targetMemoryPercent: 80
      targetCPUPercent: 80
```

### Vertical Scaling

Upgrade instance type in Dashboard:
- Free (512 MB RAM)
- Starter ($7/month, 512 MB)
- Standard ($25/month, 2 GB)
- Pro ($85/month, 8 GB)

---

## 💰 Pricing

### Free Tier

- ✅ 750 hours/month
- ✅ 512 MB RAM
- ✅ Custom domains
- ✅ Auto SSL
- ⚠️ Spins down after 15 min inactivity

### Starter ($7/month)

- Always on
- 512 MB RAM
- No spin down
- Daily backups

### Standard ($25/month)

- 2 GB RAM
- 2 vCPU
- Auto-scaling
- Point-in-time recovery

---

## 🔗 Service Communication

### Internal Networking

Services can communicate via:

```bash
# Format: service-name.onrender.com
http://nexadb-server:10000
```

### Service Discovery

```python
import os

# Automatically injected by Render
nexadb_url = os.getenv('NEXADB_SERVER_URL')
admin_url = os.getenv('ADMIN_URL')
```

---

## 🔧 Build Configuration

### Custom Build Command

```yaml
services:
  - buildCommand: |
      echo "Installing dependencies..."
      pip install -r requirements.txt
      echo "Build complete"
```

### Docker (Alternative)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
EXPOSE 10000
CMD ["python3", "nexadb_server.py"]
```

```yaml
services:
  - type: web
    env: docker
    dockerfilePath: ./Dockerfile
```

---

## 🐛 Troubleshooting

### Build Failures

Check build logs in Dashboard → Events

Common issues:
- Missing files
- Wrong Python version
- Port conflicts

### Health Check Failures

```yaml
# Increase timeout
healthCheckPath: /status
healthCheckMaxRetries: 3
healthCheckInterval: 30
```

### Memory Issues

```python
# Monitor memory usage
import psutil
print(f"Memory: {psutil.virtual_memory().percent}%")

# Optimize MemTable size
memtable_size = 1024 * 1024  # 1 MB
```

---

## 📦 Complete Example

### Project Structure

```
nexadb/
├── nexadb_server.py
├── nexadb_admin_server.py
├── veloxdb_core.py
├── storage_engine.py
├── render.yaml
└── README.md
```

### Production `render.yaml`

```yaml
services:
  - type: web
    name: nexadb-production
    env: python
    region: oregon
    plan: standard
    buildCommand: "echo 'NexaDB ready'"
    startCommand: "python3 nexadb_server.py"
    healthCheckPath: /status
    disk:
      name: nexadb-prod-data
      mountPath: /data
      sizeGB: 50
    autoDeploy: true
    branch: main
    envVars:
      - key: NEXADB_HOST
        value: 0.0.0.0
      - key: NEXADB_PORT
        value: 10000
      - key: NEXADB_API_KEY
        sync: false
      - key: NEXADB_DATA_DIR
        value: /data/nexadb_data
      - key: ENVIRONMENT
        value: production

databases:
  - name: nexadb-postgres
    databaseName: nexadb_production
    plan: standard
```

---

## 🎯 Deployment Checklist

- [ ] `render.yaml` created
- [ ] Repository connected
- [ ] Environment variables set
- [ ] Disk mounted
- [ ] Health checks configured
- [ ] Custom domain added
- [ ] SSL certificate active
- [ ] Auto-deploy enabled
- [ ] Monitoring setup
- [ ] Backup configured

---

## 🚀 Quick Commands

```bash
# Deploy manually
git push origin main

# View logs
# Dashboard → Logs

# Restart service
# Dashboard → Manual Deploy → Clear build cache & deploy

# Check status
# Dashboard → Events
```

---

## 🔗 Useful Links

- [Render Dashboard](https://dashboard.render.com)
- [Render Docs](https://render.com/docs)
- [Status Page](https://status.render.com)
- [Community Forum](https://community.render.com)

---

**Your NexaDB is now live on Render!**

Access at: `https://nexadb-server.onrender.com`

*Render Deployment Guide v1.0*
