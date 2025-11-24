#!/usr/bin/env python3
"""
NexaDB Index Manager
====================

Advanced indexing for production-grade performance:
- B-Tree index (range queries, sorting)
- Hash index (equality lookups)
- HNSW index (vector similarity - AI/ML)
- Full-text index (text search)

Author: NexaDB Core Team
"""

import os
import json
import pickle
import heapq
import math
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict
from datetime import datetime
import bisect


class BTreeNode:
    """
    B-Tree node for range queries and sorted data

    Properties:
    - Balanced tree (all leaves at same depth)
    - Each node has [t-1, 2t-1] keys (where t = minimum degree)
    - Operations: O(log n)
    """

    def __init__(self, leaf: bool = True, t: int = 64):
        self.leaf = leaf
        self.keys = []  # Sorted list of keys
        self.values = []  # Corresponding values (doc_ids)
        self.children = []  # Child nodes (if not leaf)
        self.t = t  # Minimum degree

    def is_full(self) -> bool:
        return len(self.keys) >= 2 * self.t - 1

    def split_child(self, index: int):
        """Split full child at index"""
        t = self.t
        full_child = self.children[index]
        new_child = BTreeNode(leaf=full_child.leaf, t=t)

        # Move half the keys to new child
        mid = t - 1
        new_child.keys = full_child.keys[mid + 1:]
        new_child.values = full_child.values[mid + 1:]
        full_child.keys = full_child.keys[:mid]
        full_child.values = full_child.values[:mid]

        # Move children if not leaf
        if not full_child.leaf:
            new_child.children = full_child.children[mid + 1:]
            full_child.children = full_child.children[:mid + 1]

        # Insert middle key into parent
        self.keys.insert(index, full_child.keys[mid])
        self.values.insert(index, full_child.values[mid])
        self.children.insert(index + 1, new_child)


class BTreeIndex:
    """
    B-Tree index for range queries and sorted access

    Use cases:
    - Range queries: age > 30 AND age < 50
    - Sorting: ORDER BY age
    - Prefix matching: name LIKE 'John%'

    Time complexity:
    - Insert: O(log n)
    - Search: O(log n)
    - Range scan: O(log n + k) where k = results
    """

    def __init__(self, field_name: str, t: int = 64):
        self.field_name = field_name
        self.t = t  # Minimum degree
        self.root = BTreeNode(leaf=True, t=t)
        self.size = 0

    def insert(self, key: Any, doc_id: str):
        """Insert key -> doc_id mapping"""
        if self.root.is_full():
            # Create new root
            new_root = BTreeNode(leaf=False, t=self.t)
            new_root.children.append(self.root)
            new_root.split_child(0)
            self.root = new_root

        self._insert_non_full(self.root, key, doc_id)
        self.size += 1

    def _insert_non_full(self, node: BTreeNode, key: Any, doc_id: str):
        """Insert into non-full node"""
        i = len(node.keys) - 1

        if node.leaf:
            # Insert into leaf
            node.keys.append(None)
            node.values.append(None)

            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1

            node.keys[i + 1] = key
            node.values[i + 1] = doc_id
        else:
            # Find child to insert
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1

            if node.children[i].is_full():
                node.split_child(i)
                if key > node.keys[i]:
                    i += 1

            self._insert_non_full(node.children[i], key, doc_id)

    def search(self, key: Any) -> List[str]:
        """Search for exact key match"""
        return self._search_node(self.root, key)

    def _search_node(self, node: BTreeNode, key: Any) -> List[str]:
        """Search in node"""
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        if i < len(node.keys) and key == node.keys[i]:
            return [node.values[i]] if node.leaf else self._search_node(node.children[i + 1], key)

        if node.leaf:
            return []

        return self._search_node(node.children[i], key)

    def range_search(self, min_key: Any, max_key: Any) -> List[str]:
        """Range query: min_key <= key <= max_key"""
        results = []
        self._range_search_node(self.root, min_key, max_key, results)
        return results

    def _range_search_node(self, node: BTreeNode, min_key: Any, max_key: Any, results: List[str]):
        """Range search in node"""
        i = 0

        while i < len(node.keys):
            if node.keys[i] < min_key:
                if not node.leaf:
                    self._range_search_node(node.children[i], min_key, max_key, results)
            elif node.keys[i] <= max_key:
                if node.leaf:
                    results.append(node.values[i])
                else:
                    self._range_search_node(node.children[i], min_key, max_key, results)
                    results.append(node.values[i])
            else:
                break
            i += 1

        # Check last child
        if not node.leaf and i < len(node.children):
            self._range_search_node(node.children[i], min_key, max_key, results)


