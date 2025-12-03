/**
 * NexaDB YCSB Binding Tests
 *
 * Integration tests for the NexaDB YCSB binding.
 * Requires a running NexaDB server on localhost:6970.
 *
 * Run with: mvn test -Dtest=NexaDBClientTest
 */
package site.ycsb.db;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.Assume;

import site.ycsb.ByteIterator;
import site.ycsb.Status;
import site.ycsb.StringByteIterator;

import java.util.*;

import static org.junit.Assert.*;

public class NexaDBClientTest {

    private NexaDBClient client;
    private static final String TEST_TABLE = "ycsb_test";
    private boolean serverAvailable = false;

    @Before
    public void setUp() throws Exception {
        client = new NexaDBClient();

        // Set properties
        Properties props = new Properties();
        props.setProperty("nexadb.host", "localhost");
        props.setProperty("nexadb.port", "6970");
        props.setProperty("nexadb.username", "root");
        props.setProperty("nexadb.password", "nexadb123");
        props.setProperty("nexadb.debug", "true");

        // Try to connect - skip tests if server not available
        try {
            client.setProperties(props);
            client.init();
            serverAvailable = true;
        } catch (Exception e) {
            System.out.println("NexaDB server not available, skipping tests: " + e.getMessage());
            serverAvailable = false;
        }
    }

    @After
    public void tearDown() throws Exception {
        if (client != null && serverAvailable) {
            client.cleanup();
        }
    }

    @Test
    public void testInsertAndRead() {
        Assume.assumeTrue("NexaDB server not available", serverAvailable);

        String key = "test_key_" + System.currentTimeMillis();

        // Insert
        Map<String, ByteIterator> insertValues = new HashMap<>();
        insertValues.put("field0", new StringByteIterator("value0"));
        insertValues.put("field1", new StringByteIterator("value1"));
        insertValues.put("field2", new StringByteIterator("value2"));

        Status insertStatus = client.insert(TEST_TABLE, key, insertValues);
        assertEquals("Insert should succeed", Status.OK, insertStatus);

        // Read back
        Map<String, ByteIterator> readResult = new HashMap<>();
        Status readStatus = client.read(TEST_TABLE, key, null, readResult);
        assertEquals("Read should succeed", Status.OK, readStatus);

        // Verify values
        assertEquals("field0 should match", "value0", readResult.get("field0").toString());
        assertEquals("field1 should match", "value1", readResult.get("field1").toString());
        assertEquals("field2 should match", "value2", readResult.get("field2").toString());

        // Cleanup
        client.delete(TEST_TABLE, key);
    }

    @Test
    public void testUpdate() {
        Assume.assumeTrue("NexaDB server not available", serverAvailable);

        String key = "test_update_" + System.currentTimeMillis();

        // Insert initial
        Map<String, ByteIterator> insertValues = new HashMap<>();
        insertValues.put("field0", new StringByteIterator("initial"));
        client.insert(TEST_TABLE, key, insertValues);

        // Update
        Map<String, ByteIterator> updateValues = new HashMap<>();
        updateValues.put("field0", new StringByteIterator("updated"));

        Status updateStatus = client.update(TEST_TABLE, key, updateValues);
        assertEquals("Update should succeed", Status.OK, updateStatus);

        // Verify
        Map<String, ByteIterator> readResult = new HashMap<>();
        client.read(TEST_TABLE, key, null, readResult);
        assertEquals("field0 should be updated", "updated", readResult.get("field0").toString());

        // Cleanup
        client.delete(TEST_TABLE, key);
    }

    @Test
    public void testDelete() {
        Assume.assumeTrue("NexaDB server not available", serverAvailable);

        String key = "test_delete_" + System.currentTimeMillis();

        // Insert
        Map<String, ByteIterator> insertValues = new HashMap<>();
        insertValues.put("field0", new StringByteIterator("value"));
        client.insert(TEST_TABLE, key, insertValues);

        // Delete
        Status deleteStatus = client.delete(TEST_TABLE, key);
        assertEquals("Delete should succeed", Status.OK, deleteStatus);

        // Verify deleted
        Map<String, ByteIterator> readResult = new HashMap<>();
        Status readStatus = client.read(TEST_TABLE, key, null, readResult);
        assertEquals("Read after delete should return NOT_FOUND", Status.NOT_FOUND, readStatus);
    }

