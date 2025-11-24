#!/bin/bash
# Debug Homebrew installation

echo "🔍 Debugging NexaDB Homebrew installation..."
echo ""

# Check if nexadb is installed
echo "1. Checking if nexadb is installed..."
if brew list nexadb &> /dev/null; then
    echo "   ✅ nexadb is installed via Homebrew"
    echo ""
    echo "   Installation info:"
    brew info nexadb
else
    echo "   ❌ nexadb is NOT installed"
fi

echo ""
echo "2. Checking Homebrew bin directories..."
echo "   Homebrew prefix: $(brew --prefix)"
echo "   Homebrew bin: $(brew --prefix)/bin"
echo ""

# Check if nexadb binary exists
echo "3. Looking for nexadb binary..."
if [ -f "$(brew --prefix)/bin/nexadb" ]; then
    echo "   ✅ Found: $(brew --prefix)/bin/nexadb"
    ls -la "$(brew --prefix)/bin/nexadb"
else
    echo "   ❌ Not found in: $(brew --prefix)/bin/nexadb"
fi

echo ""
echo "4. Checking PATH..."
echo "   PATH: $PATH"
echo ""
if echo "$PATH" | grep -q "$(brew --prefix)/bin"; then
    echo "   ✅ Homebrew bin is in PATH"
else
    echo "   ❌ Homebrew bin is NOT in PATH!"
    echo "   Add to your ~/.zshrc or ~/.bash_profile:"
    echo "   export PATH=\"$(brew --prefix)/bin:\$PATH\""
fi

echo ""
echo "5. Checking Python..."
python3 --version

echo ""
echo "6. Looking for NexaDB files..."
CELLAR_PATH="$(brew --prefix)/Cellar/nexadb"
if [ -d "$CELLAR_PATH" ]; then
    echo "   ✅ Found Cellar: $CELLAR_PATH"
    ls -la "$CELLAR_PATH"

    # Check latest version
    LATEST=$(ls -t "$CELLAR_PATH" | head -1)
    if [ -n "$LATEST" ]; then
        echo ""
        echo "   Latest version: $LATEST"
        echo "   Contents:"
        ls -la "$CELLAR_PATH/$LATEST/"
    fi
else
    echo "   ❌ Cellar not found: $CELLAR_PATH"
fi

echo ""
echo "7. Try running directly..."
if [ -f "$(brew --prefix)/bin/nexadb" ]; then
    echo "   Testing: $(brew --prefix)/bin/nexadb --version"
    "$(brew --prefix)/bin/nexadb" --version 2>&1 || echo "   ❌ Failed to run"
fi

echo ""
echo "=================================================="
echo "Suggestions:"
echo "=================================================="
echo ""
echo "If nexadb is installed but not found:"
echo "  1. Add Homebrew to PATH:"
echo "     export PATH=\"$(brew --prefix)/bin:\$PATH\""
echo ""
echo "  2. Reload shell:"
echo "     source ~/.zshrc  # or source ~/.bash_profile"
echo ""
echo "  3. Try again:"
echo "     nexadb --version"
echo ""
echo "If installation failed:"
echo "  1. Uninstall:"
echo "     brew uninstall nexadb"
echo ""
echo "  2. Reinstall:"
echo "     brew update"
echo "     brew install nexadb"
echo ""
echo "  3. Check logs:"
echo "     brew install nexadb --verbose"
