#!/bin/bash

# NexaDB Installation Script for Linux/Ubuntu
# Usage: curl -fsSL https://raw.githubusercontent.com/krishcdbry/nexadb/main/install.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# Banner
echo -e "${CYAN}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║     ███╗   ██╗███████╗██╗  ██╗ █████╗ ██████╗ ██████╗               ║"
echo "║     ████╗  ██║██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗██╔══██╗              ║"
echo "║     ██╔██╗ ██║█████╗   ╚███╔╝ ███████║██║  ██║██████╔╝              ║"
echo "║     ██║╚██╗██║██╔══╝   ██╔██╗ ██╔══██║██║  ██║██╔══██╗              ║"
echo "║     ██║ ╚████║███████╗██╔╝ ██╗██║  ██║██████╔╝██████╔╝              ║"
echo "║     ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝               ║"
echo "║                                                                       ║"
echo "║                   Database for AI Developers                         ║"
echo "║                          v2.2.11                                      ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo -e "${RESET}"

echo -e "${GREEN}Starting NexaDB installation...${RESET}\n"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo -e "${YELLOW}Warning: Running as root. It's recommended to run as a regular user.${RESET}"
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo -e "${RED}Cannot detect OS. Please install manually.${RESET}"
    exit 1
fi

echo -e "${CYAN}Detected OS: $OS${RESET}"

# Install dependencies
echo -e "\n${BOLD}[1/5] Installing dependencies...${RESET}"

# Check if we need sudo
SUDO=""
if [ "$EUID" -ne 0 ]; then
    if command -v sudo &> /dev/null; then
        SUDO="sudo"
    fi
fi

if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    echo -e "${CYAN}Installing packages via apt-get...${RESET}"
    $SUDO apt-get update -qq
    $SUDO apt-get install -y python3 python3-pip wget curl
elif [ "$OS" = "fedora" ] || [ "$OS" = "rhel" ] || [ "$OS" = "centos" ] || [ "$OS" = "amzn" ]; then
    echo -e "${CYAN}Installing packages via yum/dnf...${RESET}"
    # Amazon Linux uses yum, not dnf
    if command -v dnf &> /dev/null; then
        $SUDO dnf install -y python3 python3-pip wget curl
    else
        $SUDO yum install -y python3 python3-pip wget curl
    fi
elif [ "$OS" = "arch" ] || [ "$OS" = "manjaro" ]; then
    echo -e "${CYAN}Installing packages via pacman...${RESET}"
    $SUDO pacman -Sy --noconfirm python python-pip wget curl
else
    echo -e "${YELLOW}Unsupported OS. Attempting to continue...${RESET}"
fi

echo -e "${GREEN}✓ Dependencies installed${RESET}"

# Install Python dependencies
echo -e "${CYAN}Installing Python packages (msgpack)...${RESET}"
if pip3 install --user msgpack 2>&1 | grep -q "Successfully installed\|already satisfied"; then
    echo -e "${GREEN}✓ msgpack installed${RESET}"
elif python3 -m pip install --user msgpack 2>&1 | grep -q "Successfully installed\|already satisfied"; then
    echo -e "${GREEN}✓ msgpack installed${RESET}"
else
    echo -e "${YELLOW}⚠ msgpack installation may have issues, continuing...${RESET}"
fi

# Create installation directory
INSTALL_DIR="$HOME/.nexadb"
BIN_DIR="$HOME/.local/bin"
DATA_DIR="$HOME/.local/share/nexadb"

echo -e "\n${BOLD}[2/5] Creating directories...${RESET}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DATA_DIR"

# Download NexaDB files
echo -e "\n${BOLD}[3/5] Downloading NexaDB v2.2.11...${RESET}"
cd "$INSTALL_DIR"

FILES=(
    "nexadb_server.py"
    "nexadb_binary_server.py"
    "admin_server.py"
    "veloxdb_core.py"
    "storage_engine.py"
    "nexadb_client.py"
    "reset_root_password.py"
)

for file in "${FILES[@]}"; do
    echo -e "${CYAN}Downloading $file...${RESET}"
    curl -fsSL "https://raw.githubusercontent.com/krishcdbry/nexadb/main/$file" -o "$file"
done

# Download admin panel
echo -e "${CYAN}Downloading admin panel...${RESET}"
mkdir -p admin_panel/css admin_panel/js

# Download HTML files
curl -fsSL "https://raw.githubusercontent.com/krishcdbry/nexadb/main/admin_panel/index.html" -o admin_panel/index.html
curl -fsSL "https://raw.githubusercontent.com/krishcdbry/nexadb/main/admin_panel/login.html" -o admin_panel/login.html

# Download CSS
curl -fsSL "https://raw.githubusercontent.com/krishcdbry/nexadb/main/admin_panel/css/styles.css" -o admin_panel/css/styles.css 2>/dev/null || true

# Download JS
curl -fsSL "https://raw.githubusercontent.com/krishcdbry/nexadb/main/admin_panel/js/app.js" -o admin_panel/js/app.js 2>/dev/null || true
curl -fsSL "https://raw.githubusercontent.com/krishcdbry/nexadb/main/admin_panel/js/auth.js" -o admin_panel/js/auth.js 2>/dev/null || true

# Create executable wrapper scripts
echo -e "\n${BOLD}[4/5] Creating command-line tools...${RESET}"

# Main nexadb command
cat > "$BIN_DIR/nexadb" <<'EOF'
#!/bin/bash

NEXADB_DIR="$HOME/.nexadb"
DATA_DIR="${DATA_DIR:-$HOME/.local/share/nexadb}"

