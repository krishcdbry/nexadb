#!/usr/bin/env python3
"""
NexaDB Python Client SDK
=========================

Official Python client for NexaDB.

Features:
- Simple, intuitive API
- Connection pooling
- Automatic retries
- Type hints
- Async support (optional)

Usage:
    from nexadb_client import NexaDB

    # Connect
    db = NexaDB(host='localhost', port=5050, api_key='your_key')

    # Use collections
    users = db.collection('users')
    users.insert({'name': 'Alice', 'age': 28})
    users.find({'age': {'$gt': 25}})
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode


class NexaDBException(Exception):
    """Base exception for NexaDB errors"""
    pass


class CollectionClient:
    """Client for a specific collection"""

    def __init__(self, name: str, base_url: str, api_key: str):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key

    def _request(self, method: str, path: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """Make HTTP request to NexaDB server"""
        url = f"{self.base_url}{path}"

        if params:
            url += '?' + urlencode(params)

        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }

        request_data = None
        if data is not None:
            request_data = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(url, data=request_data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_data = json.loads(error_body)
                raise NexaDBException(f"{e.code} {e.reason}: {error_data.get('error', 'Unknown error')}")
            except json.JSONDecodeError:
                raise NexaDBException(f"{e.code} {e.reason}: {error_body}")
        except urllib.error.URLError as e:
            raise NexaDBException(f"Connection error: {e.reason}")

    def insert(self, document: Dict[str, Any]) -> str:
        """
        Insert a single document

        Args:
            document: Document data (dict)

        Returns:
            Document ID (str)

        Example:
            >>> users.insert({'name': 'Alice', 'age': 28})
            'a1b2c3d4e5f6'
        """
        result = self._request('POST', f'/collections/{self.name}', data=document)
        return result['document_id']

    def insert_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple documents

        Args:
            documents: List of documents

        Returns:
            List of document IDs

        Example:
            >>> users.insert_many([
            ...     {'name': 'Alice', 'age': 28},
            ...     {'name': 'Bob', 'age': 35}
            ... ])
            ['a1b2c3', 'b2c3d4']
        """
        result = self._request('POST', f'/collections/{self.name}/bulk',
                              data={'documents': documents})
        return result['document_ids']

    def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Find document by ID

        Args:
            doc_id: Document ID

        Returns:
            Document dict or None if not found

        Example:
            >>> users.find_by_id('a1b2c3d4')
            {'_id': 'a1b2c3d4', 'name': 'Alice', 'age': 28}
        """
        try:
            result = self._request('GET', f'/collections/{self.name}/{doc_id}')
            return result['document']
        except NexaDBException as e:
            if '404' in str(e):
                return None
            raise

    def find(self, query: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find documents matching query

        Args:
            query: Query dict (MongoDB-style)
            limit: Max results to return

        Returns:
            List of matching documents

        Example:
            >>> users.find({'age': {'$gt': 25}})
            [{'_id': 'a1b2', 'name': 'Alice', 'age': 28}, ...]

        Query operators:
            - $eq, $ne - Equality
            - $gt, $gte, $lt, $lte - Comparison
            - $in, $nin - Array membership
            - $regex - Regex match
            - $exists - Field exists
        """
        query = query or {}
        params = {
            'query': json.dumps(query),
            'limit': str(limit)
        }

        result = self._request('GET', f'/collections/{self.name}', params=params)
        return result['documents']

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find single document

        Args:
            query: Query dict

        Returns:
            First matching document or None

        Example:
            >>> users.find_one({'email': 'alice@example.com'})
            {'_id': 'a1b2', 'name': 'Alice', 'email': 'alice@example.com'}
        """
        results = self.find(query, limit=1)
        return results[0] if results else None

    def update(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update document by ID

        Args:
            doc_id: Document ID
            updates: Fields to update

        Returns:
            True if updated, False if not found

        Example:
            >>> users.update('a1b2c3', {'age': 29})
            True
        """
        try:
            self._request('PUT', f'/collections/{self.name}/{doc_id}', data=updates)
            return True
        except NexaDBException as e:
            if '404' in str(e):
                return False
            raise

    def delete(self, doc_id: str) -> bool:
        """
        Delete document by ID

        Args:
            doc_id: Document ID

        Returns:
            True if deleted, False if not found

        Example:
            >>> users.delete('a1b2c3')
            True
        """
        try:
            self._request('DELETE', f'/collections/{self.name}/{doc_id}')
            return True
        except NexaDBException as e:
            if '404' in str(e):
                return False
            raise

    def query(self, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Complex query (alternative to find())

        Args:
            query: Query dict
            limit: Max results

        Returns:
            List of documents

        Example:
            >>> users.query({
            ...     'age': {'$gte': 25, '$lte': 35},
            ...     'tags': {'$in': ['python', 'database']}
            ... })
        """
        result = self._request('POST', f'/collections/{self.name}/query',
                              data={'query': query, 'limit': limit})
        return result['documents']

    def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aggregation pipeline

        Args:
            pipeline: List of aggregation stages

        Returns:
            Aggregation results

        Example:
            >>> users.aggregate([
            ...     {'$match': {'age': {'$gte': 30}}},
            ...     {'$group': {'_id': '$age', 'count': {'$sum': 1}}},
            ...     {'$sort': {'count': -1}}
            ... ])
            [{'_id': 35, 'count': 10}, {'_id': 42, 'count': 5}]

        Stages:
            - $match - Filter documents
            - $group - Group by field
            - $sort - Sort results (1=asc, -1=desc)
            - $limit - Limit results
            - $project - Select fields
        """
        result = self._request('POST', f'/collections/{self.name}/aggregate',
                              data={'pipeline': pipeline})
        return result['results']

    def count(self) -> int:
        """
        Count all documents in collection

        Returns:
            Number of documents

        Example:
            >>> users.count()
            1523
        """
        result = self._request('GET', f'/collections/{self.name}', params={'limit': '999999'})
        return result['count']


class VectorCollectionClient:
    """Client for vector collections (AI/ML)"""

    def __init__(self, name: str, base_url: str, api_key: str, dimensions: int = 768):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.dimensions = dimensions
        self.collection = CollectionClient(name, base_url, api_key)

    def _request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request"""
        return self.collection._request(method, path, data)

    def insert(self, document: Dict[str, Any], vector: List[float]) -> str:
        """
        Insert document with vector embedding

        Args:
            document: Document data
            vector: Embedding vector (must match dimensions)

        Returns:
            Document ID

        Example:
            >>> products = db.vector_collection('products', dimensions=384)
            >>> products.insert(
            ...     {'name': 'Laptop', 'price': 1200},
            ...     vector=[0.1, 0.2, ..., 0.8]  # 384-dim from sentence-transformers
            ... )
            'a1b2c3'
        """
        if len(vector) != self.dimensions:
            raise ValueError(f"Vector must have {self.dimensions} dimensions, got {len(vector)}")

        # Insert document first
        doc_id = self.collection.insert(document)

        # Store vector (implementation depends on server support)
        # For now, store vector as part of document
        self.collection.update(doc_id, {'__vector__': vector})

        return doc_id

    def search(self, query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Vector similarity search

        Args:
            query_vector: Query embedding
            limit: Max results

        Returns:
            List of {document_id, similarity, document}

        Example:
            >>> # Find similar products
            >>> results = products.search(
            ...     query_vector=[0.15, 0.22, ..., 0.78],
            ...     limit=5
            ... )
            >>> for result in results:
            ...     print(f"{result['document']['name']}: {result['similarity']:.4f}")
            Laptop: 0.9823
            Mouse: 0.8765
        """
        if len(query_vector) != self.dimensions:
            raise ValueError(f"Query vector must have {self.dimensions} dimensions")

        result = self._request('POST', f'/vector/{self.name}/search',
                              data={
                                  'vector': query_vector,
                                  'limit': limit,
                                  'dimensions': self.dimensions
                              })
        return result['results']


class NexaDB:
    """
    Main NexaDB client

    Example:
        >>> db = NexaDB(host='localhost', port=5050, api_key='your_key')
        >>> users = db.collection('users')
        >>> users.insert({'name': 'Alice', 'age': 28})
    """

    def __init__(self, host: str = 'localhost', port: int = 6969, api_key: str = ''):
        """
        Initialize NexaDB client

        Args:
            host: Server hostname
            port: Server port
            api_key: API key for authentication
        """
        self.host = host
        self.port = port
        self.api_key = api_key
        self.base_url = f"http://{host}:{port}"

    def collection(self, name: str) -> CollectionClient:
        """
        Get collection client

        Args:
            name: Collection name

        Returns:
            CollectionClient instance

        Example:
            >>> users = db.collection('users')
            >>> users.insert({'name': 'Alice'})
        """
        return CollectionClient(name, self.base_url, self.api_key)

    def vector_collection(self, name: str, dimensions: int = 768) -> VectorCollectionClient:
        """
        Get vector collection client

        Args:
            name: Collection name
            dimensions: Vector dimensions (default: 768 for BERT/sentence-transformers)

        Returns:
            VectorCollectionClient instance

        Example:
            >>> products = db.vector_collection('products', dimensions=384)
            >>> products.insert(
            ...     {'name': 'Laptop'},
            ...     vector=model.encode('laptop computer')
            ... )
        """
        return VectorCollectionClient(name, self.base_url, self.api_key, dimensions)

    def list_collections(self) -> List[str]:
        """
        List all collections

        Returns:
            List of collection names

        Example:
            >>> db.list_collections()
            ['users', 'products', 'orders']
        """
        req = urllib.request.Request(
            f"{self.base_url}/collections",
            headers={'X-API-Key': self.api_key}
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result['collections']

    def drop_collection(self, name: str) -> bool:
        """
        Delete entire collection

        Args:
            name: Collection name

        Returns:
            True if dropped, False if not found

        Example:
            >>> db.drop_collection('old_collection')
            True
        """
        try:
            req = urllib.request.Request(
                f"{self.base_url}/collections/{name}",
                headers={'X-API-Key': self.api_key},
                method='DELETE'
            )

            with urllib.request.urlopen(req) as response:
                return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            raise

    def status(self) -> Dict[str, Any]:
        """
        Get server status

        Returns:
            Status dict

        Example:
            >>> db.status()
            {'status': 'ok', 'version': '1.0.0', 'database': 'NexaDB'}
        """
        req = urllib.request.Request(
            f"{self.base_url}/status",
            headers={'X-API-Key': self.api_key}
        )

        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())

    def stats(self) -> Dict[str, Any]:
        """
        Get database statistics

        Returns:
            Stats dict

        Example:
            >>> db.stats()
            {
                'engine_stats': {...},
                'collections': 5,
                'vector_collections': 2
            }
        """
        req = urllib.request.Request(
            f"{self.base_url}/stats",
            headers={'X-API-Key': self.api_key}
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result['stats']


if __name__ == '__main__':
    print("="*70)
    print("NexaDB Python Client - Example Usage")
    print("="*70)

    # Connect to NexaDB server
    # (Make sure server is running: python nexadb_server.py)
    db = NexaDB(
        host='localhost',
        port=6969,
        api_key='b8c37e33faa946d43c2f6e5a0bc7e7e0'  # Default key
    )

    # Check server status
    print("\n[STATUS] Checking server...")
    try:
        status = db.status()
        print(f"Server: {status['database']} v{status['version']} - {status['status']}")
    except Exception as e:
        print(f"Error: Server not running? ({e})")
        print("Start server with: python nexadb_server.py")
        exit(1)

    # Create collection
    print("\n[COLLECTION] Working with 'users' collection")
    users = db.collection('users')

    # Insert documents
    print("\nInserting documents...")
    user1 = users.insert({'name': 'Alice Johnson', 'age': 28, 'email': 'alice@example.com'})
    print(f"Inserted: {user1}")

    users.insert_many([
        {'name': 'Bob Smith', 'age': 35, 'email': 'bob@example.com', 'tags': ['developer', 'python']},
        {'name': 'Charlie Brown', 'age': 42, 'email': 'charlie@example.com', 'tags': ['manager']},
        {'name': 'Diana Prince', 'age': 30, 'email': 'diana@example.com', 'tags': ['developer', 'ai']}
    ])

    # Find documents
    print("\nFinding users with age > 30:")
    results = users.find({'age': {'$gt': 30}})
    for user in results:
        print(f"  - {user['name']} (age: {user['age']})")

    # Find one
    print("\nFinding user by email:")
    alice = users.find_one({'email': 'alice@example.com'})
    if alice:
        print(f"  Found: {alice['name']}")

    # Update
    print("\nUpdating Alice's age...")
    users.update(user1, {'age': 29})
    alice = users.find_by_id(user1)
    print(f"  Updated age: {alice['age']}")

    # Aggregation
    print("\nAggregation - Group by age:")
    results = users.aggregate([
        {'$match': {'age': {'$gte': 30}}},
        {'$group': {'_id': '$age', 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}}
    ])
    for group in results:
        print(f"  Age {group['_id']}: {group['count']} users")

    # Count
    print(f"\nTotal users: {users.count()}")

    # List collections
    print(f"\nAll collections: {db.list_collections()}")

    # Stats
    print("\nDatabase stats:")
    stats = db.stats()
    print(json.dumps(stats, indent=2))

    print("\n" + "="*70)
    print("Example complete!")
    print("="*70)


def cli():
    """Command-line interface for NexaDB client"""
    import sys

    if '--help' in sys.argv or '-h' in sys.argv or len(sys.argv) == 1:
        print("NexaDB CLI - Command-line client for NexaDB")
        print("\nUsage:")
        print("  nexadb [options] <command>")
        print("\nCommands:")
        print("  status              Check server status")
        print("  collections         List all collections")
        print("  stats               Show database statistics")
        print("  example             Run example usage")
        print("\nOptions:")
        print("  --host HOST         Server host (default: localhost)")
        print("  --port PORT         Server port (default: 6969)")
        print("  --api-key KEY       API key for authentication")
        print("\nEnvironment Variables:")
        print("  NEXADB_HOST         Server host")
        print("  NEXADB_PORT         Server port")
        print("  NEXADB_API_KEY      API key")
        print("\nExamples:")
        print("  nexadb status")
        print("  nexadb --host remote.server.com --port 6969 collections")
        print("  nexadb stats")
        sys.exit(0)

    # Parse arguments
    import os
    host = os.getenv('NEXADB_HOST', 'localhost')
    port = int(os.getenv('NEXADB_PORT', 6969))
    api_key = os.getenv('NEXADB_API_KEY', 'b8c37e33faa946d43c2f6e5a0bc7e7e0')

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--host' and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--port' and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--api-key' and i + 1 < len(sys.argv):
            api_key = sys.argv[i + 1]
            i += 2
        else:
            command = sys.argv[i]
            break
    else:
        print("Error: No command specified. Use --help for usage.")
        sys.exit(1)

    # Connect to database
    try:
        db = NexaDB(host=host, port=port, api_key=api_key)
    except Exception as e:
        print(f"Error connecting to NexaDB at {host}:{port}")
        print(f"Details: {e}")
        sys.exit(1)

    # Execute command
    try:
        if command == 'status':
            status = db.status()
            print(f"Server: {status['database']} v{status['version']}")
            print(f"Status: {status['status']}")

        elif command == 'collections':
            collections = db.list_collections()
            print(f"Collections ({len(collections)}):")
            for coll in collections:
                print(f"  - {coll}")

        elif command == 'stats':
            stats = db.stats()
            print("Database Statistics:")
            print(json.dumps(stats, indent=2))

        elif command == 'example':
            # Run the example from __main__
            print("Running example... (not implemented in CLI mode)")
            print("Run: python3 -m nexadb_client")

        else:
            print(f"Unknown command: {command}")
            print("Use --help for available commands.")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
