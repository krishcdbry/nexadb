/**
 * YCSB DB Interface
 *
 * This is the core abstract class that database bindings must extend.
 * Copied from YCSB project for standalone compilation.
 */
package site.ycsb;

import java.util.*;

public abstract class DB {

    private Properties properties = new Properties();

    /**
     * Set the properties for this DB.
     */
    public void setProperties(Properties p) {
        properties = p;
    }

    /**
     * Get the set of properties for this DB.
     */
    public Properties getProperties() {
        return properties;
    }

    /**
     * Initialize any state for this DB.
     * Called once per DB instance; there is one DB instance per client thread.
     */
    public void init() throws DBException {
    }

    /**
     * Cleanup any state for this DB.
     * Called once per DB instance; there is one DB instance per client thread.
     */
    public void cleanup() throws DBException {
    }

    /**
     * Read a record from the database. Each field/value pair from the result
     * will be stored in a HashMap.
     *
     * @param table  The name of the table
     * @param key    The record key of the record to read
     * @param fields The list of fields to read, or null for all of them
     * @param result A HashMap of field/value pairs for the result
     * @return The result of the operation
     */
    public abstract Status read(String table, String key, Set<String> fields,
                                Map<String, ByteIterator> result);

    /**
     * Perform a range scan for a set of records in the database. Each
     * field/value pair from the result will be stored in a HashMap.
     *
     * @param table       The name of the table
     * @param startkey    The record key of the first record to read
     * @param recordcount The number of records to read
     * @param fields      The list of fields to read, or null for all of them
     * @param result      A Vector of HashMaps, where each HashMap is a set
     *                    field/value pairs for one record
     * @return The result of the operation
     */
    public abstract Status scan(String table, String startkey, int recordcount,
                                Set<String> fields,
                                Vector<HashMap<String, ByteIterator>> result);

    /**
     * Update a record in the database. Any field/value pairs in the specified
     * values HashMap will be written into the record with the specified record
     * key, overwriting any existing values with the same field name.
     *
     * @param table  The name of the table
     * @param key    The record key of the record to write
     * @param values A HashMap of field/value pairs to update in the record
     * @return The result of the operation
     */
    public abstract Status update(String table, String key,
                                  Map<String, ByteIterator> values);

    /**
     * Insert a record in the database. Any field/value pairs in the specified
     * values HashMap will be written into the record with the specified record
     * key.
     *
     * @param table  The name of the table
     * @param key    The record key of the record to insert
     * @param values A HashMap of field/value pairs to insert in the record
     * @return The result of the operation
     */
    public abstract Status insert(String table, String key,
                                  Map<String, ByteIterator> values);

    /**
     * Delete a record from the database.
     *
     * @param table The name of the table
     * @param key   The record key of the record to delete
     * @return The result of the operation
     */
    public abstract Status delete(String table, String key);
}
