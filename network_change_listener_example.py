#!/usr/bin/env python3
"""
Example: Listen to NexaDB Changes Over Network
================================================

Real-time change notification system for NexaDB.
- Works over the network (no filesystem access needed!)
- Can connect to remote NexaDB servers
- Real-time event notifications
- Super simple!

IMPORTANT: Use a SEPARATE connection for watching!
This example uses TWO connections:
1. Watcher connection (dedicated to receiving events)
2. Operations connection (for CRUD operations)
"""

from nexaclient import NexaClient

print("="*70)
print("NexaDB Network Change Listener")
print("="*70)

# IMPORTANT: Create DEDICATED connection for watching
# Do NOT use the same connection for both watching and operations!
watcher = NexaClient(
    host='localhost',  # Can be any server: 'db.example.com'
    port=6970,
    username='root',
    password='nexadb123'
)

print("\n[1/2] Connecting to NexaDB...")
watcher.connect()
print("✅ Connected!")

print("\n[2/2] Watching for changes on 'orders' collection...")
print("   (Keep this running, then insert orders in another terminal)\n")
print("   Pro tip: Use a separate NexaClient for operations!")

# Watch for changes in real-time!
try:
    for change in watcher.watch('orders'):
        operation = change['operationType']
        collection = change['ns']['coll']

        if operation == 'insert':
            doc = change.get('fullDocument', {})
            print(f"\n✅ NEW ORDER:")
            print(f"   Customer: {doc.get('customer', 'Unknown')}")
            print(f"   Total: ${doc.get('total', 0):.2f}")
            print(f"   Order ID: {change['documentKey']['_id']}")

        elif operation == 'update':
            doc_id = change['documentKey']['_id']
            updates = change.get('updateDescription', {}).get('updatedFields', {})
            print(f"\n🔄 ORDER UPDATED:")
            print(f"   Order ID: {doc_id}")
            print(f"   Changes: {updates}")

        elif operation == 'delete':
            doc_id = change['documentKey']['_id']
            print(f"\n❌ ORDER DELETED:")
            print(f"   Order ID: {doc_id}")

except KeyboardInterrupt:
    print("\n\n👋 Stopped watching. Goodbye!")
    watcher.disconnect()
