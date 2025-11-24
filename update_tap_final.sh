#!/bin/bash
# Update Homebrew tap with fixed Python path

set -e

echo "🔧 Updating Homebrew tap with fixed formula..."
echo ""

TAP_DIR="$HOME/homebrew-nexadb"

# Check if tap directory exists
if [ ! -d "$TAP_DIR" ]; then
    echo "❌ Tap directory not found: $TAP_DIR"
    echo "Please run create_homebrew_tap.sh first"
    exit 1
fi

cd "$TAP_DIR"

# Copy updated formula
echo "📝 Copying updated formula..."
cp /Users/krish/krishx/nexadb/nexadb.rb Formula/nexadb.rb

# Commit and push
echo "📤 Committing and pushing..."
git add Formula/nexadb.rb
git commit -m "Fix Python path to use python3.11 for compatibility"
git push origin main

echo ""
echo "✅ Tap updated successfully!"
echo ""
echo "Users can now install with:"
echo "  brew tap krishcdbry/nexadb"
echo "  brew install nexadb"
echo ""
echo "To test the fix on your machine:"
echo "  brew uninstall nexadb"
echo "  brew untap krishcdbry/nexadb"
echo "  brew tap krishcdbry/nexadb"
echo "  brew install nexadb"
echo "  nexadb start"