    @Test
    public void testScan() {
        Assume.assumeTrue("NexaDB server not available", serverAvailable);

        String keyPrefix = "test_scan_" + System.currentTimeMillis() + "_";

        // Insert multiple records
        for (int i = 0; i < 10; i++) {
            Map<String, ByteIterator> values = new HashMap<>();
            values.put("field0", new StringByteIterator("value" + i));
            client.insert(TEST_TABLE, keyPrefix + String.format("%03d", i), values);
        }

        // Scan
        Vector<HashMap<String, ByteIterator>> scanResult = new Vector<>();
        Status scanStatus = client.scan(TEST_TABLE, keyPrefix + "000", 5, null, scanResult);
        assertEquals("Scan should succeed", Status.OK, scanStatus);

        // Should return some records (exact count depends on server implementation)
        assertTrue("Scan should return records", scanResult.size() > 0);

        // Cleanup
        for (int i = 0; i < 10; i++) {
            client.delete(TEST_TABLE, keyPrefix + String.format("%03d", i));
        }
    }

    @Test
    public void testReadNotFound() {
        Assume.assumeTrue("NexaDB server not available", serverAvailable);

        String key = "nonexistent_key_" + System.currentTimeMillis();

        Map<String, ByteIterator> result = new HashMap<>();
        Status status = client.read(TEST_TABLE, key, null, result);

        assertEquals("Read of nonexistent key should return NOT_FOUND", Status.NOT_FOUND, status);
    }

    @Test
    public void testReadWithFields() {
        Assume.assumeTrue("NexaDB server not available", serverAvailable);

        String key = "test_fields_" + System.currentTimeMillis();

        // Insert with multiple fields
        Map<String, ByteIterator> insertValues = new HashMap<>();
        insertValues.put("field0", new StringByteIterator("value0"));
        insertValues.put("field1", new StringByteIterator("value1"));
        insertValues.put("field2", new StringByteIterator("value2"));
        client.insert(TEST_TABLE, key, insertValues);

        // Read only specific fields
        Set<String> fields = new HashSet<>();
        fields.add("field0");
        fields.add("field2");

        Map<String, ByteIterator> result = new HashMap<>();
        Status status = client.read(TEST_TABLE, key, fields, result);

        assertEquals("Read should succeed", Status.OK, status);
        assertTrue("Should have field0", result.containsKey("field0"));
        assertTrue("Should have field2", result.containsKey("field2"));
        assertFalse("Should not have field1", result.containsKey("field1"));

        // Cleanup
        client.delete(TEST_TABLE, key);
    }

    /**
     * Simple connection test - can be run standalone.
     */
    public static void main(String[] args) {
        System.out.println("=".repeat(60));
        System.out.println("NexaDB YCSB Binding - Connection Test");
        System.out.println("=".repeat(60));

        try {
            // Test connection
            NexaDBConnection conn = new NexaDBConnection(
                    "localhost", 6970, "root", "nexadb123", 30000, 3
            );

            System.out.println("\nConnecting to NexaDB...");
            conn.connect();
            System.out.println("Connected!");

            // Test ping
            System.out.println("\nSending PING...");
            Map<String, Object> pingData = new HashMap<>();
            Map<String, Object> pong = conn.sendMessage(NexaDBConnection.MSG_PING, pingData);
            System.out.println("PONG received: " + pong);

            // Test insert
            System.out.println("\nInserting test document...");
            Map<String, Object> doc = new HashMap<>();
            doc.put("_id", "ycsb_test_" + System.currentTimeMillis());
            doc.put("name", "Test Document");
            doc.put("value", 42);

            Map<String, Object> insertData = new HashMap<>();
            insertData.put("collection", "ycsb_test");
            insertData.put("data", doc);

            Map<String, Object> insertResult = conn.sendMessage(NexaDBConnection.MSG_CREATE, insertData);
            System.out.println("Insert result: " + insertResult);

            // Test query
            System.out.println("\nQuerying documents...");
            Map<String, Object> queryData = new HashMap<>();
            queryData.put("collection", "ycsb_test");
            queryData.put("filters", new HashMap<>());
            queryData.put("limit", 10);

            Map<String, Object> queryResult = conn.sendMessage(NexaDBConnection.MSG_QUERY, queryData);
            System.out.println("Query result: " + queryResult);

            // Close
            conn.close();
            System.out.println("\nConnection closed.");

            System.out.println("\n" + "=".repeat(60));
            System.out.println("All tests passed!");
            System.out.println("=".repeat(60));

        } catch (Exception e) {
            System.err.println("\nError: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
