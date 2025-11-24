# NexaDB + FastAPI Example

Build a modern async REST API with FastAPI and NexaDB.

---

## 🚀 Quick Start

```bash
# 1. Start NexaDB
nexadb start

# 2. Install dependencies
pip install fastapi uvicorn httpx

# 3. Run the API
python main.py

# 4. Open docs
open http://localhost:8000/docs
```

---

## 💻 Complete Example (main.py)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx

app = FastAPI(
    title="NexaDB FastAPI Example",
    description="Modern async REST API with NexaDB",
    version="1.0.0"
)

# NexaDB Client
class NexaDB:
    def __init__(self, url: str = "http://localhost:6969", api_key: str = "b8c37e33faa946d43c2f6e5a0bc7e7e0"):
        self.url = url
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }

    def collection(self, name: str):
        return Collection(name, self.url, self.headers)


class Collection:
    def __init__(self, name: str, base_url: str, headers: dict):
        self.name = name
        self.base_url = base_url
        self.headers = headers

    async def insert(self, data: dict) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/collections/{self.name}",
                json=data,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()["document_id"]

    async def find(self, query: dict = None, limit: int = 100) -> List[dict]:
        query = query or {}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/collections/{self.name}",
                params={"query": str(query), "limit": limit},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()["documents"]

    async def find_by_id(self, doc_id: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/collections/{self.name}/{doc_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()["document"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise

    async def update(self, doc_id: str, data: dict) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/collections/{self.name}/{doc_id}",
                json=data,
                headers=self.headers
            )
            response.raise_for_status()
            return True

    async def delete(self, doc_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/collections/{self.name}/{doc_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return True

    async def aggregate(self, pipeline: List[dict]) -> List[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/collections/{self.name}/aggregate",
                json={"pipeline": pipeline},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()["results"]


# Initialize NexaDB
db = NexaDB()
users = db.collection("users")

# Pydantic Models
class User(BaseModel):
    name: str
    email: str
    age: int
    tags: Optional[List[str]] = []


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    tags: Optional[List[str]] = None


class UserResponse(User):
    _id: str


# Routes

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: User):
    """Create a new user"""
    user_data = user.dict()
    user_id = await users.insert(user_data)
    return {"_id": user_id, **user_data}


@app.get("/users", response_model=List[UserResponse])
async def get_users(age_min: Optional[int] = None, limit: int = 100):
    """Get all users with optional age filter"""
    query = {"age": {"$gte": age_min}} if age_min else {}
    results = await users.find(query, limit=limit)
    return results


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID"""
    user = await users.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate):
    """Update user"""
    # Check if user exists
    existing = await users.find_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    # Update only provided fields
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    await users.update(user_id, update_data)

    # Return updated user
    updated_user = await users.find_by_id(user_id)
    return updated_user


@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete user"""
    existing = await users.find_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    await users.delete(user_id)
    return {"deleted": True}


@app.get("/stats/age-groups")
async def get_age_groups():
    """Get age distribution statistics"""
    stats = await users.aggregate([
        {"$group": {"_id": "$age", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ])
    return stats


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "NexaDB"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 📦 requirements.txt

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.0
pydantic==2.5.0
```

---

## 🔧 Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py

# Or with auto-reload
uvicorn main:app --reload
```

---

## 📝 API Documentation

FastAPI auto-generates interactive API docs!

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

---

## 🧪 API Examples

### Using curl

```bash
# Create user
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "age": 28,
    "tags": ["developer", "python"]
  }'

# Get all users
curl http://localhost:8000/users

# Filter by age
curl http://localhost:8000/users?age_min=25&limit=10

# Get user by ID
curl http://localhost:8000/users/abc123

# Update user
curl -X PUT http://localhost:8000/users/abc123 \
  -H "Content-Type: application/json" \
  -d '{"age": 29}'

# Delete user
curl -X DELETE http://localhost:8000/users/abc123

# Get statistics
curl http://localhost:8000/stats/age-groups
```

### Using Python httpx

```python
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Create user
        response = await client.post(
            "http://localhost:8000/users",
            json={
                "name": "Bob Smith",
                "email": "bob@example.com",
                "age": 35,
                "tags": ["backend", "api"]
            }
        )
        user = response.json()
        print(f"Created user: {user['_id']}")

        # Get all users
        response = await client.get("http://localhost:8000/users")
        users = response.json()
        print(f"Total users: {len(users)}")

import asyncio
asyncio.run(main())
```

---

## 🚀 Deploy to Production

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t nexadb-fastapi .
docker run -p 8000:8000 nexadb-fastapi
```

### Railway

```bash
railway login
railway init
railway up
```

### Render

Create `render.yaml`:

```yaml
services:
  - type: web
    name: nexadb-fastapi
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## 🎯 Features

- ✅ Async/await support
- ✅ Auto-generated API docs
- ✅ Type validation (Pydantic)
- ✅ Modern Python 3.11+
- ✅ Error handling
- ✅ Production-ready
- ✅ Fast performance

---

## 🔧 Advanced Features

### Authentication

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "your-secret-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return credentials.credentials

@app.get("/protected")
async def protected_route(token: str = Depends(verify_token)):
    return {"message": "You have access!"}
```

### CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Background Tasks

```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Send email logic
    print(f"Sending email to {email}: {message}")

@app.post("/users")
async def create_user(user: User, background_tasks: BackgroundTasks):
    user_id = await users.insert(user.dict())
    background_tasks.add_task(send_email, user.email, "Welcome to our platform!")
    return {"_id": user_id, **user.dict()}
```

---

**Build high-performance APIs with FastAPI + NexaDB!** 🚀
