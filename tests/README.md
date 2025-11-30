# NexaDB v3.0.0 Test Suite

Comprehensive test suite for NexaDB v3.0.0, covering all features including multi-database support, vector operations, TOON format, and authentication.

## Test Structure

```
tests/
├── conftest.py                           # pytest configuration and fixtures
├── unit/                                 # Unit tests
│   ├── test_database_operations.py       # Database CRUD tests
│   ├── test_vector_operations.py         # Vector indexing and search tests
│   ├── test_toon_operations.py           # TOON format tests
│   ├── test_auth.py                      # Authentication and authorization tests
│   └── test_rest_api.py                  # REST API endpoint tests
├── integration/                          # Integration tests
│   └── test_multi_database_workflows.py  # Multi-database scenarios
├── cli/                                  # CLI tests
│   ├── test_cli_commands.sh              # Shell script testing CLI commands
│   └── test_server_commands.sh           # Server lifecycle commands (start, stop, etc.)
├── clients/                              # Client library tests
│   ├── test_javascript_client.js         # JavaScript/Node.js client tests
│   └── test_python_client.py             # Python client tests
├── admin_panel/                          # Admin panel tests
│   └── test_admin_api.py                 # Admin panel API endpoint tests
├── performance/                          # Performance tests (to be created)
└── security/                             # Security tests (to be created)
```

## Prerequisites

### For Python Tests
```bash
pip3 install pytest pytest-cov nexadb_client requests
```

### For JavaScript Tests
```bash
npm install nexadb-js
```

### For CLI Tests
- NexaDB CLI installed (`nexadb` command available)
- Bash shell

## Running Tests

### Run All Unit Tests
```bash
# Run all pytest-based tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=nexadb --cov-report=html
```

### Run Specific Test Files
```bash
# Database operations
pytest tests/unit/test_database_operations.py -v

# Vector operations
pytest tests/unit/test_vector_operations.py -v

# TOON format
pytest tests/unit/test_toon_operations.py -v

# Authentication
pytest tests/unit/test_auth.py -v

# REST API
pytest tests/unit/test_rest_api.py -v
```

### Run Integration Tests
```bash
pytest tests/integration/ -v
```

### Run Admin Panel Tests
```bash
# Start admin server first
python3 admin_server.py &

# Run admin panel API tests
pytest tests/admin_panel/test_admin_api.py -v
```

### Run CLI Tests
```bash
# Make sure NexaDB server is NOT running
./tests/cli/test_cli_commands.sh

# Test server lifecycle commands
./tests/cli/test_server_commands.sh
```

### Run Client Library Tests

**Python Client:**
```bash
# Start NexaDB binary server first
python3 nexadb_binary_server.py &

# Run Python client tests
python3 tests/clients/test_python_client.py
```

**JavaScript Client:**
```bash
# Start NexaDB binary server first
python3 nexadb_binary_server.py &

# Run JavaScript client tests
node tests/clients/test_javascript_client.js
```

## Test Configuration

### Environment Variables

- `NEXADB_TEST_HOST`: Host for test server (default: `localhost`)
- `NEXADB_TEST_PORT`: Port for test server (default: `6970`)

Example:
```bash
export NEXADB_TEST_HOST=localhost
export NEXADB_TEST_PORT=6970
pytest tests/unit/
```

## Test Coverage Goals

- **Unit Tests**: ≥80% code coverage
- **Integration Tests**: ≥70% workflow coverage
- **Client Libraries**: 100% API coverage
- **CLI Commands**: 100% command coverage

## Writing New Tests

### Adding Unit Tests

1. Create test file in `tests/unit/`
2. Import `conftest` fixtures:
   ```python
   from tests.conftest import client, test_database, test_collection
   ```

3. Use fixtures in test functions:
   ```python
   def test_my_feature(client, test_database):
       # Test code here
       pass
   ```

### Adding Integration Tests

1. Create test file in `tests/integration/`
2. Use `client` fixture for multi-step workflows
3. Test complex scenarios involving multiple databases/collections

### Adding CLI Tests

1. Add test cases to `tests/cli/test_cli_commands.sh`
2. Use `run_test` helper function:
   ```bash
   run_test "Test description" \
       "$NEXADB_BIN command --args" \
       "expected_output_substring"
   ```

## Continuous Integration

Tests are designed to run in CI/CD pipelines. Recommended workflow:

```yaml
# Example GitHub Actions workflow
- name: Install dependencies
  run: pip3 install pytest pytest-cov nexadb_client

- name: Start test server
  run: python3 nexadb_binary_server.py &

- name: Run unit tests
  run: pytest tests/unit/ --cov --cov-report=xml

- name: Run integration tests
  run: pytest tests/integration/ -v

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Test Fixtures

### Available Fixtures (from conftest.py)

- **`start_server`**: Session-scoped server startup/teardown
- **`client`**: Function-scoped NexaDB client connection
- **`test_database`**: Auto-cleanup test database
- **`test_collection`**: Auto-cleanup test collection in test database

### Helper Functions

- **`generate_test_documents(count=10)`**: Generate test documents
- **`generate_test_vector(dimensions=768)`**: Generate random test vector

## Troubleshooting

### Tests Fail to Connect

**Issue**: Tests cannot connect to NexaDB server

**Solution**:
```bash
# Start the binary server
python3 nexadb_binary_server.py &

# Wait a few seconds
sleep 3

# Run tests
pytest tests/unit/
```

### Port Already in Use

**Issue**: Test server cannot start due to port conflict

**Solution**:
```bash
# Find and kill existing NexaDB processes
lsof -ti:6970 | xargs kill -9

# Or use a different port
export NEXADB_TEST_PORT=6971
pytest tests/unit/
```

### CLI Tests Fail

**Issue**: CLI tests cannot find `nexadb` command

**Solution**:
```bash
# Install NexaDB CLI
pip3 install nexadb

# Or use full path
NEXADB_BIN=/path/to/nexadb ./tests/cli/test_cli_commands.sh
```

## Test Results

After running tests, results are available:

- **Console Output**: Pass/fail status for each test
- **Coverage Report**: `htmlcov/index.html` (if using `--cov-report=html`)
- **JUnit XML**: For CI integration (use `--junit-xml=results.xml`)

## Performance Benchmarks

Performance tests validate:
- Insert throughput: ≥10,000 docs/sec
- Query latency: <50ms for simple queries
- Vector search: <500ms for 100K vectors

Run performance tests:
```bash
pytest tests/performance/ -v
```

## Security Tests

Security tests validate:
- Authentication mechanisms
- Authorization and permissions
- Data isolation between databases
- API key security

Run security tests:
```bash
pytest tests/security/ -v
```

## Contributing

When adding new features to NexaDB:
1. Write unit tests first (TDD approach)
2. Ensure tests pass locally
3. Update test documentation
4. Add integration tests for complex workflows
5. Verify CI pipeline passes

## Support

For test-related issues:
- Check the [Testing Plan](../TESTING_PLAN_v3.0.0.md)
- Review fixture documentation in `conftest.py`
- Open an issue on GitHub
