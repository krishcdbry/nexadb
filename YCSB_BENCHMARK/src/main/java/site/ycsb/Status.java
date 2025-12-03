/**
 * YCSB Status
 *
 * Return codes for database operations.
 */
package site.ycsb;

public class Status {

    private final String name;
    private final String description;

    private Status(String name, String description) {
        this.name = name;
        this.description = description;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    @Override
    public String toString() {
        return name;
    }

    /**
     * The operation completed successfully.
     */
    public static final Status OK = new Status("OK", "Operation completed successfully");

    /**
     * The operation failed.
     */
    public static final Status ERROR = new Status("ERROR", "Operation failed");

    /**
     * The requested record was not found.
     */
    public static final Status NOT_FOUND = new Status("NOT_FOUND", "Record not found");

    /**
     * The operation was not implemented.
     */
    public static final Status NOT_IMPLEMENTED = new Status("NOT_IMPLEMENTED", "Operation not implemented");

    /**
     * The operation was forbidden.
     */
    public static final Status FORBIDDEN = new Status("FORBIDDEN", "Operation forbidden");

    /**
     * A service is unavailable.
     */
    public static final Status SERVICE_UNAVAILABLE = new Status("SERVICE_UNAVAILABLE", "Service unavailable");

    /**
     * An unexpected state was encountered.
     */
    public static final Status UNEXPECTED_STATE = new Status("UNEXPECTED_STATE", "Unexpected state");

    /**
     * The operation was batched.
     */
    public static final Status BATCHED_OK = new Status("BATCHED_OK", "Operation batched");
}
