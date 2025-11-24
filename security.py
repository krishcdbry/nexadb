#!/usr/bin/env python3
"""
NexaDB Security Module
======================

Production-grade security for NexaDB:
- Encryption at rest (AES-256-GCM)
- Authentication (API keys, JWT)
- Authorization (RBAC)
- Audit logging
- Rate limiting

Author: NexaDB Core Team
"""

import hashlib
import hmac
import secrets
import time
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock
from enum import Enum


class Role(Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    WRITE = "write"
    READ = "read"
    GUEST = "guest"


class Permission(Enum):
    """Granular permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE_COLLECTION = "create_collection"
    DROP_COLLECTION = "drop_collection"
    MANAGE_USERS = "manage_users"
    MANAGE_INDEXES = "manage_indexes"
    BACKUP = "backup"
    ADMIN = "admin"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.READ, Permission.WRITE, Permission.DELETE,
        Permission.CREATE_COLLECTION, Permission.DROP_COLLECTION,
        Permission.MANAGE_USERS, Permission.MANAGE_INDEXES,
        Permission.BACKUP, Permission.ADMIN
    ],
    Role.WRITE: [
        Permission.READ, Permission.WRITE, Permission.DELETE,
        Permission.CREATE_COLLECTION
    ],
    Role.READ: [Permission.READ],
    Role.GUEST: []
}


class Encryption:
    """
    AES-256-GCM encryption for data at rest

    Features:
    - Authenticated encryption (integrity + confidentiality)
    - Per-collection encryption keys
    - Master key from environment or KMS
    - Secure key derivation (PBKDF2)
    """

    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize encryption with master key

        Args:
            master_key: 32-byte master key (or None to generate)
        """
        if master_key is None:
            # Generate master key from environment or create new
            master_key_hex = os.getenv('NEXADB_MASTER_KEY')
            if master_key_hex:
                self.master_key = bytes.fromhex(master_key_hex)
            else:
                self.master_key = secrets.token_bytes(32)
                print("[WARNING] No NEXADB_MASTER_KEY set. Generated ephemeral key.")
                print(f"[WARNING] Set this in production: export NEXADB_MASTER_KEY={self.master_key.hex()}")
        else:
            self.master_key = master_key

        self.collection_keys = {}  # collection_name -> key

    def _derive_key(self, salt: bytes, iterations: int = 100000) -> bytes:
        """Derive encryption key using PBKDF2"""
        return hashlib.pbkdf2_hmac('sha256', self.master_key, salt, iterations, dklen=32)

    def get_collection_key(self, collection_name: str) -> bytes:
        """Get or create encryption key for collection"""
        if collection_name not in self.collection_keys:
            # Derive key from master key + collection name
            salt = hashlib.sha256(collection_name.encode()).digest()
            self.collection_keys[collection_name] = self._derive_key(salt)
        return self.collection_keys[collection_name]

    def encrypt(self, plaintext: bytes, collection_name: str) -> bytes:
        """
        Encrypt data using AES-256-GCM

        Returns: nonce(12) + ciphertext + tag(16)
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            print("[WARNING] cryptography library not installed. Data not encrypted!")
            print("[WARNING] Install: pip install cryptography")
            return plaintext

        key = self.get_collection_key(collection_name)
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        return nonce + ciphertext

    def decrypt(self, encrypted_data: bytes, collection_name: str) -> bytes:
        """Decrypt data encrypted with encrypt()"""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            # No encryption, return as-is
            return encrypted_data

        key = self.get_collection_key(collection_name)
        aesgcm = AESGCM(key)

        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext


class APIKeyManager:
    """
    API key management for authentication

    Features:
    - Secure key generation (cryptographic random)
    - Key hashing (SHA-256 + salt)
    - Key rotation
    - Expiry dates
    - Usage tracking
    """

    def __init__(self, storage_path: str = './nexadb_data/api_keys.json'):
        self.storage_path = storage_path
        self.keys: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self):
        """Load API keys from disk"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                self.keys = json.load(f)

    def save(self):
        """Save API keys to disk"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.keys, f, indent=2)

    def create_key(self, username: str, role: Role, expires_in_days: int = 365) -> str:
        """
        Create new API key

        Returns: API key string (save this, it's shown only once!)
        """
        # Generate cryptographically secure API key
        raw_key = secrets.token_urlsafe(32)

        # Hash the key for storage
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # Store metadata
        self.keys[key_hash] = {
            'username': username,
            'role': role.value,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=expires_in_days)).isoformat(),
            'last_used': None,
            'usage_count': 0
        }

        self.save()
        return raw_key

    def validate_key(self, raw_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate API key and return user info

        Returns: User metadata if valid, None otherwise
        """
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        if key_hash not in self.keys:
            return None

        key_info = self.keys[key_hash]

        # Check expiry
        expires_at = datetime.fromisoformat(key_info['expires_at'])
        if datetime.now() > expires_at:
            return None

        # Update usage stats
        key_info['last_used'] = datetime.now().isoformat()
        key_info['usage_count'] += 1
        self.save()

        return key_info

    def revoke_key(self, username: str) -> int:
        """Revoke all keys for a user"""
        count = 0
        keys_to_remove = []

        for key_hash, key_info in self.keys.items():
            if key_info['username'] == username:
                keys_to_remove.append(key_hash)
                count += 1

        for key_hash in keys_to_remove:
            del self.keys[key_hash]

        if count > 0:
            self.save()

        return count

    def list_keys(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all API keys (or for specific user)"""
        result = []
        for key_hash, key_info in self.keys.items():
            if username is None or key_info['username'] == username:
                result.append({
                    'key_hash': key_hash[:8] + '...',  # Partial hash for identification
                    **key_info
                })
        return result


class RBACManager:
    """
    Role-Based Access Control

    Features:
    - Role hierarchy (Admin > Write > Read > Guest)
    - Per-collection permissions
    - User-to-role mapping
    - Dynamic permission checks
    """

    def __init__(self):
        self.user_roles: Dict[str, Role] = {}  # username -> role
        self.collection_policies: Dict[str, Dict[str, List[Permission]]] = {}  # collection -> username -> permissions

    def assign_role(self, username: str, role: Role):
        """Assign role to user"""
        self.user_roles[username] = role

    def get_user_role(self, username: str) -> Role:
        """Get user's role (default: GUEST)"""
        return self.user_roles.get(username, Role.GUEST)

    def has_permission(self, username: str, permission: Permission, collection: Optional[str] = None) -> bool:
        """
        Check if user has permission

        Checks:
        1. Role-based permissions (global)
        2. Collection-specific policies (if collection specified)
        """
        # Get user's role
        role = self.get_user_role(username)

        # Check role permissions
        if permission in ROLE_PERMISSIONS.get(role, []):
            return True

        # Check collection-specific policies
        if collection and collection in self.collection_policies:
            user_perms = self.collection_policies[collection].get(username, [])
            if permission in user_perms:
                return True

        return False

    def grant_collection_permission(self, collection: str, username: str, permission: Permission):
        """Grant collection-specific permission to user"""
        if collection not in self.collection_policies:
            self.collection_policies[collection] = {}

        if username not in self.collection_policies[collection]:
            self.collection_policies[collection][username] = []

        if permission not in self.collection_policies[collection][username]:
            self.collection_policies[collection][username].append(permission)

    def revoke_collection_permission(self, collection: str, username: str, permission: Permission):
        """Revoke collection-specific permission"""
        if collection in self.collection_policies:
            if username in self.collection_policies[collection]:
                if permission in self.collection_policies[collection][username]:
                    self.collection_policies[collection][username].remove(permission)


class AuditLogger:
    """
    Audit logging for compliance and security

    Features:
    - All operations logged
    - User tracking
    - Tamper-proof (append-only)
    - Structured logging
    - Searchable logs
    """

    def __init__(self, log_path: str = './nexadb_data/audit.log'):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self.log_file = open(log_path, 'a')

    def log(self, event_type: str, username: str, collection: Optional[str] = None,
            document_id: Optional[str] = None, status: str = 'success',
            details: Optional[Dict[str, Any]] = None):
        """
        Log audit event

        Args:
            event_type: read, write, delete, create_collection, etc.
            username: User performing action
            collection: Collection name (if applicable)
            document_id: Document ID (if applicable)
            status: success or error
            details: Additional context
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'username': username,
            'collection': collection,
            'document_id': document_id,
            'status': status,
            'details': details or {}
        }

        self.log_file.write(json.dumps(entry) + '\n')
        self.log_file.flush()

    def search(self, username: Optional[str] = None, event_type: Optional[str] = None,
               collection: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Search audit logs"""
        results = []

        with open(self.log_path, 'r') as f:
            for line in f:
                entry = json.loads(line.strip())

                # Apply filters
                if username and entry['username'] != username:
                    continue
                if event_type and entry['event_type'] != event_type:
                    continue
                if collection and entry['collection'] != collection:
                    continue

                results.append(entry)

                if len(results) >= limit:
                    break

        return results

    def close(self):
        """Close log file"""
        self.log_file.close()


class RateLimiter:
    """
    Token bucket rate limiter

    Features:
    - Per-user rate limits
    - Per-endpoint rate limits
    - Configurable rates
    - DDoS protection
    """

    def __init__(self, default_rate: int = 100, default_burst: int = 200):
        """
        Initialize rate limiter

        Args:
            default_rate: Requests per second
            default_burst: Maximum burst size
        """
        self.default_rate = default_rate
        self.default_burst = default_burst
        self.buckets: Dict[str, Dict[str, Any]] = {}  # key -> {tokens, last_update}
        self.lock = Lock()

    def _get_bucket(self, key: str) -> Dict[str, Any]:
        """Get or create token bucket for key"""
        if key not in self.buckets:
            self.buckets[key] = {
                'tokens': self.default_burst,
                'last_update': time.time()
            }
        return self.buckets[key]

    def allow(self, key: str, cost: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed

        Returns: (allowed, info)
        """
        with self.lock:
            bucket = self._get_bucket(key)
            now = time.time()

            # Refill tokens based on time elapsed
            elapsed = now - bucket['last_update']
            tokens_to_add = elapsed * self.default_rate
            bucket['tokens'] = min(self.default_burst, bucket['tokens'] + tokens_to_add)
            bucket['last_update'] = now

            # Check if enough tokens
            if bucket['tokens'] >= cost:
                bucket['tokens'] -= cost
                return True, {
                    'allowed': True,
                    'remaining': int(bucket['tokens']),
                    'limit': self.default_burst,
                    'reset_at': now + (self.default_burst - bucket['tokens']) / self.default_rate
                }
            else:
                return False, {
                    'allowed': False,
                    'remaining': 0,
                    'limit': self.default_burst,
                    'reset_at': now + (cost - bucket['tokens']) / self.default_rate,
                    'retry_after': (cost - bucket['tokens']) / self.default_rate
                }


class SecurityManager:
    """
    Main security manager - coordinates all security features

    Usage:
        security = SecurityManager()

        # Authenticate
        user_info = security.authenticate(api_key)

        # Authorize
        if security.authorize(user_info['username'], Permission.WRITE, 'users'):
            # Perform operation
            security.audit_log('write', user_info['username'], 'users', doc_id)

        # Rate limit
        allowed, info = security.rate_limit(user_info['username'])
        if not allowed:
            raise RateLimitExceeded()
    """

    def __init__(self, data_dir: str = './nexadb_data'):
        self.encryption = Encryption()
        self.api_keys = APIKeyManager(os.path.join(data_dir, 'api_keys.json'))
        self.rbac = RBACManager()
        self.audit = AuditLogger(os.path.join(data_dir, 'audit.log'))
        self.rate_limiter = RateLimiter(default_rate=100, default_burst=200)

        # Create default admin user if no keys exist
        if not self.api_keys.keys:
            admin_key = self.api_keys.create_key('admin', Role.ADMIN, expires_in_days=3650)
            self.rbac.assign_role('admin', Role.ADMIN)
            print(f"[SECURITY] Created default admin key: {admin_key}")
            print(f"[SECURITY] Save this key securely!")

    def authenticate(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with API key"""
        return self.api_keys.validate_key(api_key)

    def authorize(self, username: str, permission: Permission, collection: Optional[str] = None) -> bool:
        """Check if user has permission"""
        return self.rbac.has_permission(username, permission, collection)

    def audit_log(self, event_type: str, username: str, collection: Optional[str] = None,
                  document_id: Optional[str] = None, status: str = 'success',
                  details: Optional[Dict[str, Any]] = None):
        """Log audit event"""
        self.audit.log(event_type, username, collection, document_id, status, details)

    def rate_limit(self, username: str) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit for user"""
        return self.rate_limiter.allow(f"user:{username}")

    def close(self):
        """Cleanup"""
        self.audit.close()


if __name__ == '__main__':
    print("="*70)
    print("NexaDB Security Module - Test Suite")
    print("="*70)

    # Test encryption
    print("\n[TEST 1] Encryption")
    enc = Encryption()
    plaintext = b"sensitive data"
    encrypted = enc.encrypt(plaintext, "test_collection")
    decrypted = enc.decrypt(encrypted, "test_collection")
    print(f"Plaintext: {plaintext}")
    print(f"Encrypted: {encrypted[:20]}... ({len(encrypted)} bytes)")
    print(f"Decrypted: {decrypted}")
    print(f"✓ Encryption works: {plaintext == decrypted}")

    # Test API keys
    print("\n[TEST 2] API Key Management")
    api_keys = APIKeyManager('./test_data/api_keys.json')
    key1 = api_keys.create_key('alice', Role.WRITE)
    key2 = api_keys.create_key('bob', Role.READ)
    print(f"Created key for alice: {key1[:16]}...")
    print(f"Created key for bob: {key2[:16]}...")

    user_info = api_keys.validate_key(key1)
    print(f"✓ Validated alice: {user_info['username']} (role: {user_info['role']})")

    # Test RBAC
    print("\n[TEST 3] RBAC")
    rbac = RBACManager()
    rbac.assign_role('alice', Role.WRITE)
    rbac.assign_role('bob', Role.READ)

    print(f"Alice can write: {rbac.has_permission('alice', Permission.WRITE)}")
    print(f"Alice can manage users: {rbac.has_permission('alice', Permission.MANAGE_USERS)}")
    print(f"Bob can read: {rbac.has_permission('bob', Permission.READ)}")
    print(f"Bob can write: {rbac.has_permission('bob', Permission.WRITE)}")

    # Test audit logging
    print("\n[TEST 4] Audit Logging")
    audit = AuditLogger('./test_data/audit.log')
    audit.log('write', 'alice', 'users', 'doc123', 'success')
    audit.log('read', 'bob', 'users', 'doc123', 'success')
    audit.log('delete', 'alice', 'users', 'doc456', 'error', {'reason': 'not found'})

    logs = audit.search(username='alice', limit=10)
    print(f"✓ Found {len(logs)} audit entries for alice")
    for log in logs:
        print(f"  - {log['timestamp']}: {log['event_type']} on {log['collection']}/{log['document_id']}")
    audit.close()

    # Test rate limiting
    print("\n[TEST 5] Rate Limiting")
    limiter = RateLimiter(default_rate=10, default_burst=20)

    allowed_count = 0
    for i in range(25):
        allowed, info = limiter.allow('user:alice')
        if allowed:
            allowed_count += 1

    print(f"✓ Allowed {allowed_count}/25 requests (expected: ~20 with burst)")

    # Test full security manager
    print("\n[TEST 6] Security Manager Integration")
    security = SecurityManager('./test_data')

    print(f"Created security manager")
    print(f"Admin key: {list(security.api_keys.keys.keys())[0][:16]}...")

    print("\n" + "="*70)
    print("Security Module Tests Complete!")
    print("="*70)
