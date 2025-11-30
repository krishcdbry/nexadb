"""
Unit Tests for Vector Operations (v3.0.0)
Tests vector indexing, HNSW creation, and similarity search
"""

import pytest
from conftest import generate_test_vector


class TestVectorIndexing:
    """Test vector index creation and management"""

    def test_create_vector_collection(self, client, test_database):
        """Test creating a collection with vector indexing"""
        collection_name = 'test_vector_collection'

        result = client.create_collection(
            collection_name,
            database=test_database,
            vector_dimensions=768
        )

        assert result['status'] == 'success'
        assert collection_name in result['collection']

        # Cleanup
        client.drop_collection(collection_name, database=test_database)

    def test_insert_document_with_vector(self, client, test_database):
        """Test inserting documents with vector embeddings"""
        collection_name = 'test_vectors'
        client.create_collection(collection_name, database=test_database, vector_dimensions=768)

        doc = {
            'title': 'Test Document',
            'content': 'Test content',
            'vector': generate_test_vector(768)
        }

        doc_id = client.insert(collection_name, doc, database=test_database)
        assert doc_id is not None

        # Cleanup
        client.drop_collection(collection_name, database=test_database)

    def test_insert_multiple_vectors(self, client, test_database):
        """Test inserting multiple documents with vectors"""
        collection_name = 'test_multi_vectors'
        client.create_collection(collection_name, database=test_database, vector_dimensions=384)

        docs = [
            {'title': f'Doc {i}', 'vector': generate_test_vector(384)}
            for i in range(10)
        ]

        for doc in docs:
            doc_id = client.insert(collection_name, doc, database=test_database)
            assert doc_id is not None

        # Verify count
        all_docs = client.query(collection_name, database=test_database)
        assert len(all_docs) == 10

        # Cleanup
        client.drop_collection(collection_name, database=test_database)

    def test_vector_dimension_validation(self, client, test_database):
        """Test that vector dimensions are validated"""
        collection_name = 'test_dimension_validation'
        client.create_collection(collection_name, database=test_database, vector_dimensions=768)

        # Insert with wrong dimensions should fail
        doc = {
            'title': 'Invalid Vector',
            'vector': generate_test_vector(384)  # Wrong dimensions
        }

        with pytest.raises(Exception):
            client.insert(collection_name, doc, database=test_database)

        # Cleanup
        client.drop_collection(collection_name, database=test_database)


class TestHNSWIndex:
    """Test HNSW index operations"""

    def test_build_hnsw_index(self, client, test_database):
        """Test building HNSW index on vector collection"""
        collection_name = 'test_hnsw'
        client.create_collection(collection_name, database=test_database, vector_dimensions=768)

        # Insert documents with vectors
        for i in range(50):
            doc = {'id': i, 'vector': generate_test_vector(768)}
            client.insert(collection_name, doc, database=test_database)

        # Build HNSW index
        result = client.build_hnsw_index(collection_name, database=test_database)
        assert result['status'] == 'success'

        # Cleanup
        client.drop_collection(collection_name, database=test_database)

    def test_hnsw_index_params(self, client, test_database):
        """Test HNSW index with custom parameters"""
        collection_name = 'test_hnsw_params'
        client.create_collection(collection_name, database=test_database, vector_dimensions=384)

        # Insert test data
        for i in range(30):
            doc = {'id': i, 'vector': generate_test_vector(384)}
            client.insert(collection_name, doc, database=test_database)

        # Build with custom params
        result = client.build_hnsw_index(
            collection_name,
            database=test_database,
            M=16,
            ef_construction=200
        )

        assert result['status'] == 'success'

        # Cleanup
        client.drop_collection(collection_name, database=test_database)

    def test_rebuild_hnsw_index(self, client, test_database):
        """Test rebuilding HNSW index after adding more documents"""
        collection_name = 'test_hnsw_rebuild'
        client.create_collection(collection_name, database=test_database, vector_dimensions=768)

        # Insert initial batch
        for i in range(50):
            doc = {'id': i, 'vector': generate_test_vector(768)}
            client.insert(collection_name, doc, database=test_database)

        # Build index
        client.build_hnsw_index(collection_name, database=test_database)

        # Insert more documents
        for i in range(50, 100):
            doc = {'id': i, 'vector': generate_test_vector(768)}
            client.insert(collection_name, doc, database=test_database)

        # Rebuild index
        result = client.build_hnsw_index(collection_name, database=test_database)
        assert result['status'] == 'success'

        # Cleanup
        client.drop_collection(collection_name, database=test_database)


