# Homebrew Formula for NexaDB
# Install with: brew install nexadb

class Nexadb < Formula
  include Language::Python::Virtualenv

  desc "Zero-dependency LSM-Tree database with vector search - The database for quick apps"
  homepage "https://github.com/krishcdbry/nexadb"
  url "https://github.com/krishcdbry/nexadb/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "YOUR_SHA256_HASH_HERE"  # Generate after creating release
  license "MIT"
  head "https://github.com/krishcdbry/nexadb.git", branch: "main"

  # Python 3.8+ required
  depends_on "python@3.11"

  def install
    # Install Python files
    libexec.install Dir["*.py"]
    libexec.install Dir["*.html"]

    # Create bin directory
    bin.mkpath

    # Create wrapper scripts
    (bin/"nexadb-server").write <<~EOS
      #!/bin/bash
      PYTHONPATH="#{libexec}" exec "#{Formula["python@3.11"].opt_bin}/python3" "#{libexec}/nexadb_server.py" "$@"
    EOS

    (bin/"nexadb-admin").write <<~EOS
      #!/bin/bash
      PYTHONPATH="#{libexec}" exec "#{Formula["python@3.11"].opt_bin}/python3" "#{libexec}/nexadb_admin_server.py" "$@"
    EOS

    # Main nexadb command
    (bin/"nexadb").write <<~EOS
      #!/bin/bash

      case "$1" in
        start|server)
          shift
          PYTHONPATH="#{libexec}" exec "#{Formula["python@3.11"].opt_bin}/python3" "#{libexec}/nexadb_server.py" "$@"
          ;;
        admin|ui)
          shift
          PYTHONPATH="#{libexec}" exec "#{Formula["python@3.11"].opt_bin}/python3" "#{libexec}/nexadb_admin_server.py" "$@"
          ;;
        --version|-v)
          echo "NexaDB v#{version}"
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

Learn more: https://github.com/yourusername/nexadb
HELP
          ;;
      esac
    EOS

    # Make scripts executable
    chmod 0755, bin/"nexadb"
    chmod 0755, bin/"nexadb-server"
    chmod 0755, bin/"nexadb-admin"
  end

  def caveats
    <<~EOS
      🎉 NexaDB installed successfully!

      Quick Start:
        1. Start database:  nexadb start
        2. Start admin UI:  nexadb admin
        3. Open browser:    http://localhost:9999

      Commands:
        nexadb start        Start database server (port 6969)
        nexadb admin        Start admin UI (port 9999)
        nexadb --help       Show all commands

      Documentation:
        Homepage: https://github.com/yourusername/nexadb
        Docs:     https://github.com/yourusername/nexadb#readme

      Connect from your app:
        npm install nexadb-client
        pip install nexadb-client

      Happy building! 🚀
    EOS
  end

  test do
    # Test that files exist
    assert_predicate libexec/"nexadb_server.py", :exist?
    assert_predicate libexec/"veloxdb_core.py", :exist?

    # Test that commands work
    assert_match "NexaDB", shell_output("#{bin}/nexadb --version")
    assert_match "Usage:", shell_output("#{bin}/nexadb --help")
  end
end
