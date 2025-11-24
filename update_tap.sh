#!/bin/bash
# Update the Homebrew tap with the correct SHA256

set -e

echo "🍺 Updating Homebrew tap with correct SHA256..."

# Check if homebrew-nexadb exists
if [ ! -d "$HOME/homebrew-nexadb" ]; then
    echo "📁 Cloning homebrew-nexadb repository..."
    cd ~
    git clone git@gitkc:krishcdbry/homebrew-nexadb.git
    cd homebrew-nexadb
else
    echo "📁 Using existing homebrew-nexadb repository..."
    cd "$HOME/homebrew-nexadb"
    git pull origin main
fi

# Create Formula directory if needed
mkdir -p Formula

# Copy updated formula
echo "📝 Copying updated formula..."
cp /Users/krish/krishx/nexadb/nexadb.rb Formula/nexadb.rb

# Commit and push
echo "💾 Committing update..."
git add Formula/nexadb.rb
git commit -m "Update SHA256 for v1.0.0 release

Correct SHA256: 5058886298767c3130c084aaa82bdeb2fc2c867160175960b83753c1a94680f6"

echo "🚀 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Homebrew tap updated!"
echo ""
echo "Now try installing again:"
echo "  brew update"
echo "  brew install nexadb"