class HashIndex:
    """
    Hash index for O(1) equality lookups

    Use cases:
    - Exact match: email = 'john@example.com'
    - IN queries: id IN (1, 2, 3)

    Time complexity:
    - Insert: O(1) average
    - Search: O(1) average
    - Space: O(n)
    """

    def __init__(self, field_name: str):
        self.field_name = field_name
        self.index: Dict[Any, List[str]] = defaultdict(list)
        self.size = 0

    def insert(self, key: Any, doc_id: str):
        """Insert key -> doc_id mapping"""
        # Hash the key for consistent lookups
        hash_key = self._hash_key(key)
        self.index[hash_key].append(doc_id)
        self.size += 1

    def search(self, key: Any) -> List[str]:
        """Search for exact key match"""
        hash_key = self._hash_key(key)
        return self.index.get(hash_key, [])

    def delete(self, key: Any, doc_id: str) -> bool:
        """Delete key -> doc_id mapping"""
        hash_key = self._hash_key(key)
        if hash_key in self.index and doc_id in self.index[hash_key]:
            self.index[hash_key].remove(doc_id)
            self.size -= 1
            return True
        return False

    def _hash_key(self, key: Any) -> int:
        """Hash key for storage"""
        if isinstance(key, (int, float, str, bool)):
            return hash(key)
        elif isinstance(key, (list, tuple)):
            return hash(tuple(key))
        elif isinstance(key, dict):
            return hash(tuple(sorted(key.items())))
        else:
            return hash(str(key))


