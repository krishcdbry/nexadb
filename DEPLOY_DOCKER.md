# Deploy NexaDB with Docker

Complete guide for containerizing and deploying NexaDB using Docker and Docker Compose.

---

## 🐳 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/yourusername/nexadb/main/docker-compose.yml

# Start NexaDB
docker-compose up -d

# View logs
docker-compose logs -f

# Stop NexaDB
docker-compose down
```

**Access:**
- Database API: http://localhost:6969
- Admin UI: http://localhost:9999

---

## 📋 Prerequisites

- Docker 20.10 or higher
- Docker Compose 2.0 or higher

```bash
# Check versions
docker --version
docker-compose --version
```

---

## Method 1: Docker Compose (Full Setup)

### Step 1: Create `docker-compose.yml`

```yaml
version: '3.8'

services:
  nexadb:
    image: nexadb/nexadb:latest
    container_name: nexadb-server
    ports:
      - "6969:6969"
      - "9999:9999"
    volumes:
      - nexadb_data:/app/nexadb_data
      - nexadb_wal:/app/nexadb_wal
    environment:
      - NEXADB_HOST=0.0.0.0
      - NEXADB_PORT=6969
      - ADMIN_PORT=9999
      - NEXADB_API_KEY=${NEXADB_API_KEY:-b8c37e33faa946d43c2f6e5a0bc7e7e0}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:6969/status')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - nexadb-network

volumes:
  nexadb_data:
    driver: local
  nexadb_wal:
    driver: local

networks:
  nexadb-network:
    driver: bridge
```

### Step 2: Create `.env` File

```bash
# .env
NEXADB_API_KEY=your-secure-api-key-here
NEXADB_HOST=0.0.0.0
NEXADB_PORT=6969
ADMIN_PORT=9999
```

### Step 3: Launch

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f nexadb

# Check status
docker-compose ps

# Stop
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Method 2: Docker CLI

### Pull Official Image

```bash
# Pull latest version
docker pull nexadb/nexadb:latest

# Pull specific version
docker pull nexadb/nexadb:1.0.0
```

### Run Container

```bash
docker run -d \
  --name nexadb \
  -p 6969:6969 \
  -p 9999:9999 \
  -v nexadb_data:/app/nexadb_data \
  -e NEXADB_API_KEY=your-api-key \
  --restart unless-stopped \
  nexadb/nexadb:latest
```

### Manage Container

```bash
# View logs
docker logs -f nexadb

# Stop container
docker stop nexadb

# Start container
docker start nexadb

# Restart container
docker restart nexadb

# Remove container
docker rm -f nexadb

# Execute commands inside container
docker exec -it nexadb bash
```

---

## Method 3: Build Your Own Image

### Step 1: Create `Dockerfile`

```dockerfile
FROM python:3.11-slim

# Metadata
LABEL maintainer="NexaDB Team"
LABEL description="NexaDB - Zero-dependency LSM-Tree database"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Copy NexaDB files
COPY nexadb_server.py .
COPY veloxdb_core.py .
COPY storage_engine.py .
COPY nexadb_admin_professional.html .
COPY nexadb_admin_server.py .
COPY nexadb_client.py .

# Create data directories
RUN mkdir -p /app/nexadb_data /app/nexadb_wal && \
    chmod -R 755 /app

# Expose ports
EXPOSE 6969 9999

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:6969/status')" || exit 1

# Environment variables
ENV NEXADB_HOST=0.0.0.0
ENV NEXADB_PORT=6969
ENV ADMIN_PORT=9999
ENV PYTHONUNBUFFERED=1

# Create startup script
RUN echo '#!/bin/bash\n\
python3 nexadb_server.py &\n\
python3 nexadb_admin_server.py &\n\
wait -n\n\
exit $?' > /app/start.sh && chmod +x /app/start.sh

# Start both servers
CMD ["/app/start.sh"]
```

### Step 2: Build Image

```bash
# Build image
docker build -t nexadb:latest .

# Build with custom tag
docker build -t nexadb:1.0.0 .

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t nexadb:latest .
```

### Step 3: Run Your Image

```bash
docker run -d \
  --name nexadb \
  -p 6969:6969 \
  -p 9999:9999 \
  -v nexadb_data:/app/nexadb_data \
  nexadb:latest
