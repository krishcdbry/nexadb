#!/bin/bash
# Setup script for pushing NexaDB to GitHub
# Run this manually: bash setup_github.sh

set -e

echo "🚀 Setting up NexaDB GitHub repository..."

# Initialize git if not already
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
fi

# Add all files
echo "📝 Adding files..."
git add .

# Commit
echo "💾 Creating commit..."
git commit -m "Initial release - NexaDB v1.0.0

- Zero-dependency LSM-Tree database
- MongoDB-like API with REST interface
- Built-in vector search for AI/ML
- Professional admin UI with dark theme
- Support for collections, queries, aggregations
- Homebrew, pip, npm installation support"

# Add remote (if not already added)
if ! git remote | grep -q origin; then
    echo "🔗 Adding remote..."
    git remote add origin git@gitkc:krishcdbry/nexadb.git
fi

# Rename branch to main
echo "🌿 Setting main branch..."
git branch -M main

# Push to GitHub
echo "🚀 Pushing to GitHub..."
git push -u origin main

# Create tag for v1.0.0
echo "🏷️  Creating v1.0.0 tag..."
git tag -a v1.0.0 -m "NexaDB v1.0.0 - Initial Release

The database for quick apps

Features:
- 30-second installation
- Zero dependencies
- Vector search built-in
- MongoDB-like queries
- Beautiful admin UI
- REST API"

git push origin v1.0.0

echo ""
echo "✅ Done! NexaDB pushed to GitHub"
echo ""
echo "📍 Repository: https://github.com/krishcdbry/nexadb"
echo "🏷️  Release: https://github.com/krishcdbry/nexadb/releases/tag/v1.0.0"
echo ""
echo "Next steps:"
echo "1. Go to GitHub and create a release from the v1.0.0 tag"
echo "2. Run: bash calculate_sha256.sh"
echo "3. Run: bash create_homebrew_tap.sh"