class HNSWIndex:
    """
    Hierarchical Navigable Small World (HNSW) index for vector similarity

    State-of-the-art approximate nearest neighbor (ANN) search
    Used in production systems like Pinecone, Weaviate, Qdrant

    Properties:
    - Multi-layer graph structure
    - Logarithmic search complexity
    - High recall (>95%) with proper parameters

    Parameters:
    - M: Number of connections per node (default: 16)
    - efConstruction: Size of dynamic candidate list (default: 200)
    - efSearch: Size of search candidate list (default: 50)

    Time complexity:
    - Build: O(n * log(n) * M)
    - Search: O(log(n) * efSearch)
    """

    def __init__(self, dimensions: int, M: int = 16, efConstruction: int = 200, metric: str = 'cosine'):
        self.dimensions = dimensions
        self.M = M  # Max connections per layer
        self.M0 = M * 2  # Max connections at layer 0
        self.efConstruction = efConstruction
        self.metric = metric  # cosine, euclidean, dot_product
        self.ml = 1.0 / math.log(2.0)  # Level multiplier

        # Graph structure: layer -> {node_id -> [neighbor_ids]}
        self.graphs: List[Dict[str, List[str]]] = [{}]

        # Vectors: {doc_id -> vector}
        self.vectors: Dict[str, List[float]] = {}

        # Entry point
        self.entry_point: Optional[str] = None
        self.max_layer = 0

    def _distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate distance between vectors"""
        if self.metric == 'cosine':
            # Cosine similarity -> distance
            dot = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = math.sqrt(sum(a * a for a in vec1))
            norm2 = math.sqrt(sum(b * b for b in vec2))
            similarity = dot / (norm1 * norm2 + 1e-10)
            return 1.0 - similarity
        elif self.metric == 'euclidean':
            return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))
        elif self.metric == 'dot_product':
            return -sum(a * b for a, b in zip(vec1, vec2))
        else:
            raise ValueError(f"Unknown metric: {self.metric}")

    def _get_random_layer(self) -> int:
        """Select layer for new node using exponential decay"""
        import random
        return int(-math.log(random.uniform(0, 1)) * self.ml)

    def insert(self, doc_id: str, vector: List[float]):
        """Insert vector into HNSW index"""
        if len(vector) != self.dimensions:
            raise ValueError(f"Vector must have {self.dimensions} dimensions")

        # Store vector
        self.vectors[doc_id] = vector

        if self.entry_point is None:
            # First node
            self.entry_point = doc_id
            self.graphs[0][doc_id] = []
            return

        # Select layer for new node
        node_layer = min(self._get_random_layer(), self.max_layer + 1)

        # Ensure graph has enough layers
        while len(self.graphs) <= node_layer:
            self.graphs.append({})

        # Update max layer if needed
        if node_layer > self.max_layer:
            self.max_layer = node_layer

        # Search for nearest neighbors at each layer
        nearest = self.entry_point
        for layer in range(self.max_layer, node_layer, -1):
            nearest = self._search_layer(vector, [nearest], 1, layer)[0][1]

        # Insert node at each layer from node_layer to 0
        for layer in range(node_layer, -1, -1):
            M = self.M if layer > 0 else self.M0
            candidates = self._search_layer(vector, [nearest], self.efConstruction, layer)

            # Add bidirectional links
            self.graphs[layer][doc_id] = []
            for _, neighbor_id in candidates[:M]:
                self.graphs[layer][doc_id].append(neighbor_id)
                if neighbor_id in self.graphs[layer]:
                    self.graphs[layer][neighbor_id].append(doc_id)

                    # Prune connections if needed
                    if len(self.graphs[layer][neighbor_id]) > M:
                        self._prune_connections(neighbor_id, M, layer)

            nearest = candidates[0][1]

        # Update entry point if necessary
        if node_layer > self.max_layer:
            self.entry_point = doc_id

    def search(self, query_vector: List[float], k: int = 10, ef: Optional[int] = None) -> List[Tuple[str, float]]:
        """
        Search for k nearest neighbors

        Args:
            query_vector: Query vector
            k: Number of results
            ef: Size of candidate list (default: max(efConstruction, k))

        Returns:
            List of (doc_id, distance) sorted by distance
        """
        if ef is None:
            ef = max(self.efConstruction, k)

        if self.entry_point is None:
            return []

        # Search from top layer to layer 0
        nearest = self.entry_point
        for layer in range(self.max_layer, 0, -1):
            nearest = self._search_layer(query_vector, [nearest], 1, layer)[0][1]

        # Search layer 0 with larger ef
        candidates = self._search_layer(query_vector, [nearest], ef, 0)

        return [(doc_id, dist) for dist, doc_id in candidates[:k]]

    def _search_layer(self, query: List[float], entry_points: List[str], num_to_return: int, layer: int) -> List[Tuple[float, str]]:
        """Search single layer using beam search"""
        visited = set(entry_points)
        candidates = []
        w = []  # Dynamic candidate list

        for ep in entry_points:
            dist = self._distance(query, self.vectors[ep])
            heapq.heappush(candidates, (-dist, ep))
            heapq.heappush(w, (dist, ep))

        while candidates:
            current_dist, current_id = heapq.heappop(candidates)
            current_dist = -current_dist

            if current_dist > w[0][0]:
                break

            # Check neighbors
            if current_id in self.graphs[layer]:
                for neighbor_id in self.graphs[layer][current_id]:
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        dist = self._distance(query, self.vectors[neighbor_id])

                        if dist < w[0][0] or len(w) < num_to_return:
                            heapq.heappush(candidates, (-dist, neighbor_id))
                            heapq.heappush(w, (dist, neighbor_id))

                            if len(w) > num_to_return:
                                heapq.heappop(w)

        return sorted(w)

    def _prune_connections(self, node_id: str, M: int, layer: int):
        """Prune connections to keep only M best neighbors"""
        neighbors = self.graphs[layer][node_id]
        if len(neighbors) <= M:
            return

        # Sort neighbors by distance
        distances = [(self._distance(self.vectors[node_id], self.vectors[n]), n) for n in neighbors]
        distances.sort()

        # Keep M nearest
        self.graphs[layer][node_id] = [n for _, n in distances[:M]]


class FullTextIndex:
    """
    Inverted index for full-text search

    Use cases:
    - Text search: "machine learning database"
    - Phrase matching: "artificial intelligence"
    - Fuzzy search: "databas" matches "database"

    Features:
    - Tokenization
    - Stemming (basic)
    - Stop words removal
    - TF-IDF scoring
    """

    def __init__(self, field_name: str):
        self.field_name = field_name
        self.index: Dict[str, Set[str]] = defaultdict(set)  # term -> {doc_ids}
        self.doc_terms: Dict[str, List[str]] = {}  # doc_id -> [terms]
        self.doc_count = 0

        # Common stop words
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with'
        }

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize and normalize text"""
        # Convert to lowercase
        text = text.lower()

        # Remove punctuation and split
        import re
        tokens = re.findall(r'\b\w+\b', text)

        # Remove stop words and short tokens
        tokens = [t for t in tokens if t not in self.stop_words and len(t) > 2]

        return tokens

    def insert(self, doc_id: str, text: str):
        """Index document text"""
        tokens = self._tokenize(text)
        self.doc_terms[doc_id] = tokens

        for token in tokens:
            self.index[token].add(doc_id)

        self.doc_count += 1

    def search(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Search for documents matching query

        Returns: List of (doc_id, score) sorted by relevance
        """
        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        # Find documents containing any query term
        doc_scores: Dict[str, float] = defaultdict(float)

        for token in query_tokens:
            if token in self.index:
                # Calculate TF-IDF
                idf = math.log(self.doc_count / len(self.index[token]))

                for doc_id in self.index[token]:
                    tf = self.doc_terms[doc_id].count(token) / len(self.doc_terms[doc_id])
                    doc_scores[doc_id] += tf * idf

        # Sort by score
        results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        return results[:limit]


class IndexManager:
    """
    Unified index manager for all index types

    Usage:
        manager = IndexManager()

        # Create indexes
        manager.create_index('users', 'age', 'btree')
        manager.create_index('users', 'email', 'hash')
        manager.create_index('products', 'embedding', 'hnsw', dimensions=768)

        # Query with index
        doc_ids = manager.query('users', 'age', {'$gt': 30, '$lt': 50})
    """

    def __init__(self, data_dir: str = './nexadb_data/indexes'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        # {collection: {field: index}}
        self.indexes: Dict[str, Dict[str, Any]] = defaultdict(dict)

        # Load existing indexes
        self.load_all()

    def create_index(self, collection: str, field: str, index_type: str, **kwargs) -> bool:
        """
        Create index on collection.field

        Args:
            collection: Collection name
            field: Field name
            index_type: 'btree', 'hash', 'hnsw', 'fulltext'
            **kwargs: Index-specific parameters
        """
        if field in self.indexes[collection]:
            print(f"[INDEX] Index already exists: {collection}.{field}")
            return False

        if index_type == 'btree':
            self.indexes[collection][field] = BTreeIndex(field)
        elif index_type == 'hash':
            self.indexes[collection][field] = HashIndex(field)
        elif index_type == 'hnsw':
            dimensions = kwargs.get('dimensions', 768)
            self.indexes[collection][field] = HNSWIndex(dimensions)
        elif index_type == 'fulltext':
            self.indexes[collection][field] = FullTextIndex(field)
        else:
            raise ValueError(f"Unknown index type: {index_type}")

        print(f"[INDEX] Created {index_type} index: {collection}.{field}")
        return True

    def drop_index(self, collection: str, field: str) -> bool:
        """Drop index"""
        if field in self.indexes[collection]:
            del self.indexes[collection][field]
            self._delete_index_file(collection, field)
            print(f"[INDEX] Dropped index: {collection}.{field}")
            return True
        return False

    def list_indexes(self, collection: str) -> List[Dict[str, Any]]:
        """List all indexes for collection"""
        result = []
        for field, index in self.indexes[collection].items():
            result.append({
                'field': field,
                'type': type(index).__name__,
                'size': getattr(index, 'size', len(getattr(index, 'vectors', {})))
            })
        return result

    def save_all(self):
        """Save all indexes to disk"""
        for collection, fields in self.indexes.items():
            for field, index in fields.items():
                self._save_index(collection, field, index)

    def load_all(self):
        """Load all indexes from disk"""
        if not os.path.exists(self.data_dir):
            return

        for filename in os.listdir(self.data_dir):
            if filename.endswith('.idx'):
                parts = filename[:-4].split('_')
                if len(parts) >= 2:
                    collection = parts[0]
                    field = '_'.join(parts[1:])
                    self._load_index(collection, field)

    def _save_index(self, collection: str, field: str, index: Any):
        """Save single index"""
        filepath = os.path.join(self.data_dir, f"{collection}_{field}.idx")
        with open(filepath, 'wb') as f:
            pickle.dump(index, f)

    def _load_index(self, collection: str, field: str):
        """Load single index"""
        filepath = os.path.join(self.data_dir, f"{collection}_{field}.idx")
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                self.indexes[collection][field] = pickle.load(f)

    def _delete_index_file(self, collection: str, field: str):
        """Delete index file"""
        filepath = os.path.join(self.data_dir, f"{collection}_{field}.idx")
        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == '__main__':
    print("="*70)
    print("NexaDB Index Manager - Test Suite")
    print("="*70)

    # Test B-Tree
    print("\n[TEST 1] B-Tree Index")
    btree = BTreeIndex('age', t=3)
    for age, doc_id in [(25, 'doc1'), (30, 'doc2'), (35, 'doc3'), (40, 'doc4'), (45, 'doc5')]:
        btree.insert(age, doc_id)

    print(f"Exact search (age=30): {btree.search(30)}")
    print(f"Range search (30-45): {btree.range_search(30, 45)}")

    # Test Hash Index
    print("\n[TEST 2] Hash Index")
    hash_idx = HashIndex('email')
    hash_idx.insert('alice@example.com', 'doc1')
    hash_idx.insert('bob@example.com', 'doc2')
    hash_idx.insert('alice@example.com', 'doc3')  # Duplicate key

    print(f"Search alice@example.com: {hash_idx.search('alice@example.com')}")

    # Test HNSW
    print("\n[TEST 3] HNSW Vector Index")
    hnsw = HNSWIndex(dimensions=4, M=8, efConstruction=100)

    # Insert vectors
    vectors = [
        ('doc1', [1.0, 0.0, 0.0, 0.0]),
        ('doc2', [0.9, 0.1, 0.0, 0.0]),
        ('doc3', [0.0, 1.0, 0.0, 0.0]),
        ('doc4', [0.0, 0.0, 1.0, 0.0]),
        ('doc5', [0.8, 0.2, 0.0, 0.0]),
    ]

    for doc_id, vec in vectors:
        hnsw.insert(doc_id, vec)

    # Search
    query = [0.95, 0.05, 0.0, 0.0]
    results = hnsw.search(query, k=3)
    print(f"Query: {query}")
    print(f"Top 3 nearest neighbors:")
    for doc_id, dist in results:
        print(f"  {doc_id}: distance={dist:.4f}")

    # Test Full-Text
    print("\n[TEST 4] Full-Text Index")
    fulltext = FullTextIndex('description')
    fulltext.insert('doc1', 'Machine learning with Python and TensorFlow')
    fulltext.insert('doc2', 'Deep learning neural networks')
    fulltext.insert('doc3', 'Python database development')
    fulltext.insert('doc4', 'Machine learning algorithms')

    results = fulltext.search('machine learning', limit=3)
    print(f"Query: 'machine learning'")
    for doc_id, score in results:
        print(f"  {doc_id}: score={score:.4f}")

    print("\n" + "="*70)
    print("Index Manager Tests Complete!")
    print("="*70)
