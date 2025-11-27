#!/usr/bin/env python3
"""
NexaDB Change Events System
============================

MongoDB-style change streams for NexaDB with real-time event notifications.

Features:
- Event types: insert, update, delete, drop_collection
- Collection-level filtering
- Full document in change event
- Thread-safe event broadcasting
- WebSocket support for real-time streaming

Usage:
------
    # Listen to all changes
    def on_change(event):
        print(f"Change detected: {event['operation']} on {event['collection']}")

    change_stream = ChangeStream(db)
    change_stream.on('insert', on_change)
    change_stream.on('update', on_change)

    # Listen to specific collection
    change_stream.on('insert', on_change, collection='users')
"""

import threading
import time
from typing import Dict, Any, List, Callable, Optional
from collections import defaultdict
import json


class ChangeEvent:
    """Represents a database change event"""

    # Event types (MongoDB-compatible)
    INSERT = 'insert'
    UPDATE = 'update'
    DELETE = 'delete'
    REPLACE = 'replace'
    DROP = 'drop'
    DROP_COLLECTION = 'dropCollection'

    def __init__(
        self,
        operation: str,
        collection: str,
        document_id: str = None,
        full_document: Dict[str, Any] = None,
        update_description: Dict[str, Any] = None
    ):
        self.operation = operation
        self.collection = collection
        self.document_id = document_id
        self.full_document = full_document
        self.update_description = update_description
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to MongoDB change stream format"""
        event = {
            'operationType': self.operation,
            'ns': {
                'db': 'nexadb',
                'coll': self.collection
            },
            'timestamp': self.timestamp
        }

        if self.document_id:
            event['documentKey'] = {'_id': self.document_id}

        if self.full_document:
            event['fullDocument'] = self.full_document

        if self.update_description:
            event['updateDescription'] = self.update_description

        return event

    def __str__(self):
        return json.dumps(self.to_dict(), indent=2)


class ChangeStream:
    """
    Change stream for monitoring database changes.

    Provides MongoDB-style change streams with callbacks.
    """

    def __init__(self):
        # Callbacks: {event_type: {collection: [callbacks]}}
        self._callbacks: Dict[str, Dict[str, List[Callable]]] = defaultdict(lambda: defaultdict(list))
        self._lock = threading.RLock()

        # Global callbacks (listen to all collections)
        self._global_callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def on(
        self,
        event_type: str,
        callback: Callable[[Dict[str, Any]], None],
        collection: Optional[str] = None
    ):
        """
        Register a callback for change events.

        Args:
            event_type: Type of event ('insert', 'update', 'delete', etc.)
            callback: Function to call when event occurs
            collection: Optional collection filter (None = listen to all)

        Example:
            def my_callback(event):
                print(f"Document {event['documentKey']['_id']} was inserted")

            stream.on('insert', my_callback, collection='users')
        """
        with self._lock:
            if collection:
                self._callbacks[event_type][collection].append(callback)
            else:
                self._global_callbacks[event_type].append(callback)

    def off(
        self,
        event_type: str,
        callback: Callable[[Dict[str, Any]], None],
        collection: Optional[str] = None
    ):
        """Remove a callback"""
        with self._lock:
            if collection:
                if callback in self._callbacks[event_type][collection]:
                    self._callbacks[event_type][collection].remove(callback)
            else:
                if callback in self._global_callbacks[event_type]:
                    self._global_callbacks[event_type].remove(callback)

    def emit(self, event: ChangeEvent):
        """
        Emit a change event to all registered callbacks.

        Called internally by VeloxDB when changes occur.
        """
        event_dict = event.to_dict()

        with self._lock:
            # Call collection-specific callbacks
            collection_callbacks = self._callbacks[event.operation].get(event.collection, [])
            for callback in collection_callbacks:
                try:
                    callback(event_dict)
                except Exception as e:
                    print(f"[CHANGE_STREAM] Error in callback: {e}")

            # Call global callbacks
            global_callbacks = self._global_callbacks[event.operation]
            for callback in global_callbacks:
                try:
                    callback(event_dict)
                except Exception as e:
                    print(f"[CHANGE_STREAM] Error in global callback: {e}")

    def watch(
        self,
        collection: Optional[str] = None,
        pipeline: Optional[List[Dict]] = None
    ):
        """
        Create a cursor-style change stream (MongoDB compatible).

        Args:
            collection: Optional collection to watch
            pipeline: Optional aggregation pipeline to filter events

        Returns:
            Iterator that yields change events

        Example:
            for change in stream.watch(collection='users'):
                print(f"Change: {change}")
        """
        import queue

        # Create a queue for this watcher
        q = queue.Queue()

        def enqueue(event):
            q.put(event)

        # Register callback
        self.on('insert', enqueue, collection=collection)
        self.on('update', enqueue, collection=collection)
        self.on('delete', enqueue, collection=collection)

        # Yield events from queue
        try:
            while True:
                event = q.get()

                # Apply pipeline filters if provided
                if pipeline:
                    # TODO: Implement aggregation pipeline filtering
                    pass

                yield event
        finally:
            # Cleanup callbacks
            self.off('insert', enqueue, collection=collection)
            self.off('update', enqueue, collection=collection)
            self.off('delete', enqueue, collection=collection)


# Global change stream instance
_global_change_stream = ChangeStream()


def get_change_stream() -> ChangeStream:
    """Get the global change stream instance"""
    return _global_change_stream


# Example usage
if __name__ == '__main__':
    # Demo
    stream = ChangeStream()

    def on_insert(event):
        print(f"✅ INSERT: Document {event['documentKey']['_id']} in {event['ns']['coll']}")
        print(f"   Data: {event.get('fullDocument', {})}")

    def on_update(event):
        print(f"🔄 UPDATE: Document {event['documentKey']['_id']} in {event['ns']['coll']}")
        print(f"   Changes: {event.get('updateDescription', {})}")

    def on_delete(event):
        print(f"❌ DELETE: Document {event['documentKey']['_id']} in {event['ns']['coll']}")

    # Listen to all collections
    stream.on('insert', on_insert)
    stream.on('update', on_update)
    stream.on('delete', on_delete)

    # Listen to specific collection
    def users_only(event):
        print(f"[USERS] Event: {event['operationType']}")

    stream.on('insert', users_only, collection='users')

    # Simulate events
    print("=== Simulating Change Events ===\n")

    event1 = ChangeEvent(
        operation='insert',
        collection='users',
        document_id='user_123',
        full_document={'name': 'John', 'email': 'john@example.com'}
    )
    stream.emit(event1)

    print()

    event2 = ChangeEvent(
        operation='update',
        collection='users',
        document_id='user_123',
        update_description={'updatedFields': {'email': 'newemail@example.com'}}
    )
    stream.emit(event2)

    print()

    event3 = ChangeEvent(
        operation='delete',
        collection='products',
        document_id='prod_456'
    )
    stream.emit(event3)
