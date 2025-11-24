#!/bin/bash
# Create Homebrew tap repository
# Run after updating nexadb.rb with SHA256: bash create_homebrew_tap.sh

set -e

echo "🍺 Creating Homebrew tap for NexaDB..."
echo ""

# Create temporary directory for tap
TEMP_DIR=$(mktemp -d)
echo "📁 Working in: $TEMP_DIR"

cd $TEMP_DIR

# Clone or create homebrew-nexadb repository
echo "📦 Setting up homebrew-nexadb repository..."
git clone git@gitkc:krishcdbry/homebrew-nexadb.git || {
    echo "Repository doesn't exist yet. Create it on GitHub:"
    echo "https://github.com/new"
    echo ""
    echo "Name: homebrew-nexadb"
    echo "Description: Homebrew tap for NexaDB"
    echo "Public: Yes"
    echo ""
    echo "Then run this script again."
    exit 1
}

cd homebrew-nexadb

# Create Formula directory
mkdir -p Formula

# Copy the updated formula
echo "📝 Copying Homebrew formula..."
cp /Users/krish/krishx/nexadb/nexadb.rb Formula/nexadb.rb

# Update the formula with correct username
sed -i '' 's/yourusername/krishcdbry/g' Formula/nexadb.rb

# Commit and push
echo "💾 Committing formula..."
git add Formula/nexadb.rb
git commit -m "Add NexaDB formula v1.0.0

Zero-dependency database for quick apps with:
- MongoDB-like API
- Vector search built-in
- Beautiful admin UI
- REST interface"

echo "🚀 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Homebrew tap created successfully!"
echo ""
echo "🍺 Users can now install NexaDB with:"
echo ""
echo "  brew tap krishcdbry/nexadb"
echo "  brew install nexadb"
echo "  nexadb start"
echo ""
echo "📍 Tap repository: https://github.com/krishcdbry/homebrew-nexadb"
echo ""

# Cleanup
cd ~
rm -rf $TEMP_DIR
echo "🧹 Cleaned up temporary files"
