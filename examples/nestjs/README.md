# NexaDB + NestJS Example

Build a REST API with NestJS and NexaDB in 5 minutes.

---

## 🚀 Quick Start

```bash
# 1. Install NexaDB
brew install nexadb  # or: pip install nexadb

# 2. Start NexaDB
nexadb start  # Runs on port 6969

# 3. Clone this example
git clone https://github.com/YOUR_USERNAME/nexadb-examples.git
cd nexadb-examples/nestjs

# 4. Install dependencies
npm install

# 5. Run the API
npm run start:dev

# 6. Test it
curl http://localhost:3000/users
```

---

## 📦 Installation

### Method 1: Clone this Example

```bash
git clone https://github.com/YOUR_USERNAME/nexadb-examples.git
cd nexadb-examples/nestjs
npm install
```

### Method 2: Add to Existing NestJS Project

```bash
npm install axios
```

Copy `src/nexadb` folder to your project.

---

## 🏗️ Project Structure

```
nestjs-example/
├── src/
│   ├── nexadb/
│   │   ├── nexadb.module.ts      # NexaDB module
│   │   ├── nexadb.service.ts     # NexaDB service
│   │   └── nexadb.interface.ts   # TypeScript types
│   ├── users/
│   │   ├── users.controller.ts   # REST endpoints
│   │   ├── users.service.ts      # Business logic
│   │   └── users.module.ts       # Users module
│   ├── app.module.ts
│   └── main.ts
├── package.json
└── README.md
```

---

## 💻 Code Examples

### NexaDB Service

```typescript
// src/nexadb/nexadb.service.ts
import { Injectable } from '@nestjs/common';
import axios, { AxiosInstance } from 'axios';

@Injectable()
export class NexaDBService {
  private client: AxiosInstance;
  private baseURL: string;
  private apiKey: string;

  constructor() {
    this.baseURL = process.env.NEXADB_URL || 'http://localhost:6969';
    this.apiKey = process.env.NEXADB_API_KEY || 'b8c37e33faa946d43c2f6e5a0bc7e7e0';

    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
      },
    });
  }

  collection(name: string) {
    return {
      insert: async (data: any) => {
        const response = await this.client.post(`/collections/${name}`, data);
        return response.data.document_id;
      },

      find: async (query: any = {}, limit: number = 100) => {
        const response = await this.client.get(`/collections/${name}`, {
          params: { query: JSON.stringify(query), limit },
        });
        return response.data.documents;
      },

      findById: async (id: string) => {
        const response = await this.client.get(`/collections/${name}/${id}`);
        return response.data.document;
      },

      update: async (id: string, data: any) => {
        await this.client.put(`/collections/${name}/${id}`, data);
        return true;
      },

      delete: async (id: string) => {
        await this.client.delete(`/collections/${name}/${id}`);
        return true;
      },

      aggregate: async (pipeline: any[]) => {
        const response = await this.client.post(`/collections/${name}/aggregate`, { pipeline });
        return response.data.results;
      },
    };
  }

  async status() {
    const response = await this.client.get('/status');
    return response.data;
  }
}
```

### Users Controller

```typescript
// src/users/users.controller.ts
import { Controller, Get, Post, Put, Delete, Body, Param, Query } from '@nestjs/common';
import { UsersService } from './users.service';

@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Post()
  async create(@Body() createUserDto: any) {
    return this.usersService.create(createUserDto);
  }

  @Get()
  async findAll(@Query('age') age?: number) {
    return this.usersService.findAll(age ? { age: { $gte: age } } : {});
  }

  @Get(':id')
  async findOne(@Param('id') id: string) {
    return this.usersService.findOne(id);
  }

  @Put(':id')
  async update(@Param('id') id: string, @Body() updateUserDto: any) {
    return this.usersService.update(id, updateUserDto);
  }

  @Delete(':id')
  async remove(@Param('id') id: string) {
    return this.usersService.remove(id);
  }

  @Get('stats/age-groups')
  async getAgeGroups() {
    return this.usersService.getAgeGroups();
  }
}
```

