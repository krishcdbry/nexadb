#!/usr/bin/env python3
"""
Unified Authentication System for NexaDB
=========================================

Manages users with BOTH username/password (for binary protocol)
and API keys (for HTTP REST API).

When you create a user, they get:
- Username + Password (for binary protocol: 10x faster)
- API Key (for HTTP REST API: works everywhere)
- One RBAC role that applies to both protocols

This is like AWS: one user, multiple access methods, same permissions.
"""

import hashlib
import json
import os
import secrets
import time
from typing import Dict, Any, Optional


class UnifiedAuthManager:
    """
    Unified authentication manager.

    Features:
    - Username/password authentication (binary protocol)
    - API key authentication (HTTP REST API)
    - RBAC with 4 roles: admin, write, read, guest
    - SHA-256 password hashing
    - Persistent storage
    """

    def __init__(self, data_dir: str):
        """Initialize unified auth manager."""
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, 'users.json')
        self.users = {}  # username -> user data
        self.api_key_index = {}  # api_key -> username (for fast lookups)
        self.load_users(verbose=True)  # Print message on initial load

    def load_users(self, verbose: bool = False):
        """
        Load users from disk or create default root user.

        Args:
            verbose: If True, print loading messages (default: False for silent reloads)
        """
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)

            # Rebuild API key index
            for username, user in self.users.items():
                if 'api_key' in user:
                    self.api_key_index[user['api_key']] = username

            if verbose:
                print(f"[AUTH] Loaded {len(self.users)} users")
        else:
            # Create default root user
            root_api_key = self.create_user('root', 'nexadb123', 'admin')
            print(f"[AUTH] ⚡ Created default root user")
            print(f"[AUTH] Username: root")
            print(f"[AUTH] Password: nexadb123")
            print(f"[AUTH] API Key: {root_api_key}")
            print(f"[AUTH] ⚠️  CHANGE PASSWORD IN PRODUCTION!")

    def save_users(self):
        """Save users to disk."""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)

    def _hash_password(self, password: str) -> str:
        """Hash password with SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _generate_api_key(self) -> str:
        """Generate a secure API key."""
        # Generate 32-byte random key
        raw_key = secrets.token_urlsafe(32)
        return f"nxdb_{raw_key}"

    def create_user(self, username: str, password: str, role: str = 'read') -> str:
        """
        Create new user with BOTH password and API key.

        Args:
            username: Username for login
            password: Password for binary protocol
            role: RBAC role (admin, write, read, guest)

        Returns:
            API key (for HTTP REST API)
        """
        # Validate role
        valid_roles = ['admin', 'write', 'read', 'guest']
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")

        # Check if user already exists
        if username in self.users:
            raise ValueError(f"User '{username}' already exists")

        # Generate API key
        api_key = self._generate_api_key()

        # Create user
        self.users[username] = {
            'password_hash': self._hash_password(password),
            'api_key': api_key,
            'role': role,
            'created_at': time.time(),
            'last_login': None
        }

        # Add to API key index
        self.api_key_index[api_key] = username

        self.save_users()

        return api_key

    def authenticate_password(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate with username/password (binary protocol).

        Args:
            username: Username
            password: Password

        Returns:
            User info if authenticated, None otherwise
        """
        # Reload users from disk to get latest changes (e.g., password updates)
        self.load_users()

        if username not in self.users:
            return None

        user = self.users[username]
        password_hash = self._hash_password(password)

        if password_hash != user['password_hash']:
            return None

        # Update last login
        self.users[username]['last_login'] = time.time()
        self.save_users()

        return {
            'username': username,
            'role': user['role'],
            'api_key': user['api_key']
        }

    def authenticate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate with API key (HTTP REST API).

        Args:
            api_key: API key

        Returns:
            User info if authenticated, None otherwise
        """
        # Reload users from disk to get latest changes (e.g., role updates)
        self.load_users()

        username = self.api_key_index.get(api_key)

        if not username or username not in self.users:
            return None

        user = self.users[username]

        # Update last login
        self.users[username]['last_login'] = time.time()
        self.save_users()

        return {
            'username': username,
            'role': user['role'],
            'api_key': api_key
        }

    def change_password(self, username: str, new_password: str) -> bool:
        """Change user password."""
        if username not in self.users:
            return False

        self.users[username]['password_hash'] = self._hash_password(new_password)
        self.users[username]['password_changed_at'] = time.time()
        self.save_users()

        return True

    def regenerate_api_key(self, username: str) -> Optional[str]:
        """
        Regenerate API key for a user.

        Args:
            username: Username

        Returns:
            New API key if successful, None otherwise
        """
        if username not in self.users:
            return None

        # Remove old API key from index
        old_api_key = self.users[username].get('api_key')
        if old_api_key and old_api_key in self.api_key_index:
            del self.api_key_index[old_api_key]

        # Generate new API key
        new_api_key = self._generate_api_key()

        # Update user
        self.users[username]['api_key'] = new_api_key
        self.users[username]['api_key_regenerated_at'] = time.time()

        # Add to index
        self.api_key_index[new_api_key] = username

        self.save_users()

        return new_api_key

    def update_user(self, username: str, password: Optional[str] = None, role: Optional[str] = None) -> bool:
        """
        Update user password and/or role.

        Args:
            username: Username to update
            password: New password (optional)
            role: New role (optional)

        Returns:
            True if successful, False otherwise
        """
        if username not in self.users:
            raise ValueError(f"User '{username}' not found")

        # Validate role if provided
        if role is not None:
            valid_roles = ['admin', 'write', 'read', 'guest']
            if role not in valid_roles:
                raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")

            # Don't allow changing root role
            if username == 'root' and role != 'admin':
                raise ValueError("Cannot change root user's role")

        # Update password if provided
        if password is not None:
            self.users[username]['password_hash'] = self._hash_password(password)
            self.users[username]['password_changed_at'] = time.time()

        # Update role if provided
        if role is not None:
            self.users[username]['role'] = role

        self.save_users()

        return True

    def delete_user(self, username: str) -> bool:
        """Delete user (cannot delete root)."""
        if username == 'root':
            raise ValueError("Cannot delete root user")

        if username not in self.users:
            raise ValueError(f"User '{username}' not found")

        # Remove API key from index
        api_key = self.users[username].get('api_key')
        if api_key and api_key in self.api_key_index:
            del self.api_key_index[api_key]

        # Delete user
        del self.users[username]
        self.save_users()

        return True

    def list_users(self) -> Dict[str, Dict[str, Any]]:
        """List all users (without password hashes or full API keys)."""
        return {
            username: {
                'role': user['role'],
                'api_key_prefix': user.get('api_key', '')[:15] + '...' if user.get('api_key') else None,
                'created_at': user.get('created_at'),
                'last_login': user.get('last_login'),
                'password_changed_at': user.get('password_changed_at')
            }
            for username, user in self.users.items()
        }

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user info (without password hash or full API key)."""
        if username not in self.users:
            return None

        user = self.users[username]

        return {
            'username': username,
            'role': user['role'],
            'api_key_prefix': user.get('api_key', '')[:15] + '...' if user.get('api_key') else None,
            'created_at': user.get('created_at'),
            'last_login': user.get('last_login'),
            'password_changed_at': user.get('password_changed_at')
        }

    def get_full_credentials(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get full credentials for a user (including full API key).
        Only use this when showing credentials to the user who created them!

        Args:
            username: Username

        Returns:
            Full user credentials including API key
        """
        if username not in self.users:
            return None

        user = self.users[username]

        return {
            'username': username,
            'role': user['role'],
            'api_key': user.get('api_key'),
            'created_at': user.get('created_at')
        }
