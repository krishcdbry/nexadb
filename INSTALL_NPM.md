# Install NexaDB via npm

Install and run NexaDB using npm/npx - perfect for Node.js developers.

---

## 📋 Prerequisites

- **Node.js 14+** (includes npm)
- **Python 3.8+** (NexaDB runs on Python)

```bash
# Check versions
node --version    # Should be 14.0.0 or higher
python3 --version # Should be 3.8.0 or higher
```

---

## 🚀 Quick Start (npx)

Use `npx` to run NexaDB without installing:

```bash
# Start database server
npx nexadb-server

# In another terminal, start admin UI
npx nexadb-admin
```

**Access:**
- Database API: http://localhost:6969
- Admin UI: http://localhost:9999

---

## 📦 Method 1: Global Installation (Recommended)

Install NexaDB globally to use from anywhere:

```bash
# Install globally
npm install -g nexadb

# Start server
nexadb-server

# Start admin UI (in another terminal)
nexadb-admin
```

### Using the CLI

```bash
# Show help
nexadb --help

# Start server
nexadb server

# Start admin UI
nexadb admin
```

### With Custom Options

```bash
# Custom port
nexadb-server --port 8080

# Custom host
nexadb-server --host 192.168.1.100

# Custom data directory
nexadb-server --data-dir /var/lib/nexadb
```

---

## 📂 Method 2: Local Installation (Project)

Install in your Node.js project:

```bash
# Create project
mkdir my-app
cd my-app
npm init -y

# Install NexaDB
npm install nexadb

# Add to package.json scripts
```

**package.json:**

```json
{
  "scripts": {
    "db:server": "nexadb-server",
    "db:admin": "nexadb-admin",
    "db:start": "nexadb-server & nexadb-admin"
  }
}
```

**Run:**

```bash
npm run db:server    # Start server
npm run db:admin     # Start admin UI
npm run db:start     # Start both
```

---

## 🎯 Method 3: Use in Node.js Project

While NexaDB server runs in Python, you can easily integrate it into Node.js projects:

### Start Server from Node.js

```javascript
// start-nexadb.js
const { spawn } = require('child_process');

// Start database server
const server = spawn('nexadb-server', [], {
  stdio: 'inherit'
});

// Start admin UI
const admin = spawn('nexadb-admin', [], {
  stdio: 'inherit'
});

// Cleanup on exit
process.on('exit', () => {
  server.kill();
  admin.kill();
});
```

```bash
node start-nexadb.js
```

### Use REST API from Node.js

```javascript
// nexadb-client.js
const axios = require('axios');

const NEXADB_URL = 'http://localhost:6969';
const API_KEY = 'b8c37e33faa946d43c2f6e5a0bc7e7e0';

// Insert document
async function insertUser(user) {
  const response = await axios.post(
    `${NEXADB_URL}/collections/users`,
    user,
    {
      headers: { 'X-API-Key': API_KEY }
    }
  );
  return response.data.document_id;
}

// Find documents
async function findUsers(query = {}) {
  const response = await axios.get(
    `${NEXADB_URL}/collections/users`,
    {
      params: { query: JSON.stringify(query) },
      headers: { 'X-API-Key': API_KEY }
    }
  );
  return response.data.documents;
}

// Example usage
(async () => {
  // Insert
  const userId = await insertUser({
    name: 'Alice',
    email: 'alice@example.com',
    age: 28
  });
  console.log('Inserted user:', userId);

  // Find
  const users = await findUsers({ age: { $gte: 25 } });
  console.log('Found users:', users);
})();
```

**Install axios:**

```bash
npm install axios
```

**Run:**

```bash
node nexadb-client.js
```

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
export NEXADB_API_KEY=your-custom-key
```

### Use in npm scripts

**.env file:**

```bash
NEXADB_PORT=8080
NEXADB_DATA_DIR=/var/lib/nexadb
```

**package.json:**

```json
{
  "scripts": {
    "db:start": "env-cmd nexadb-server"
  },
  "devDependencies": {
    "env-cmd": "^10.1.0"
  }
}
```

---

## 🐳 Docker Alternative

If you prefer Docker, use the official image:

```bash
# Pull image
docker pull nexadb/nexadb

# Run
docker run -p 6969:6969 -p 9999:9999 nexadb/nexadb
```

See [DEPLOY_DOCKER.md](DEPLOY_DOCKER.md) for full Docker guide.

---

## 📊 Process Management

### With PM2 (Production)

```bash
# Install PM2
npm install -g pm2

# Start services
pm2 start nexadb-server --name nexadb-server
pm2 start nexadb-admin --name nexadb-admin

# View logs
pm2 logs

# Save configuration
pm2 save
pm2 startup

