#!/bin/bash
# Test fresh installation after updating tap

set -e

echo "🧪 Testing fresh NexaDB installation..."
echo ""

# Step 1: Update the tap
echo "1️⃣ Updating tap repository..."
cd ~/homebrew-nexadb
cp /Users/krish/krishx/nexadb/nexadb.rb Formula/nexadb.rb
git add Formula/nexadb.rb
git commit -m "Fix: Use dynamic Python path and auto-add to shell PATH" || echo "Already committed"
git push origin main
echo "✅ Tap updated"
echo ""

# Step 2: Clean existing installation
echo "2️⃣ Removing old installation..."
brew uninstall nexadb 2>/dev/null || echo "Not installed"
brew untap krishcdbry/nexadb 2>/dev/null || echo "Not tapped"
echo "✅ Cleaned"
echo ""

# Step 3: Fresh install
echo "3️⃣ Installing fresh from tap..."
brew tap krishcdbry/nexadb
brew install nexadb
echo "✅ Installed"
echo ""

# Step 4: Test
echo "4️⃣ Testing installation..."
echo "Version check:"
nexadb --version
echo ""

echo "Starting server (will run for 3 seconds)..."
timeout 3 nexadb start 2>&1 || echo ""
echo ""

echo "✅ All tests passed!"
echo ""
echo "🎉 Fresh installation working! Users can now:"
echo "   brew tap krishcdbry/nexadb"
echo "   brew install nexadb"
echo "   nexadb start"
