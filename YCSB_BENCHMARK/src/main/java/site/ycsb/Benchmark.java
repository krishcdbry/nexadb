/**
 * Simple YCSB-style Benchmark Runner for NexaDB
 *
 * This is a standalone benchmark that mimics YCSB workloads.
 * Use this for quick testing without the full YCSB installation.
 *
 * Usage:
 *   java -cp "target/classes:target/dependency/*" site.ycsb.Benchmark [options]
 *
 * Options:
 *   -load              Run load phase only
 *   -run               Run benchmark phase only
 *   -records N         Number of records (default: 10000)
 *   -operations N      Number of operations (default: 10000)
 *   -threads N         Number of threads (default: 1)
 *   -workload X        Workload type: a, b, c, d, e, f (default: a)
 */
package site.ycsb;

import site.ycsb.db.NexaDBClient;

import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class Benchmark {

    // Configuration
    private int recordCount = 10000;
    private int operationCount = 10000;
    private int threadCount = 1;
    private String workload = "a";
    private boolean loadPhase = true;
    private boolean runPhase = true;

    // Workload ratios
    private double readProportion = 0.5;
    private double updateProportion = 0.5;
    private double insertProportion = 0.0;
    private double scanProportion = 0.0;

    // Statistics
    private final AtomicLong totalOps = new AtomicLong(0);
    private final AtomicLong readOps = new AtomicLong(0);
    private final AtomicLong updateOps = new AtomicLong(0);
    private final AtomicLong insertOps = new AtomicLong(0);
    private final AtomicLong scanOps = new AtomicLong(0);
    private final AtomicLong errors = new AtomicLong(0);

    private final List<Long> readLatencies = Collections.synchronizedList(new ArrayList<>());
    private final List<Long> updateLatencies = Collections.synchronizedList(new ArrayList<>());
    private final List<Long> insertLatencies = Collections.synchronizedList(new ArrayList<>());

    private final Random random = new Random();

    public static void main(String[] args) {
        Benchmark benchmark = new Benchmark();
        benchmark.parseArgs(args);
        benchmark.run();
    }

    private void parseArgs(String[] args) {
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "-load":
                    loadPhase = true;
                    runPhase = false;
                    break;
                case "-run":
                    loadPhase = false;
                    runPhase = true;
                    break;
                case "-records":
                    recordCount = Integer.parseInt(args[++i]);
                    break;
                case "-operations":
                    operationCount = Integer.parseInt(args[++i]);
                    break;
                case "-threads":
                    threadCount = Integer.parseInt(args[++i]);
                    break;
                case "-workload":
                    workload = args[++i];
                    break;
            }
        }

        // Set workload proportions
        switch (workload.toLowerCase()) {
            case "a": // Update heavy: 50/50
                readProportion = 0.5;
                updateProportion = 0.5;
                break;
            case "b": // Read mostly: 95/5
                readProportion = 0.95;
                updateProportion = 0.05;
                break;
            case "c": // Read only: 100/0
                readProportion = 1.0;
                updateProportion = 0.0;
                break;
            case "d": // Read latest
                readProportion = 0.95;
                insertProportion = 0.05;
                break;
            case "e": // Short ranges
                scanProportion = 0.95;
                insertProportion = 0.05;
                break;
            case "f": // Read-modify-write
                readProportion = 0.5;
                updateProportion = 0.5;
                break;
        }
    }

    private void run() {
        printHeader();

        if (loadPhase) {
            runLoadPhase();
        }

        if (runPhase) {
            runBenchmarkPhase();
        }

        printResults();
    }

    private void printHeader() {
        System.out.println("=".repeat(70));
        System.out.println("NexaDB YCSB Benchmark");
        System.out.println("=".repeat(70));
        System.out.println("Records:      " + recordCount);
        System.out.println("Operations:   " + operationCount);
        System.out.println("Threads:      " + threadCount);
        System.out.println("Workload:     " + workload.toUpperCase());
        System.out.println("Read/Update:  " + (readProportion * 100) + "/" + (updateProportion * 100));
        System.out.println("=".repeat(70));
    }

    private void runLoadPhase() {
        System.out.println("\n[LOAD] Loading " + recordCount + " records...");

        long startTime = System.currentTimeMillis();
        ExecutorService executor = Executors.newFixedThreadPool(threadCount);

        int recordsPerThread = recordCount / threadCount;

        for (int t = 0; t < threadCount; t++) {
            final int threadId = t;
            final int startRecord = t * recordsPerThread;
            final int endRecord = (t == threadCount - 1) ? recordCount : startRecord + recordsPerThread;

            executor.submit(() -> {
                try {
                    NexaDBClient client = createClient();
                    client.init();

                    for (int i = startRecord; i < endRecord; i++) {
                        String key = String.format("user%010d", i);
                        Map<String, ByteIterator> values = createRecord();

                        long opStart = System.nanoTime();
                        Status status = client.insert("usertable", key, values);
                        long opEnd = System.nanoTime();

                        if (status == Status.OK) {
                            insertOps.incrementAndGet();
                            insertLatencies.add((opEnd - opStart) / 1000); // microseconds
                        } else {
                            errors.incrementAndGet();
                        }

                        totalOps.incrementAndGet();

                        if (totalOps.get() % 1000 == 0) {
                            System.out.print("\r[LOAD] " + totalOps.get() + "/" + recordCount + " records");
                        }
                    }

                    client.cleanup();
                } catch (Exception e) {
                    System.err.println("Load error: " + e.getMessage());
                }
            });
        }

        executor.shutdown();
        try {
            executor.awaitTermination(1, TimeUnit.HOURS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        long endTime = System.currentTimeMillis();
        double seconds = (endTime - startTime) / 1000.0;
        double throughput = recordCount / seconds;

        System.out.println("\n[LOAD] Complete!");
        System.out.printf("[LOAD] Time: %.2f seconds\n", seconds);
        System.out.printf("[LOAD] Throughput: %.2f ops/sec\n", throughput);

        // Reset counters for run phase
        totalOps.set(0);
        insertOps.set(0);
    }

    private void runBenchmarkPhase() {
        System.out.println("\n[RUN] Running " + operationCount + " operations...");

        // Reset stats
        readLatencies.clear();
        updateLatencies.clear();
        insertLatencies.clear();

        long startTime = System.currentTimeMillis();
        ExecutorService executor = Executors.newFixedThreadPool(threadCount);

        int opsPerThread = operationCount / threadCount;

        for (int t = 0; t < threadCount; t++) {
            final int threadOps = (t == threadCount - 1) ?
                operationCount - (t * opsPerThread) : opsPerThread;

            executor.submit(() -> {
                try {
                    NexaDBClient client = createClient();
                    client.init();

                    for (int i = 0; i < threadOps; i++) {
                        doOperation(client);

                        if (totalOps.get() % 1000 == 0) {
                            System.out.print("\r[RUN] " + totalOps.get() + "/" + operationCount + " ops");
                        }
                    }

                    client.cleanup();
                } catch (Exception e) {
                    System.err.println("Run error: " + e.getMessage());
                }
            });
        }

        executor.shutdown();
        try {
            executor.awaitTermination(1, TimeUnit.HOURS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        long endTime = System.currentTimeMillis();
        double seconds = (endTime - startTime) / 1000.0;
        double throughput = operationCount / seconds;

        System.out.println("\n[RUN] Complete!");
        System.out.printf("[RUN] Time: %.2f seconds\n", seconds);
        System.out.printf("[RUN] Throughput: %.2f ops/sec\n", throughput);
    }

    private void doOperation(NexaDBClient client) {
        double rand = random.nextDouble();
        String key = String.format("user%010d", random.nextInt(recordCount));

        if (rand < readProportion) {
            // Read
            Map<String, ByteIterator> result = new HashMap<>();
            long opStart = System.nanoTime();
            Status status = client.read("usertable", key, null, result);
            long opEnd = System.nanoTime();

            if (status == Status.OK || status == Status.NOT_FOUND) {
                readOps.incrementAndGet();
                readLatencies.add((opEnd - opStart) / 1000);
            } else {
                errors.incrementAndGet();
            }
        } else if (rand < readProportion + updateProportion) {
            // Update
            Map<String, ByteIterator> values = new HashMap<>();
            values.put("field0", new StringByteIterator(randomString(100)));

            long opStart = System.nanoTime();
            Status status = client.update("usertable", key, values);
            long opEnd = System.nanoTime();

            if (status == Status.OK) {
                updateOps.incrementAndGet();
                updateLatencies.add((opEnd - opStart) / 1000);
            } else {
                errors.incrementAndGet();
            }
        } else if (rand < readProportion + updateProportion + insertProportion) {
            // Insert
            String newKey = String.format("user%010d", recordCount + insertOps.get());
            Map<String, ByteIterator> values = createRecord();

            long opStart = System.nanoTime();
            Status status = client.insert("usertable", newKey, values);
            long opEnd = System.nanoTime();

            if (status == Status.OK) {
                insertOps.incrementAndGet();
                insertLatencies.add((opEnd - opStart) / 1000);
            } else {
                errors.incrementAndGet();
            }
        } else {
            // Scan
            Vector<HashMap<String, ByteIterator>> result = new Vector<>();
            long opStart = System.nanoTime();
            Status status = client.scan("usertable", key, 10, null, result);
            long opEnd = System.nanoTime();

            if (status == Status.OK) {
                scanOps.incrementAndGet();
                readLatencies.add((opEnd - opStart) / 1000);
            } else {
                errors.incrementAndGet();
            }
        }

        totalOps.incrementAndGet();
    }

    private Map<String, ByteIterator> createRecord() {
        Map<String, ByteIterator> values = new HashMap<>();
        for (int i = 0; i < 10; i++) {
            values.put("field" + i, new StringByteIterator(randomString(100)));
        }
        return values;
    }

    private String randomString(int length) {
        StringBuilder sb = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            sb.append((char) ('a' + random.nextInt(26)));
        }
        return sb.toString();
    }

    private NexaDBClient createClient() {
        NexaDBClient client = new NexaDBClient();
        Properties props = new Properties();
        props.setProperty("nexadb.host", "localhost");
        props.setProperty("nexadb.port", "6970");
        props.setProperty("nexadb.username", "root");
        props.setProperty("nexadb.password", "nexadb123");
        client.setProperties(props);
        return client;
    }

    private void printResults() {
        System.out.println("\n" + "=".repeat(70));
        System.out.println("RESULTS");
        System.out.println("=".repeat(70));

        System.out.printf("[OVERALL], Operations, %d\n", totalOps.get());
        System.out.printf("[OVERALL], Errors, %d\n", errors.get());

        if (!readLatencies.isEmpty()) {
            printLatencyStats("READ", readOps.get(), readLatencies);
        }

        if (!updateLatencies.isEmpty()) {
            printLatencyStats("UPDATE", updateOps.get(), updateLatencies);
        }

        if (!insertLatencies.isEmpty()) {
            printLatencyStats("INSERT", insertOps.get(), insertLatencies);
        }

        if (scanOps.get() > 0) {
            System.out.printf("[SCAN], Operations, %d\n", scanOps.get());
        }

        System.out.println("=".repeat(70));
    }

    private void printLatencyStats(String operation, long count, List<Long> latencies) {
        if (latencies.isEmpty()) return;

        Collections.sort(latencies);
        long sum = latencies.stream().mapToLong(Long::longValue).sum();
        double avg = sum / (double) latencies.size();
        long min = latencies.get(0);
        long max = latencies.get(latencies.size() - 1);
        long p50 = latencies.get((int) (latencies.size() * 0.50));
        long p95 = latencies.get((int) (latencies.size() * 0.95));
        long p99 = latencies.get((int) (latencies.size() * 0.99));

        System.out.printf("[%s], Operations, %d\n", operation, count);
        System.out.printf("[%s], AverageLatency(us), %.2f\n", operation, avg);
        System.out.printf("[%s], MinLatency(us), %d\n", operation, min);
        System.out.printf("[%s], MaxLatency(us), %d\n", operation, max);
        System.out.printf("[%s], 50thPercentileLatency(us), %d\n", operation, p50);
        System.out.printf("[%s], 95thPercentileLatency(us), %d\n", operation, p95);
        System.out.printf("[%s], 99thPercentileLatency(us), %d\n", operation, p99);
    }
}
