# Homebrew Formula for NexaDB
# Install with: brew install nexadb

class Nexadb < Formula
  include Language::Python::Virtualenv

  desc "Zero-dependency LSM-Tree database with vector search - The database for quick apps"
  homepage "https://github.com/krishcdbry/nexadb"
  url "https://github.com/krishcdbry/nexadb/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "5058886298767c3130c084aaa82bdeb2fc2c867160175960b83753c1a94680f6"
  license "MIT"
  head "https://github.com/krishcdbry/nexadb.git", branch: "main"

  # Python 3.8+ required
  depends_on "python@3"

  def install
    # Use system Python3 (works with any version)
    python3 = which("python3")

    # Install Python files
    libexec.install Dir["*.py"]
    libexec.install Dir["*.html"]

    # Create bin directory
    bin.mkpath

    # Create wrapper scripts
    (bin/"nexadb-server").write <<~EOS
      #!/bin/bash
      PYTHONPATH="#{libexec}" exec "#{python3}" "#{libexec}/nexadb_server.py" "$@"
    EOS
    (bin/"nexadb-server").chmod 0755

    (bin/"nexadb-admin").write <<~EOS
      #!/bin/bash
      PYTHONPATH="#{libexec}" exec "#{python3}" "#{libexec}/nexadb_admin_server.py" "$@"
    EOS
    (bin/"nexadb-admin").chmod 0755

    # Main nexadb command
    (bin/"nexadb").write <<~EOS
#!/bin/bash

case "$1" in
  start|server)
    shift
    PYTHONPATH="#{libexec}" exec "#{python3}" "#{libexec}/nexadb_server.py" "$@"
    ;;
  admin|ui)
    shift
    PYTHONPATH="#{libexec}" exec "#{python3}" "#{libexec}/nexadb_admin_server.py" "$@"
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

Learn more: https://github.com/krishcdbry/nexadb
HELP
    ;;
esac
    EOS
    (bin/"nexadb").chmod 0755
  end

  def post_install
    # Auto-add Homebrew to PATH if not already present
    shell_rc = if ENV["SHELL"]&.include?("zsh")
      "#{ENV["HOME"]}/.zshrc"
    else
      "#{ENV["HOME"]}/.bash_profile"
    end

    homebrew_path = "export PATH=\"#{HOMEBREW_PREFIX}/bin:$PATH\""

    if File.exist?(shell_rc)
      content = File.read(shell_rc)
      unless content.include?("#{HOMEBREW_PREFIX}/bin")
        File.open(shell_rc, "a") do |f|
          f.puts "\n# Added by NexaDB"
          f.puts homebrew_path
        end
        ohai "Added Homebrew to PATH in #{shell_rc}"
        ohai "Run: source #{shell_rc}"
      end
    end
  end

  def caveats
    <<~EOS
      🎉 NexaDB installed successfully!

      Quick Start (run in new terminal or source your shell config):
        nexadb start        Start database server
        nexadb admin        Start admin UI

      If 'nexadb' command not found, run:
        source ~/.zshrc     (or source ~/.bash_profile)

      Or simply open a new terminal window.

      Documentation: https://github.com/krishcdbry/nexadb

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