### Users Service

```typescript
// src/users/users.service.ts
import { Injectable } from '@nestjs/common';
import { NexaDBService } from '../nexadb/nexadb.service';

@Injectable()
export class UsersService {
  private users: any;

  constructor(private nexadb: NexaDBService) {
    this.users = this.nexadb.collection('users');
  }

  async create(createUserDto: any) {
    const id = await this.users.insert(createUserDto);
    return { id, ...createUserDto };
  }

  async findAll(query: any = {}) {
    return this.users.find(query);
  }

  async findOne(id: string) {
    return this.users.findById(id);
  }

  async update(id: string, updateUserDto: any) {
    await this.users.update(id, updateUserDto);
    return { id, ...updateUserDto };
  }

  async remove(id: string) {
    await this.users.delete(id);
    return { deleted: true };
  }

  async getAgeGroups() {
    return this.users.aggregate([
      { $group: { _id: '$age', count: { $sum: 1 } } },
      { $sort: { _id: 1 } },
    ]);
  }
}
```

---

## 🔧 Configuration

### .env

```bash
NEXADB_URL=http://localhost:6969
NEXADB_API_KEY=b8c37e33faa946d43c2f6e5a0bc7e7e0
PORT=3000
```

### package.json

```json
{
  "name": "nexadb-nestjs-example",
  "version": "1.0.0",
  "scripts": {
    "start": "nest start",
    "start:dev": "nest start --watch",
    "build": "nest build"
  },
  "dependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0",
    "@nestjs/platform-express": "^10.0.0",
    "axios": "^1.6.0",
    "reflect-metadata": "^0.1.13",
    "rxjs": "^7.8.1"
  },
  "devDependencies": {
    "@nestjs/cli": "^10.0.0",
    "@types/node": "^20.0.0",
    "typescript": "^5.1.3"
  }
}
```

---

## 📝 API Endpoints

### Create User
```bash
POST http://localhost:3000/users
{
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "age": 28
}
```

### Get All Users
```bash
GET http://localhost:3000/users
```

### Filter by Age
```bash
GET http://localhost:3000/users?age=25
# Returns users with age >= 25
```

### Get User by ID
```bash
GET http://localhost:3000/users/abc123
```

### Update User
```bash
PUT http://localhost:3000/users/abc123
{
  "age": 29
}
```

### Delete User
```bash
DELETE http://localhost:3000/users/abc123
```

### Get Age Statistics
```bash
GET http://localhost:3000/users/stats/age-groups
```

---

## 🚀 Deploy to Production

### Docker

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["node", "dist/main"]
```

```bash
docker build -t nexadb-nestjs .
docker run -p 3000:3000 --env-file .env nexadb-nestjs
```

### With Docker Compose

```yaml
version: '3.8'

services:
  nexadb:
    image: nexadb/nexadb:latest
    ports:
      - "6969:6969"
    volumes:
      - nexadb_data:/app/nexadb_data

  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NEXADB_URL=http://nexadb:6969
    depends_on:
      - nexadb

volumes:
  nexadb_data:
```

```bash
docker-compose up -d
```

---

## 🎯 Features Demonstrated

- ✅ Full CRUD operations
- ✅ Query filtering
- ✅ Aggregation pipeline
- ✅ TypeScript types
- ✅ Dependency injection
- ✅ Environment variables
- ✅ Error handling
- ✅ Production deployment

---

## 📚 Learn More

- [NexaDB Documentation](https://github.com/YOUR_USERNAME/nexadb)
- [NestJS Documentation](https://docs.nestjs.com)
- [Full NexaDB API Reference](https://github.com/YOUR_USERNAME/nexadb/blob/main/API.md)

---

**Build your next MVP with NestJS + NexaDB!** 🚀
