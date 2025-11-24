#!/bin/bash
# Calculate SHA256 hash for Homebrew formula
# Run after creating GitHub release: bash calculate_sha256.sh

set -e

echo "🔐 Calculating SHA256 hash for NexaDB v1.0.0..."
echo ""

# Download the release tarball
echo "📥 Downloading release tarball..."
curl -L https://github.com/krishcdbry/nexadb/archive/refs/tags/v1.0.0.tar.gz -o nexadb-1.0.0.tar.gz

# Calculate SHA256
echo ""
echo "🔢 Calculating SHA256..."
SHA256=$(shasum -a 256 nexadb-1.0.0.tar.gz | awk '{print $1}')

echo ""
echo "✅ SHA256 hash calculated!"
echo ""
echo "=================================================="
echo "SHA256: $SHA256"
echo "=================================================="
echo ""
echo "📝 Next step:"
echo "Update nexadb.rb and replace 'YOUR_SHA256_HASH_HERE' with:"
echo "$SHA256"
echo ""

# Save to file
echo "$SHA256" > sha256.txt
echo "💾 SHA256 saved to sha256.txt"

# Cleanup
rm nexadb-1.0.0.tar.gz
echo "🧹 Cleaned up temporary files"