case "$1" in
  start|server)
    shift
    mkdir -p "$DATA_DIR"
    cd "$NEXADB_DIR"
    python3 nexadb_server.py --data-dir "$DATA_DIR" "$@"
    ;;
  admin|ui)
    shift
    mkdir -p "$DATA_DIR"
    cd "$NEXADB_DIR"
    python3 admin_server.py --data-dir "$DATA_DIR" "$@"
    ;;
  reset-password)
    shift
    cd "$NEXADB_DIR"
    python3 reset_root_password.py --data-dir "$DATA_DIR" "$@"
    ;;
  --version|-v)
    echo "NexaDB v2.2.11"
    ;;
  --help|-h|help|*)
    cat <<HELP
NexaDB - The database for quick apps

Usage:
  nexadb start              Start all services (Binary + REST + Admin)
  nexadb admin              Start admin UI only (port 9999)
  nexadb reset-password     Reset root password to default
  nexadb --version          Show version
  nexadb --help             Show this help

Services (when running 'nexadb start'):
  Binary Protocol           Port 6970 (10x faster!)
  JSON REST API             Port 6969 (REST fallback)
  Admin Web UI              Port 9999 (Web interface)

Examples:
  nexadb start                         # Start all services
  nexadb admin                         # Start admin UI only
  nexadb reset-password                # Reset root password
  nexadb reset-password --password foo # Reset to custom password

Default Credentials:
  Username: root
  Password: nexadb123

Learn more: https://github.com/krishcdbry/nexadb
HELP
    ;;
esac
EOF

chmod +x "$BIN_DIR/nexadb"

# Download nexa CLI binary
echo -e "${CYAN}Downloading nexa CLI (interactive terminal)...${RESET}"

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    NEXA_BINARY="nexa-x86_64-unknown-linux-gnu"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    NEXA_BINARY="nexa-aarch64-unknown-linux-gnu"
else
    echo -e "${YELLOW}Unsupported architecture: $ARCH. Skipping nexa CLI installation.${RESET}"
    NEXA_BINARY=""
fi

if [ -n "$NEXA_BINARY" ]; then
    # Download nexa CLI v2.2.0 from GitHub releases
    NEXA_URL="https://github.com/krishcdbry/nexadb/releases/download/cli-v2.2.0/$NEXA_BINARY"
    if curl -fsSL "$NEXA_URL" -o "$BIN_DIR/nexa" 2>/dev/null; then
        chmod +x "$BIN_DIR/nexa"
        echo -e "${GREEN}✓ nexa CLI v2.2.0 installed${RESET}"
    else
        echo -e "${YELLOW}⚠ Could not download nexa CLI. Skipping...${RESET}"
    fi
fi

# Add to PATH if not already
echo -e "\n${BOLD}[5/5] Configuring PATH...${RESET}"

SHELL_RC=""
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
else
    SHELL_RC="$HOME/.profile"
fi

if ! grep -q "$BIN_DIR" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# Added by NexaDB installer" >> "$SHELL_RC"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    echo -e "${GREEN}Added $BIN_DIR to PATH in $SHELL_RC${RESET}"
else
    echo -e "${CYAN}PATH already configured${RESET}"
fi

# Installation complete
echo -e "\n${GREEN}${BOLD}╔════════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║                                                                ║${RESET}"
echo -e "${GREEN}${BOLD}║            ✓ Installation Complete!                           ║${RESET}"
echo -e "${GREEN}${BOLD}║                                                                ║${RESET}"
echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════════════════════════╝${RESET}\n"

echo -e "${YELLOW}${BOLD}🚀 QUICK START${RESET}"
echo -e "   ${CYAN}Reload your shell:${RESET}"
echo -e "   ${BOLD}$ source $SHELL_RC${RESET}"
echo -e ""
echo -e "   ${CYAN}Start NexaDB:${RESET}"
echo -e "   ${BOLD}$ nexadb start${RESET}"
echo -e ""

echo -e "${CYAN}${BOLD}✨ KEY FEATURES${RESET}"
echo -e "   ${GREEN}✓${RESET} HNSW Vector Search (200x faster)"
echo -e "   ${GREEN}✓${RESET} Enterprise Security (AES-256-GCM, RBAC)"
echo -e "   ${GREEN}✓${RESET} Advanced Indexing (B-Tree, Hash, Full-text)"
echo -e "   ${GREEN}✓${RESET} TOON Format (40-50% LLM cost savings)"
echo -e "   ${GREEN}✓${RESET} 20K reads/sec, <1ms lookups"
echo -e ""

echo -e "${YELLOW}${BOLD}🔐 DEFAULT CREDENTIALS${RESET}"
echo -e "   ${CYAN}Username:${RESET} ${GREEN}root${RESET}"
echo -e "   ${CYAN}Password:${RESET} ${GREEN}nexadb123${RESET}"
echo -e ""

echo -e "${CYAN}${BOLD}📚 USEFUL COMMANDS${RESET}"
echo -e "   ${CYAN}nexadb start${RESET}          - Start all services"
echo -e "   ${CYAN}nexadb admin${RESET}          - Admin UI only"
echo -e "   ${CYAN}nexa -u root -p${RESET}       - Interactive CLI terminal"
echo -e "   ${CYAN}nexadb reset-password${RESET} - Reset password"
echo -e "   ${CYAN}nexadb --help${RESET}         - Show help"
echo -e ""

echo -e "${CYAN}${BOLD}🔗 RESOURCES${RESET}"
echo -e "   ${CYAN}Documentation:${RESET} https://github.com/krishcdbry/nexadb"
echo -e "   ${CYAN}Website:${RESET}       https://nexadb.io"
echo -e ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}${BOLD}  🎉 Ready to build! Run 'nexadb start' to begin  ${RESET}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
