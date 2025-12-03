/**
 * NexaDB Exception
 *
 * Base exception class for all NexaDB-related errors.
 */
package site.ycsb.db;

public class NexaDBException extends Exception {

    public NexaDBException(String message) {
        super(message);
    }

    public NexaDBException(String message, Throwable cause) {
        super(message, cause);
    }
}