# Stop services
pm2 stop nexadb-server
pm2 stop nexadb-admin
```

### ecosystem.config.js (PM2)

```javascript
module.exports = {
  apps: [
    {
      name: 'nexadb-server',
      script: 'nexadb-server',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NEXADB_HOST: '0.0.0.0',
        NEXADB_PORT: 6969,
        NEXADB_DATA_DIR: '/var/lib/nexadb'
      }
    },
    {
      name: 'nexadb-admin',
      script: 'nexadb-admin',
      instances: 1,
      autorestart: true,
      watch: false,
      env: {
        ADMIN_HOST: '0.0.0.0',
        ADMIN_PORT: 9999
      }
    }
  ]
};
```

```bash
pm2 start ecosystem.config.js
```

---

## 🔒 Security

### API Key Setup

```bash
# Generate secure API key
node -e "console.log(require('crypto').randomBytes(16).toString('hex'))"

# Set as environment variable
export NEXADB_API_KEY=your-generated-key
```

### HTTPS with Node.js Proxy

```javascript
// proxy.js
const https = require('https');
const httpProxy = require('http-proxy');
const fs = require('fs');

const proxy = httpProxy.createProxyServer({});

const options = {
  key: fs.readFileSync('key.pem'),
  cert: fs.readFileSync('cert.pem')
};

https.createServer(options, (req, res) => {
  proxy.web(req, res, {
    target: 'http://localhost:6969'
  });
}).listen(443);

console.log('HTTPS proxy listening on port 443');
```

---

## 📱 Integration Examples

### Express.js Integration

```javascript
// server.js
const express = require('express');
const { spawn } = require('child_process');
const axios = require('axios');

const app = express();

// Start NexaDB in background
const nexadb = spawn('nexadb-server', []);

// Wait for NexaDB to start
setTimeout(() => {
  console.log('NexaDB started');
}, 2000);

// Proxy API to NexaDB
app.use('/api/db', async (req, res) => {
  try {
    const response = await axios({
      method: req.method,
      url: `http://localhost:6969${req.path}`,
      data: req.body,
      headers: {
        'X-API-Key': process.env.NEXADB_API_KEY
      }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({
      error: error.message
    });
  }
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});

// Cleanup
process.on('exit', () => nexadb.kill());
```

### Next.js API Route

```javascript
// pages/api/users.js
import axios from 'axios';

const NEXADB_URL = 'http://localhost:6969';
const API_KEY = process.env.NEXADB_API_KEY;

export default async function handler(req, res) {
  if (req.method === 'GET') {
    // Get users
    const response = await axios.get(
      `${NEXADB_URL}/collections/users`,
      {
        params: { query: '{}' },
        headers: { 'X-API-Key': API_KEY }
      }
    );
    res.json(response.data);
  } else if (req.method === 'POST') {
    // Create user
    const response = await axios.post(
      `${NEXADB_URL}/collections/users`,
      req.body,
      { headers: { 'X-API-Key': API_KEY } }
    );
    res.json(response.data);
  }
}
```

---

## 🐛 Troubleshooting

### Python Not Found

```bash
# Check Python installation
which python3
python3 --version

# Install Python (macOS)
brew install python3

# Install Python (Ubuntu)
sudo apt install python3

# Install Python (Windows)
# Download from https://www.python.org/downloads/
```

### Port Already in Use

```bash
# Find process using port
lsof -i :6969

# Kill process
kill -9 <PID>

# Or use different port
nexadb-server --port 7000
```

### npm Permission Errors

```bash
# Use nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Or fix npm permissions
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.profile
source ~/.profile
```

### Module Not Found

```bash
# Reinstall
npm uninstall -g nexadb
npm install -g nexadb

# Clear cache
npm cache clean --force
```

---

## 📦 Publishing (For Maintainers)

### Prepare for Publishing

```bash
# Update version
npm version patch  # or minor, major

# Test locally
npm link
nexadb-server

# Unlink
npm unlink
```

### Publish to npm

```bash
# Login to npm
npm login

# Publish
npm publish

# Publish with tag
npm publish --tag beta
```

### Install from GitHub

```bash
# Install from GitHub directly
npm install -g github:yourusername/nexadb

# Or from specific branch
npm install -g github:yourusername/nexadb#develop
```

---

## 🎯 Quick Commands Reference

```bash
# Install
npm install -g nexadb

# Start server
nexadb-server

# Start admin
nexadb-admin

# With options
nexadb-server --port 8080 --host 0.0.0.0

# View help
nexadb --help
nexadb-server --help
nexadb-admin --help

# Uninstall
npm uninstall -g nexadb

# Update
npm update -g nexadb
```

---

## 🔗 Resources

- [npm Package](https://www.npmjs.com/package/nexadb)
- [GitHub Repository](https://github.com/yourusername/nexadb)
- [Documentation](README.md)
- [Installation Guide](INSTALLATION.md)

---

**Your NexaDB is ready to use with npm!**

Access Admin UI: http://localhost:9999

*npm Installation Guide v1.0*
