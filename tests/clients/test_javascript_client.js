/**
 * JavaScript Client Integration Tests (v3.0.0)
 * Tests nexadb-js client library
 */

const NexaClient = require('nexadb-js');
const assert = require('assert');

// Test configuration
const TEST_HOST = process.env.NEXADB_TEST_HOST || 'localhost';
const TEST_PORT = parseInt(process.env.NEXADB_TEST_PORT || 6970);

// Test state
let testsPassed = 0;
let testsFailed = 0;
let client;

// Helper function to run tests
async function runTest(name, testFn) {
    process.stdout.write(`\n🧪 ${name}... `);
    try {
        await testFn();
        console.log('✅ PASS');
        testsPassed++;
    } catch (error) {
        console.log('❌ FAIL');
        console.error(`   Error: ${error.message}`);
        testsFailed++;
    }
}

// Generate unique database name
function generateDbName(prefix = 'js_test') {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ============================================
// Database Operations Tests
// ============================================

async function testCreateDatabase() {
    const dbName = generateDbName('create_db');
    const result = await client.createDatabase(dbName);
    assert(result.status === 'success', 'Database creation failed');
    await client.dropDatabase(dbName);
}

async function testListDatabases() {
    const dbName = generateDbName('list_db');
    await client.createDatabase(dbName);

    const databases = await client.listDatabases();
    assert(databases.includes(dbName), 'Created database not found in list');

    await client.dropDatabase(dbName);
}

async function testGetDatabaseStats() {
    const dbName = generateDbName('stats_db');
    await client.createDatabase(dbName);

    const stats = await client.getDatabaseStats(dbName);
    assert('collections_count' in stats, 'Stats missing collections_count');
    assert('documents_count' in stats, 'Stats missing documents_count');

    await client.dropDatabase(dbName);
}

async function testDropDatabase() {
    const dbName = generateDbName('drop_db');
    await client.createDatabase(dbName);

    const result = await client.dropDatabase(dbName);
    assert(result.status === 'success', 'Database drop failed');

    const databases = await client.listDatabases();
    assert(!databases.includes(dbName), 'Database still exists after drop');
}

// ============================================
// Collection Operations Tests
// ============================================

async function testCreateCollection() {
    const dbName = generateDbName('coll_db');
    await client.createDatabase(dbName);

    const collName = 'test_collection';
    const result = await client.createCollection(collName, { database: dbName });
    assert(result.status === 'success', 'Collection creation failed');

    await client.dropDatabase(dbName);
}

async function testListCollections() {
    const dbName = generateDbName('list_coll_db');
    await client.createDatabase(dbName);

    const collName = 'test_collection';
    await client.createCollection(collName, { database: dbName });

    const collections = await client.listCollections({ database: dbName });
    assert(collections.includes(collName), 'Created collection not found in list');

    await client.dropDatabase(dbName);
}

async function testDropCollection() {
    const dbName = generateDbName('drop_coll_db');
    await client.createDatabase(dbName);

    const collName = 'test_collection';
    await client.createCollection(collName, { database: dbName });

    const result = await client.dropCollection(collName, { database: dbName });
    assert(result.status === 'success', 'Collection drop failed');

    await client.dropDatabase(dbName);
}

// ============================================
// Document CRUD Operations Tests
// ============================================

async function testInsertDocument() {
    const dbName = generateDbName('insert_db');
    await client.createDatabase(dbName);
    await client.createCollection('items', { database: dbName });

    const doc = { name: 'Test Item', value: 123 };
    const docId = await client.insert('items', doc, { database: dbName });

    assert(docId, 'Insert did not return document ID');
    assert(typeof docId === 'string', 'Document ID should be a string');

    await client.dropDatabase(dbName);
}

async function testQueryDocuments() {
    const dbName = generateDbName('query_db');
    await client.createDatabase(dbName);
    await client.createCollection('items', { database: dbName });

    // Insert test data
    await client.insert('items', { category: 'A', price: 10 }, { database: dbName });
    await client.insert('items', { category: 'B', price: 20 }, { database: dbName });
    await client.insert('items', { category: 'A', price: 30 }, { database: dbName });

    // Query all
    const allDocs = await client.query('items', {}, { database: dbName });
    assert(allDocs.length === 3, 'Query all should return 3 documents');

    // Query with filter
    const filteredDocs = await client.query('items', { category: 'A' }, { database: dbName });
    assert(filteredDocs.length === 2, 'Filtered query should return 2 documents');

    await client.dropDatabase(dbName);
}

async function testUpdateDocument() {
    const dbName = generateDbName('update_db');
    await client.createDatabase(dbName);
    await client.createCollection('items', { database: dbName });

    const docId = await client.insert('items', { name: 'Original', value: 100 }, { database: dbName });

    const result = await client.update('items', docId, { value: 200 }, { database: dbName });
    assert(result.status === 'success', 'Update failed');

    const docs = await client.query('items', {}, { database: dbName });
    assert(docs[0].value === 200, 'Document not updated correctly');

    await client.dropDatabase(dbName);
}

async function testDeleteDocument() {
    const dbName = generateDbName('delete_db');
    await client.createDatabase(dbName);
    await client.createCollection('items', { database: dbName });

    const docId = await client.insert('items', { name: 'To Delete' }, { database: dbName });

    const result = await client.delete('items', docId, { database: dbName });
    assert(result.status === 'success', 'Delete failed');

    const docs = await client.query('items', {}, { database: dbName });
    assert(docs.length === 0, 'Document not deleted');

    await client.dropDatabase(dbName);
}

// ============================================
// Vector Operations Tests
// ============================================

async function testCreateVectorCollection() {
    const dbName = generateDbName('vector_db');
    await client.createDatabase(dbName);

    const result = await client.createCollection('embeddings', {
        database: dbName,
        vectorDimensions: 384
    });

    assert(result.status === 'success', 'Vector collection creation failed');

    await client.dropDatabase(dbName);
}

async function testInsertVectorDocument() {
    const dbName = generateDbName('vector_insert_db');
    await client.createDatabase(dbName);
    await client.createCollection('embeddings', { database: dbName, vectorDimensions: 384 });

    const vector = Array(384).fill(0).map(() => Math.random());
    const doc = { title: 'Document 1', vector };

    const docId = await client.insert('embeddings', doc, { database: dbName });
    assert(docId, 'Vector document insert failed');

    await client.dropDatabase(dbName);
}

async function testBuildHNSWIndex() {
    const dbName = generateDbName('hnsw_db');
    await client.createDatabase(dbName);
    await client.createCollection('embeddings', { database: dbName, vectorDimensions: 384 });

    // Insert vectors
    for (let i = 0; i < 20; i++) {
        const vector = Array(384).fill(0).map(() => Math.random());
        await client.insert('embeddings', { id: i, vector }, { database: dbName });
    }

    const result = await client.buildHNSWIndex('embeddings', { database: dbName });
    assert(result.status === 'success', 'HNSW index build failed');

    await client.dropDatabase(dbName);
}

async function testVectorSearch() {
    const dbName = generateDbName('search_db');
    await client.createDatabase(dbName);
    await client.createCollection('embeddings', { database: dbName, vectorDimensions: 384 });

    // Insert vectors
    for (let i = 0; i < 30; i++) {
        const vector = Array(384).fill(0).map(() => Math.random());
        await client.insert('embeddings', { id: i, vector }, { database: dbName });
    }

    await client.buildHNSWIndex('embeddings', { database: dbName });

    // Search
    const queryVector = Array(384).fill(0).map(() => Math.random());
    const results = await client.vectorSearch('embeddings', queryVector, {
        limit: 5,
        database: dbName
    });

    assert(results.length <= 5, 'Vector search returned too many results');
    assert(results.every(r => 'similarity' in r), 'Results missing similarity scores');
    assert(results.every(r => 'document' in r), 'Results missing documents');

    await client.dropDatabase(dbName);
}

// ============================================
// TOON Format Tests
// ============================================

async function testQueryWithTOONFormat() {
    const dbName = generateDbName('toon_db');
    await client.createDatabase(dbName);
    await client.createCollection('items', { database: dbName });

    // Insert data
    for (let i = 0; i < 10; i++) {
        await client.insert('items', { id: i, name: `Item ${i}` }, { database: dbName });
    }

    const toonResult = await client.query('items', {}, { database: dbName, format: 'toon' });

    assert(toonResult, 'TOON format query returned null');
    assert(typeof toonResult === 'string', 'TOON result should be a string');

    await client.dropDatabase(dbName);
}

// ============================================
// Multi-Database Tests
// ============================================

async function testDataIsolationBetweenDatabases() {
    const db1 = generateDbName('isolation_db1');
    const db2 = generateDbName('isolation_db2');

    await client.createDatabase(db1);
    await client.createDatabase(db2);

    const collName = 'shared_collection';
    await client.createCollection(collName, { database: db1 });
    await client.createCollection(collName, { database: db2 });

    await client.insert(collName, { db: 'db1', value: 100 }, { database: db1 });
    await client.insert(collName, { db: 'db2', value: 200 }, { database: db2 });

    const docs1 = await client.query(collName, {}, { database: db1 });
    const docs2 = await client.query(collName, {}, { database: db2 });

    assert(docs1.length === 1, 'DB1 should have 1 document');
    assert(docs2.length === 1, 'DB2 should have 1 document');
    assert(docs1[0].value === 100, 'DB1 data incorrect');
    assert(docs2[0].value === 200, 'DB2 data incorrect');

    await client.dropDatabase(db1);
    await client.dropDatabase(db2);
}

// ============================================
// Error Handling Tests
// ============================================

async function testNonExistentDatabaseError() {
    try {
        await client.dropDatabase('nonexistent_db_12345');
        throw new Error('Should have thrown error for non-existent database');
    } catch (error) {
        assert(error.message.includes('not found') || error.message.includes('does not exist'),
            'Error message should indicate database not found');
    }
}

async function testNonExistentCollectionError() {
    const dbName = generateDbName('error_db');
    await client.createDatabase(dbName);

    try {
        await client.query('nonexistent_collection', {}, { database: dbName });
        throw new Error('Should have thrown error for non-existent collection');
    } catch (error) {
        assert(error.message.includes('not found') || error.message.includes('does not exist'),
            'Error message should indicate collection not found');
    } finally {
        await client.dropDatabase(dbName);
    }
}

// ============================================
// Main Test Runner
// ============================================

async function runAllTests() {
    console.log('🚀 Starting JavaScript Client Tests for NexaDB v3.0.0\n');
    console.log(`📡 Connecting to ${TEST_HOST}:${TEST_PORT}...`);

    try {
        client = new NexaClient({ host: TEST_HOST, port: TEST_PORT });
        console.log('✅ Connected successfully\n');
    } catch (error) {
        console.error('❌ Failed to connect to NexaDB:', error.message);
        process.exit(1);
    }

    console.log('═══ Database Operations Tests ═══');
    await runTest('Create database', testCreateDatabase);
    await runTest('List databases', testListDatabases);
    await runTest('Get database stats', testGetDatabaseStats);
    await runTest('Drop database', testDropDatabase);

    console.log('\n═══ Collection Operations Tests ═══');
    await runTest('Create collection', testCreateCollection);
    await runTest('List collections', testListCollections);
    await runTest('Drop collection', testDropCollection);

    console.log('\n═══ Document CRUD Operations Tests ═══');
    await runTest('Insert document', testInsertDocument);
    await runTest('Query documents', testQueryDocuments);
    await runTest('Update document', testUpdateDocument);
    await runTest('Delete document', testDeleteDocument);

    console.log('\n═══ Vector Operations Tests ═══');
    await runTest('Create vector collection', testCreateVectorCollection);
    await runTest('Insert vector document', testInsertVectorDocument);
    await runTest('Build HNSW index', testBuildHNSWIndex);
    await runTest('Vector search', testVectorSearch);

    console.log('\n═══ TOON Format Tests ═══');
    await runTest('Query with TOON format', testQueryWithTOONFormat);

    console.log('\n═══ Multi-Database Tests ═══');
    await runTest('Data isolation between databases', testDataIsolationBetweenDatabases);

    console.log('\n═══ Error Handling Tests ═══');
    await runTest('Non-existent database error', testNonExistentDatabaseError);
    await runTest('Non-existent collection error', testNonExistentCollectionError);

    // Summary
    console.log('\n' + '═'.repeat(50));
    console.log('📊 Test Summary');
    console.log('═'.repeat(50));
    console.log(`✅ Passed: ${testsPassed}`);
    console.log(`❌ Failed: ${testsFailed}`);
    console.log(`📈 Total:  ${testsPassed + testsFailed}`);

    if (testsFailed === 0) {
        console.log('\n🎉 All tests passed!');
        process.exit(0);
    } else {
        console.log('\n⚠️  Some tests failed');
        process.exit(1);
    }
}

// Run tests
runAllTests().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
});
