#!/usr/bin/env python3
"""
NexaDB Root Password Reset Utility

This script allows you to reset the root user password without losing any data.
It directly modifies the users.json file with a new password hash.
"""

import json
import hashlib
import sys
import os
from pathlib import Path


def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def reset_root_password(data_dir=None, new_password=None):
    """Reset the root password"""

    # Determine data directory
    if data_dir is None:
        # Try to find users.json in common locations
        possible_locations = [
            Path.cwd() / "nexadb_data" / "users.json",
            Path.cwd() / "users.json",
            Path("/opt/homebrew/var/nexadb/users.json"),
            Path("/usr/local/var/nexadb/users.json"),
        ]

        users_file = None
        for location in possible_locations:
            if location.exists():
                users_file = location
                break

        if not users_file:
            print("Error: Could not find users.json file")
            print("Please specify the data directory with --data-dir")
            sys.exit(1)
    else:
        users_file = Path(data_dir) / "users.json"
        if not users_file.exists():
            print(f"Error: users.json not found at {users_file}")
            sys.exit(1)

    print(f"Found users file: {users_file}")

    # Load users
    try:
        with open(users_file, 'r') as f:
            users = json.load(f)
    except Exception as e:
        print(f"Error loading users.json: {e}")
        sys.exit(1)

    # Check if root user exists
    if "root" not in users:
        print("Error: Root user not found in users.json")
        sys.exit(1)

    # Get new password
    if new_password is None:
        # Default password
        new_password = "nexadb123"
        print(f"\nResetting root password to default: {new_password}")
    else:
        print(f"\nSetting new root password: {new_password}")

    # Update password hash
    password_hash = hash_password(new_password)
    users["root"]["password_hash"] = password_hash

    # Save users file
    try:
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=2)

        print(f"\n✓ Root password reset successfully!")
        print(f"\nLogin credentials:")
        print(f"  Username: root")
        print(f"  Password: {new_password}")
        print(f"\nYou can now log in to the admin panel at http://localhost:9999/admin_panel/")

    except Exception as e:
        print(f"Error saving users.json: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    data_dir = None
    new_password = None

    # Parse arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--data-dir" and i + 1 < len(args):
            data_dir = args[i + 1]
            i += 2
        elif args[i] == "--password" and i + 1 < len(args):
            new_password = args[i + 1]
            i += 2
        elif args[i] in ["-h", "--help"]:
            print("NexaDB Root Password Reset Utility")
            print("\nUsage:")
            print("  python3 reset_root_password.py [options]")
            print("\nOptions:")
            print("  --data-dir <path>    Path to data directory containing users.json")
            print("  --password <pwd>     New password (default: nexadb123)")
            print("  -h, --help           Show this help message")
            print("\nExamples:")
            print("  # Reset to default password (nexadb123)")
            print("  python3 reset_root_password.py")
            print("")
            print("  # Reset to custom password")
            print("  python3 reset_root_password.py --password myNewPassword123")
            print("")
            print("  # Specify custom data directory")
            print("  python3 reset_root_password.py --data-dir /path/to/nexadb_data")
            sys.exit(0)
        else:
            print(f"Unknown argument: {args[i]}")
            print("Use -h or --help for usage information")
            sys.exit(1)

    print("=" * 60)
    print("NexaDB Root Password Reset Utility")
    print("=" * 60)

    reset_root_password(data_dir, new_password)


if __name__ == "__main__":
    main()
