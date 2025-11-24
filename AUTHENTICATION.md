# NexaDB Authentication Guide

## 🔓 No API Key Required for Localhost!

Good news! **You don't need an API key when connecting from your own machine.**

---

## 🎯 How It Works

### **Localhost (Your Machine):**
✅ **No API key required**
- Automatic authentication
- Perfect for development
- Zero friction

### **Remote Connections (Production):**
🔐 **API key required**
- Security for production deployments
- Prevents unauthorized access
- Multi-user support

---

## 💻 Usage Examples

### **Web UI (Localhost):**

1. Open: http://localhost:9999
2. Connection bar shows:
   - Host: `localhost`
   - Port: `6969`
   - API Key: **(leave empty!)**
3. Click **Connect**
4. ✅ Works without API key!

### **Terminal CLI (Localhost):**

```bash
# Just run it - no API key needed!
python3 nexadb_cli.py
```

✅ Automatically connects to localhost:6969

### **Python SDK (Localhost):**

```python
from nexadb_client import NexaDB

# No API key needed for localhost
db = NexaDB(host='localhost', port=6969)

users = db.collection('users')
users.insert({'name': 'Alice', 'age': 28})
```

✅ Works without API key!

### **REST API (Localhost):**

```bash
# No X-API-Key header needed for localhost
curl http://localhost:6969/collections

curl -X POST http://localhost:6969/collections/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","age":28}'
```

✅ Works without API key!

---

## 🌐 Remote Server (Production)

### **When You Deploy NexaDB to a Server:**

```bash
# Server IP: 203.0.113.50
# Port: 6969
```

### **Web UI (Remote):**
- Host: `203.0.113.50`
- Port: `6969`
- API Key: `b8c37e33faa946d43c2f6e5a0bc7e7e0` **(required!)**

### **Python SDK (Remote):**

```python
db = NexaDB(
    host='203.0.113.50',
    port=6969,
    api_key='b8c37e33faa946d43c2f6e5a0bc7e7e0'  # Required!
)
```

### **REST API (Remote):**

```bash
# X-API-Key header required for remote
curl http://203.0.113.50:6969/collections \
  -H "X-API-Key: b8c37e33faa946d43c2f6e5a0bc7e7e0"
```

---

## 🔑 Managing API Keys

### **Default API Key:**
```
b8c37e33faa946d43c2f6e5a0bc7e7e0
```

This is printed when you start the server:
```bash
python3 nexadb_server.py

# Output:
[AUTH] Default API Key: b8c37e33faa946d43c2f6e5a0bc7e7e0
```

### **Add Custom API Keys:**

Modify `nexadb_server.py`:

```python
if __name__ == '__main__':
    server = NexaDBServer(host='0.0.0.0', port=6969)

    # Add custom API keys
    server.add_api_key('alice', 'alice_secret_key_123')
    server.add_api_key('bob', 'bob_secret_key_456')

    server.start()
```

Now users can connect with:
- Alice: `api_key=alice_secret_key_123`
- Bob: `api_key=bob_secret_key_456`

---

## 🛡️ Security Best Practices

### **Development (Localhost):**
✅ No API key needed - it's your machine!

### **Production (Remote Server):**
1. ✅ **Always use API keys**
2. ✅ **Use HTTPS** (not HTTP)
3. ✅ **Change default API key**
4. ✅ **Use strong, random keys**
5. ✅ **Rotate keys regularly**
6. ✅ **One key per user/application**

### **Generate Secure API Keys:**

```python
import secrets

# Generate a secure random API key
api_key = secrets.token_hex(32)
print(api_key)
# Output: a1b2c3d4e5f6...
```

---

## 🔍 How Localhost Detection Works

The server checks the client's IP address:

```python
def _is_localhost(self) -> bool:
    """Check if request is from localhost"""
    client_ip = self.client_address[0]
    return client_ip in ('127.0.0.1', '::1', 'localhost')
```

**Localhost IPs:**
- `127.0.0.1` (IPv4)
- `::1` (IPv6)
- `localhost` (hostname)

**All other IPs** → API key required

---

## 📊 Quick Reference

| Connection Type | API Key Required? | Example |
|----------------|-------------------|---------|
| **Localhost (Web UI)** | ❌ No | http://localhost:9999 |
| **Localhost (CLI)** | ❌ No | `python3 nexadb_cli.py` |
| **Localhost (Python)** | ❌ No | `NexaDB(host='localhost')` |
| **Localhost (curl)** | ❌ No | `curl localhost:6969/status` |
| **Remote (Web UI)** | ✅ Yes | Host: `server.com`, API Key: `xxx` |
| **Remote (CLI)** | ✅ Yes | `--api-key xxx` |
| **Remote (Python)** | ✅ Yes | `api_key='xxx'` |
| **Remote (curl)** | ✅ Yes | `-H "X-API-Key: xxx"` |

---

## 🎉 Summary

**The Problem:**
- Requiring API keys for localhost was annoying
- You're the only user on your own machine
- Extra friction for development

**The Solution:**
✅ **Localhost = No API key needed**
🔐 **Remote = API key required**

**Result:**
- Faster development
- Better security in production
- Best of both worlds!

---

## 🚀 Try It Now!

1. **Restart your server:**
   ```bash
   python3 nexadb_server.py
   ```

2. **Open Web UI:**
   ```bash
   python3 nexadb_admin_server.py
   ```

3. **Open browser:** http://localhost:9999

4. **Leave API Key field EMPTY**

5. **Click Connect**

6. **✅ It works!** No more "Unauthorized" errors!

---

**Enjoy your friction-free local development! 🎊**
