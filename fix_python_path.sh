#!/bin/bash
# Fix Python path in NexaDB scripts

set -e

echo "🔧 Fixing Python path in NexaDB scripts..."

# Fix nexadb
cat > /opt/homebrew/Cellar/nexadb/1.0.0/bin/nexadb << 'EOF'
#!/bin/bash

case "$1" in
  start|server)
    shift
    PYTHONPATH="/opt/homebrew/Cellar/nexadb/1.0.0/libexec" exec "/opt/homebrew/opt/python@3.11/bin/python3.11" "/opt/homebrew/Cellar/nexadb/1.0.0/libexec/nexadb_server.py" "$@"
    ;;
  admin|ui)
    shift
    PYTHONPATH="/opt/homebrew/Cellar/nexadb/1.0.0/libexec" exec "/opt/homebrew/opt/python@3.11/bin/python3.11" "/opt/homebrew/Cellar/nexadb/1.0.0/libexec/nexadb_admin_server.py" "$@"
    ;;
  --version|-v)
    echo "NexaDB v1.0.0"
    ;;
  --help|-h|help|*)
    cat <<HELP
NexaDB - The database for quick apps

Usage:
  nexadb start          Start database server (port 6969)
  nexadb admin          Start admin UI (port 9999)
  nexadb --version      Show version
  nexadb --help         Show this help

Commands:
  nexadb-server         Start database server
  nexadb-admin          Start admin UI

Examples:
  nexadb start                    # Start server
  nexadb admin                    # Start admin UI
  nexadb-server --port 8080       # Custom port
  nexadb-admin --host 0.0.0.0     # Bind to all interfaces

Learn more: https://github.com/krishcdbry/nexadb
HELP
    ;;
esac
EOF

# Fix nexadb-server
cat > /opt/homebrew/Cellar/nexadb/1.0.0/bin/nexadb-server << 'EOF'
#!/bin/bash
PYTHONPATH="/opt/homebrew/Cellar/nexadb/1.0.0/libexec" exec "/opt/homebrew/opt/python@3.11/bin/python3.11" "/opt/homebrew/Cellar/nexadb/1.0.0/libexec/nexadb_server.py" "$@"
EOF

# Fix nexadb-admin
cat > /opt/homebrew/Cellar/nexadb/1.0.0/bin/nexadb-admin << 'EOF'
#!/bin/bash
PYTHONPATH="/opt/homebrew/Cellar/nexadb/1.0.0/libexec" exec "/opt/homebrew/opt/python@3.11/bin/python3.11" "/opt/homebrew/Cellar/nexadb/1.0.0/libexec/nexadb_admin_server.py" "$@"
EOF

# Make executable
chmod +x /opt/homebrew/Cellar/nexadb/1.0.0/bin/nexadb
chmod +x /opt/homebrew/Cellar/nexadb/1.0.0/bin/nexadb-server
chmod +x /opt/homebrew/Cellar/nexadb/1.0.0/bin/nexadb-admin

echo "✅ Fixed! Now try:"
echo "  nexadb start"
