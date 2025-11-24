# NexaDB + Express Example

Build a REST API with Express and NexaDB in 3 minutes.

---

## 🚀 Quick Start

```bash
# 1. Start NexaDB
nexadb start

# 2. Clone and run
git clone https://github.com/YOUR_USERNAME/nexadb-examples.git
cd nexadb-examples/express
npm install
npm start

# 3. Test
curl http://localhost:3000/users
```

---

## 💻 Complete Example (server.js)

```javascript
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

// NexaDB Client
class NexaDB {
  constructor(url = 'http://localhost:6969', apiKey = 'b8c37e33faa946d43c2f6e5a0bc7e7e0') {
    this.client = axios.create({
      baseURL: url,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
    });
  }

  collection(name) {
    return {
      insert: async (data) => {
        const res = await this.client.post(`/collections/${name}`, data);
        return res.data.document_id;
      },

      find: async (query = {}, limit = 100) => {
        const res = await this.client.get(`/collections/${name}`, {
          params: { query: JSON.stringify(query), limit },
        });
        return res.data.documents;
      },

      findById: async (id) => {
        const res = await this.client.get(`/collections/${name}/${id}`);
        return res.data.document;
      },

      update: async (id, data) => {
        await this.client.put(`/collections/${name}/${id}`, data);
        return true;
      },

      delete: async (id) => {
        await this.client.delete(`/collections/${name}/${id}`);
        return true;
      },

      aggregate: async (pipeline) => {
        const res = await this.client.post(`/collections/${name}/aggregate`, { pipeline });
        return res.data.results;
      },
    };
  }
}

// Initialize NexaDB
const db = new NexaDB();
const users = db.collection('users');

// Routes

// Create user
app.post('/users', async (req, res) => {
  try {
    const id = await users.insert(req.body);
    res.status(201).json({ id, ...req.body });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get all users
app.get('/users', async (req, res) => {
  try {
    const { age } = req.query;
    const query = age ? { age: { $gte: parseInt(age) } } : {};
    const results = await users.find(query);
    res.json(results);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get user by ID
app.get('/users/:id', async (req, res) => {
  try {
    const user = await users.findById(req.params.id);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    res.json(user);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update user
app.put('/users/:id', async (req, res) => {
  try {
    await users.update(req.params.id, req.body);
    res.json({ id: req.params.id, ...req.body });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Delete user
app.delete('/users/:id', async (req, res) => {
  try {
    await users.delete(req.params.id);
    res.json({ deleted: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get age statistics
app.get('/stats/age-groups', async (req, res) => {
  try {
    const stats = await users.aggregate([
      { $group: { _id: '$age', count: { $sum: 1 } } },
      { $sort: { _id: 1 } },
    ]);
    res.json(stats);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`✅ Server running on http://localhost:${PORT}`);
  console.log(`📊 NexaDB: http://localhost:6969`);
});
```

---

## 📦 package.json

```json
{
  "name": "nexadb-express-example",
  "version": "1.0.0",
  "description": "Express + NexaDB REST API",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}
```

---

## 🔧 Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Or start production
npm start
```

---

## 📝 API Examples

### Create User
```bash
curl -X POST http://localhost:3000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","age":28}'
```

### Get All Users
```bash
curl http://localhost:3000/users
```

### Filter by Age
```bash
curl http://localhost:3000/users?age=25
```

### Get User by ID
```bash
curl http://localhost:3000/users/abc123
```

### Update User
```bash
curl -X PUT http://localhost:3000/users/abc123 \
  -H "Content-Type: application/json" \
  -d '{"age":29}'
```

### Delete User
```bash
curl -X DELETE http://localhost:3000/users/abc123
```

### Age Statistics
```bash
curl http://localhost:3000/stats/age-groups
```

---

## 🚀 Deploy

### Vercel

```json
{
  "version": 2,
  "builds": [
    {
      "src": "server.js",
      "use": "@vercel/node"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/server.js"
    }
  ]
}
```

```bash
npm install -g vercel
vercel
```

### Heroku

```bash
# Create Procfile
echo "web: node server.js" > Procfile

# Deploy
heroku create
git push heroku main
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

```bash
docker build -t nexadb-express .
docker run -p 3000:3000 nexadb-express
```

---

## 🎯 Features

- ✅ Full CRUD operations
- ✅ Query filtering
- ✅ Aggregation
- ✅ Error handling
- ✅ Clean REST API
- ✅ Ready for production

---

**Build APIs fast with Express + NexaDB!** ⚡