```

---

## 🔧 Advanced Configuration

### Multi-Stage Build (Optimized)

```dockerfile
# Stage 1: Base
FROM python:3.11-slim as base

WORKDIR /app

# Copy only necessary files
COPY nexadb_server.py veloxdb_core.py storage_engine.py ./
COPY nexadb_admin_professional.html nexadb_admin_server.py ./

# Stage 2: Runtime
FROM python:3.11-alpine

WORKDIR /app

# Copy from base
COPY --from=base /app /app

# Create non-root user
RUN addgroup -g 1000 nexadb && \
    adduser -D -u 1000 -G nexadb nexadb && \
    mkdir -p /app/nexadb_data /app/nexadb_wal && \
    chown -R nexadb:nexadb /app

USER nexadb

EXPOSE 6969 9999

CMD ["python3", "nexadb_server.py"]
```

### Separate Services

**docker-compose.yml** (split services):

```yaml
version: '3.8'

services:
  nexadb-server:
    image: nexadb/server:latest
    container_name: nexadb-server
    ports:
      - "6969:6969"
    volumes:
      - nexadb_data:/app/nexadb_data
    environment:
      - NEXADB_HOST=0.0.0.0
      - NEXADB_PORT=6969
    networks:
      - nexadb-network
    restart: unless-stopped

  nexadb-admin:
    image: nexadb/admin:latest
    container_name: nexadb-admin
    ports:
      - "9999:9999"
    environment:
      - ADMIN_PORT=9999
      - NEXADB_SERVER_URL=http://nexadb-server:6969
    depends_on:
      - nexadb-server
    networks:
      - nexadb-network
    restart: unless-stopped

volumes:
  nexadb_data:

networks:
  nexadb-network:
    driver: bridge
```

---

## 🔒 Production Configuration

### With Nginx Reverse Proxy

**docker-compose.yml**:

```yaml
version: '3.8'

services:
  nexadb:
    image: nexadb/nexadb:latest
    container_name: nexadb
    volumes:
      - nexadb_data:/app/nexadb_data
    environment:
      - NEXADB_HOST=0.0.0.0
      - NEXADB_PORT=6969
      - NEXADB_API_KEY=${NEXADB_API_KEY}
    networks:
      - nexadb-network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: nexadb-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - nexadb
    networks:
      - nexadb-network
    restart: unless-stopped

volumes:
  nexadb_data:

networks:
  nexadb-network:
    driver: bridge
```

**nginx.conf**:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream nexadb_backend {
        server nexadb:6969;
    }

    server {
        listen 80;
        server_name nexadb.yourdomain.com;

        location / {
            proxy_pass http://nexadb_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### With SSL/TLS (Let's Encrypt)

```yaml
version: '3.8'

services:
  nexadb:
    image: nexadb/nexadb:latest
    networks:
      - nexadb-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - certbot_certs:/etc/letsencrypt
    networks:
      - nexadb-network

  certbot:
    image: certbot/certbot
    volumes:
      - certbot_certs:/etc/letsencrypt
    command: certonly --webroot --webroot-path=/var/www/html --email you@email.com --agree-tos --no-eff-email -d nexadb.yourdomain.com

volumes:
  nexadb_data:
  certbot_certs:

networks:
  nexadb-network:
```

---

## 📊 Monitoring

### With Prometheus & Grafana

```yaml
version: '3.8'

services:
  nexadb:
    image: nexadb/nexadb:latest
    networks:
      - monitoring

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - monitoring

volumes:
  nexadb_data:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
    driver: bridge
```

---

## 💾 Data Persistence

### Volume Types

**Named Volume (Recommended):**

```bash
docker volume create nexadb_data
docker run -v nexadb_data:/app/nexadb_data nexadb/nexadb
```

**Bind Mount:**

```bash
docker run -v /host/path/nexadb_data:/app/nexadb_data nexadb/nexadb
```

**tmpfs Mount (Testing):**

```bash
docker run --tmpfs /app/nexadb_data:rw,size=1g nexadb/nexadb
```

### Backup & Restore

**Backup:**

```bash
# Backup volume to tar
docker run --rm \
  -v nexadb_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/nexadb_backup_$(date +%Y%m%d).tar.gz -C /data .

# Backup from running container
docker exec nexadb tar czf - /app/nexadb_data > nexadb_backup.tar.gz
```

**Restore:**

```bash
# Restore from tar
docker run --rm \
  -v nexadb_data:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/nexadb_backup.tar.gz"

