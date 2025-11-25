#!/bin/bash

# NexaDB Uninstallation Script for Linux/Ubuntu

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${CYAN}${BOLD}NexaDB Uninstaller${RESET}\n"

# Directories
INSTALL_DIR="$HOME/.nexadb"
BIN_DIR="$HOME/.local/bin"
DATA_DIR="$HOME/.local/share/nexadb"

echo -e "${YELLOW}This will remove NexaDB from your system.${RESET}"
echo -e "${RED}Your data in $DATA_DIR will be kept.${RESET}"
echo -e "\nContinue? (y/N) "
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Uninstall cancelled.${RESET}"
    exit 0
fi

# Kill running processes
echo -e "\n${BOLD}[1/3] Stopping NexaDB processes...${RESET}"
pkill -f "nexadb_server.py" 2>/dev/null || true
pkill -f "nexadb_binary_server.py" 2>/dev/null || true
pkill -f "admin_server.py" 2>/dev/null || true
echo -e "${GREEN}Stopped all NexaDB processes${RESET}"

# Remove installation directory
echo -e "\n${BOLD}[2/3] Removing installation files...${RESET}"
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}Removed $INSTALL_DIR${RESET}"
fi

# Remove binary
if [ -f "$BIN_DIR/nexadb" ]; then
    rm "$BIN_DIR/nexadb"
    echo -e "${GREEN}Removed $BIN_DIR/nexadb${RESET}"
fi

# Clean PATH from shell configs
echo -e "\n${BOLD}[3/3] Cleaning PATH configuration...${RESET}"
for rc_file in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
    if [ -f "$rc_file" ]; then
        if grep -q "Added by NexaDB installer" "$rc_file"; then
            sed -i.bak '/# Added by NexaDB installer/,+1d' "$rc_file"
            echo -e "${GREEN}Cleaned $rc_file${RESET}"
        fi
    fi
done

echo -e "\n${GREEN}${BOLD}✓ NexaDB uninstalled successfully!${RESET}\n"
echo -e "${YELLOW}Your data is still in: ${CYAN}$DATA_DIR${RESET}"
echo -e "${YELLOW}To remove data: ${CYAN}rm -rf $DATA_DIR${RESET}\n"
echo -e "${CYAN}To reinstall: ${RESET}curl -fsSL https://raw.githubusercontent.com/krishcdbry/nexadb/main/install.sh | bash\n"
