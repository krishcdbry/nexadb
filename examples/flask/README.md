# NexaDB + Flask Example

Build a simple REST API with Flask and NexaDB in 2 minutes.

---

## 🚀 Quick Start

```bash
# 1. Start NexaDB
nexadb start

# 2. Install dependencies
pip install flask requests

# 3. Run the API
python app.py

# 4. Test
curl http://localhost:5000/users
```

---

## 💻 Complete Example (app.py)

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# NexaDB Client
class NexaDB:
    def __init__(self, url="http://localhost:6969", api_key="b8c37e33faa946d43c2f6e5a0bc7e7e0"):
        self.url = url
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }

    def collection(self, name):
        return Collection(name, self.url, self.headers)


class Collection:
    def __init__(self, name, base_url, headers):
        self.name = name
        self.base_url = base_url
        self.headers = headers

    def insert(self, data):
        response = requests.post(
            f"{self.base_url}/collections/{self.name}",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["document_id"]

    def find(self, query=None, limit=100):
        query = query or {}
        response = requests.get(
            f"{self.base_url}/collections/{self.name}",
            params={"query": str(query), "limit": limit},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["documents"]

    def find_by_id(self, doc_id):
        try:
            response = requests.get(
                f"{self.base_url}/collections/{self.name}/{doc_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()["document"]
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def update(self, doc_id, data):
        response = requests.put(
            f"{self.base_url}/collections/{self.name}/{doc_id}",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return True

    def delete(self, doc_id):
        response = requests.delete(
            f"{self.base_url}/collections/{self.name}/{doc_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return True

    def aggregate(self, pipeline):
        response = requests.post(
            f"{self.base_url}/collections/{self.name}/aggregate",
            json={"pipeline": pipeline},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["results"]


# Initialize NexaDB
db = NexaDB()
users = db.collection("users")


# Routes

@app.route("/users", methods=["POST"])
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        user_id = users.insert(data)
        return jsonify({"_id": user_id, **data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/users", methods=["GET"])
def get_users():
    """Get all users with optional filtering"""
    try:
        age_min = request.args.get("age", type=int)
        query = {"age": {"$gte": age_min}} if age_min else {}
        results = users.find(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    """Get user by ID"""
    try:
        user = users.find_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    """Update user"""
    try:
        # Check if user exists
        existing = users.find_by_id(user_id)
        if not existing:
            return jsonify({"error": "User not found"}), 404

        # Update user
        data = request.get_json()
        users.update(user_id, data)

        # Return updated user
        updated_user = users.find_by_id(user_id)
        return jsonify(updated_user)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Delete user"""
    try:
        existing = users.find_by_id(user_id)
        if not existing:
            return jsonify({"error": "User not found"}), 404

        users.delete(user_id)
        return jsonify({"deleted": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/stats/age-groups", methods=["GET"])
def get_age_groups():
    """Get age distribution statistics"""
    try:
        stats = users.aggregate([
            {"$group": {"_id": "$age", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ])
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "database": "NexaDB"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
```

---

## 📦 requirements.txt

```txt
Flask==3.0.0
requests==2.31.0
```

---

## 🔧 Installation

```bash
# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python app.py
```

---

## 📝 API Examples

```bash
# Create user
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","age":28}'

# Get all users
curl http://localhost:5000/users

# Filter by age
curl http://localhost:5000/users?age=25

# Get user by ID
curl http://localhost:5000/users/abc123

# Update user
curl -X PUT http://localhost:5000/users/abc123 \
  -H "Content-Type: application/json" \
  -d '{"age":29}'

# Delete user
curl -X DELETE http://localhost:5000/users/abc123

# Get statistics
curl http://localhost:5000/stats/age-groups
```

---

## 🚀 Deploy

### Gunicorn (Production)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t nexadb-flask .
docker run -p 5000:5000 nexadb-flask
```

---

## 🎯 Features

- ✅ Simple and lightweight
- ✅ Full CRUD operations
- ✅ Query filtering
- ✅ Aggregation support
- ✅ Error handling
- ✅ Production-ready

---

**Build APIs quickly with Flask + NexaDB!** ⚡