class TestVectorSearch:
    """Test vector similarity search operations"""

    def test_basic_vector_search(self, client, test_database):
        """Test basic vector similarity search"""
        collection_name = 'test_search'
        client.create_collection(collection_name, database=test_database, vector_dimensions=768)

        # Insert documents
        for i in range(20):
            doc = {'id': i, 'title': f'Document {i}', 'vector': generate_test_vector(768)}
            client.insert(collection_name, doc, database=test_database)

        # Build index
        client.build_hnsw_index(collection_name, database=test_database)

        # Search
        query_vector = generate_test_vector(768)
        results = client.vector_search(
            collection_name,
            query_vector,
            limit=5,
            database=test_database
        )

        assert len(results) <= 5
        assert all('similarity' in r for r in results)
        assert all('document' in r for r in results)

        # Cleanup
        client.drop_collection(collection_name, database=test_database)

    def test_vector_search_with_filters(self, client, test_database):
        """Test vector search with metadata filters"""
        collection_name = 'test_search_filters'
        client.create_collection(collection_name, database=test_database, vector_dimensions=384)

        # Insert documents with metadata
        for i in range(30):
            doc = {
                'id': i,
                'category': 'A' if i % 2 == 0 else 'B',
                'price': i * 10,
                'vector': generate_test_vector(384)
            }
            client.insert(collection_name, doc, database=test_database)

        # Build index
        client.build_hnsw_index(collection_name, database=test_database)

        # Search with filters
        query_vector = generate_test_vector(384)
        results = client.vector_search(
            collection_name,
            query_vector,
            limit=10,
            filters={'category': 'A'},
            database=test_database
        )

        assert len(results) <= 10
        assert all(r['document']['category'] == 'A' for r in results)

        # Cleanup
        client.drop_collection(collection_name, database=test_database)

    def test_vector_search_k_parameter(self, client, test_database):
        """Test vector search with different k values"""
        collection_name = 'test_search_k'
        client.create_collection(collection_name, database=test_database, vector_dimensions=768)

        # Insert 50 documents
        for i in range(50):
            doc = {'id': i, 'vector': generate_test_vector(768)}
            client.insert(collection_name, doc, database=test_database)

        # Build index
        client.build_hnsw_index(collection_name, database=test_database)

        query_vector = generate_test_vector(768)

        # Test k=1
        results = client.vector_search(collection_name, query_vector, limit=1, database=test_database)
        assert len(results) == 1

        # Test k=10
        results = client.vector_search(collection_name, query_vector, limit=10, database=test_database)
        assert len(results) == 10

        # Test k=20
        results = client.vector_search(collection_name, query_vector, limit=20, database=test_database)
        assert len(results) == 20

        # Cleanup
        client.drop_collection(collection_name, database=test_database)

    def test_vector_search_similarity_ordering(self, client, test_database):
        """Test that results are ordered by similarity descending"""
        collection_name = 'test_similarity_order'
        client.create_collection(collection_name, database=test_database, vector_dimensions=384)

        # Insert documents
        for i in range(30):
            doc = {'id': i, 'vector': generate_test_vector(384)}
            client.insert(collection_name, doc, database=test_database)

        # Build index
        client.build_hnsw_index(collection_name, database=test_database)

        # Search
        query_vector = generate_test_vector(384)
        results = client.vector_search(collection_name, query_vector, limit=10, database=test_database)

        # Verify ordering (similarities should be descending)
        similarities = [r['similarity'] for r in results]
        assert similarities == sorted(similarities, reverse=True)

        # Cleanup
        client.drop_collection(collection_name, database=test_database)

    def test_vector_search_empty_collection(self, client, test_database):
        """Test vector search on empty collection"""
        collection_name = 'test_empty_search'
        client.create_collection(collection_name, database=test_database, vector_dimensions=768)

        query_vector = generate_test_vector(768)
        results = client.vector_search(collection_name, query_vector, limit=5, database=test_database)

        assert len(results) == 0

        # Cleanup
        client.drop_collection(collection_name, database=test_database)

    def test_vector_search_isolation_between_databases(self, client):
        """Test that vector search results are isolated between databases"""
        db1 = 'vector_isolation_db1'
        db2 = 'vector_isolation_db2'
        collection_name = 'embeddings'

        # Create databases and collections
        client.create_database(db1)
        client.create_database(db2)
        client.create_collection(collection_name, database=db1, vector_dimensions=384)
        client.create_collection(collection_name, database=db2, vector_dimensions=384)

        # Insert different vectors in each database
        for i in range(10):
            doc1 = {'db': 'db1', 'id': i, 'vector': generate_test_vector(384)}
            doc2 = {'db': 'db2', 'id': i + 100, 'vector': generate_test_vector(384)}
            client.insert(collection_name, doc1, database=db1)
            client.insert(collection_name, doc2, database=db2)

        # Build indexes
        client.build_hnsw_index(collection_name, database=db1)
        client.build_hnsw_index(collection_name, database=db2)

        # Search in each database
        query_vector = generate_test_vector(384)
        results_db1 = client.vector_search(collection_name, query_vector, limit=5, database=db1)
        results_db2 = client.vector_search(collection_name, query_vector, limit=5, database=db2)

        # Verify isolation
        assert all(r['document']['db'] == 'db1' for r in results_db1)
        assert all(r['document']['db'] == 'db2' for r in results_db2)

        # Cleanup
        client.drop_collection(collection_name, database=db1)
        client.drop_collection(collection_name, database=db2)
        client.drop_database(db1)
        client.drop_database(db2)