# Or restore to running container
docker exec -i nexadb tar xzf - -C /app/nexadb_data < nexadb_backup.tar.gz
```

---

## 🚀 Scaling with Docker Swarm

### Initialize Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml nexadb

# Scale service
docker service scale nexadb_nexadb=3

# View services
docker service ls

# Remove stack
docker stack rm nexadb
```

### Swarm Stack File

```yaml
version: '3.8'

services:
  nexadb:
    image: nexadb/nexadb:latest
    ports:
      - "6969:6969"
    volumes:
      - nexadb_data:/app/nexadb_data
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      update_config:
        parallelism: 1
        delay: 10s
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

volumes:
  nexadb_data:
```

---

## 🔧 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs nexadb

# Inspect container
docker inspect nexadb

# Check if port is in use
lsof -i :6969

# Remove and recreate
docker rm -f nexadb
docker-compose up -d
```

### Permission Issues

```bash
# Fix volume permissions
docker run --rm \
  -v nexadb_data:/data \
  alpine chown -R 1000:1000 /data

# Run as root (not recommended for production)
docker run --user root nexadb/nexadb
```

### Out of Memory

```bash
# Set memory limit
docker run --memory="1g" --memory-swap="2g" nexadb/nexadb

# In docker-compose.yml
services:
  nexadb:
    deploy:
      resources:
        limits:
          memory: 1G
```

### Network Issues

```bash
# Check container network
docker network inspect nexadb-network

# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

---

## 🎯 Best Practices

### 1. Use Multi-Stage Builds
```dockerfile
FROM python:3.11-slim as builder
# Build steps

FROM python:3.11-alpine
# Runtime only
```

### 2. Non-Root User
```dockerfile
RUN adduser -D nexadb
USER nexadb
```

### 3. Health Checks
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:6969/status || exit 1
```

### 4. Use .dockerignore
```
# .dockerignore
.git
.gitignore
*.md
.env
__pycache__
*.pyc
.DS_Store
```

### 5. Pin Image Versions
```yaml
services:
  nexadb:
    image: nexadb/nexadb:1.0.0  # Not :latest
```

---

## 📦 Publishing to Docker Hub

### Step 1: Login

```bash
docker login
```

### Step 2: Tag Image

```bash
docker tag nexadb:latest yourusername/nexadb:latest
docker tag nexadb:latest yourusername/nexadb:1.0.0
```

### Step 3: Push

```bash
docker push yourusername/nexadb:latest
docker push yourusername/nexadb:1.0.0
```

### Step 4: Create Automated Builds

Link GitHub repository to Docker Hub for automatic builds on push.

---

## 🌐 Deploy to Cloud with Docker

### AWS ECS

```bash
# Create ECR repository
aws ecr create-repository --repository-name nexadb

# Login to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com

# Push image
docker tag nexadb:latest <account-id>.dkr.ecr.<region>.amazonaws.com/nexadb:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/nexadb:latest
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/project-id/nexadb

# Deploy
gcloud run deploy nexadb \
  --image gcr.io/project-id/nexadb \
  --platform managed \
  --port 6969
```

### Azure Container Instances

```bash
# Create container
az container create \
  --resource-group myResourceGroup \
  --name nexadb \
  --image nexadb/nexadb:latest \
  --dns-name-label nexadb \
  --ports 6969 9999
```

---

## 📊 Resource Requirements

### Minimum

```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 256M
```

### Recommended

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

### Production

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
    reservations:
      cpus: '2'
      memory: 4G
```

---

## 🎯 Quick Commands Reference

```bash
# Build
docker build -t nexadb .

# Run
docker run -d -p 6969:6969 nexadb

# Logs
docker logs -f nexadb

# Shell
docker exec -it nexadb bash

# Stop
docker stop nexadb

# Remove
docker rm nexadb

# Compose up
docker-compose up -d

# Compose down
docker-compose down

# Compose logs
docker-compose logs -f

# Restart
docker-compose restart

# Update
docker-compose pull && docker-compose up -d
```

---

## 🔗 Resources

- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Docker Hub](https://hub.docker.com)
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Your NexaDB is now containerized and ready to deploy anywhere!**

*Docker Deployment Guide v1.0*
