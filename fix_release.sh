#!/bin/bash
# Fix: Create release from existing v1.0.0 tag

set -e

echo "🔍 Checking if v1.0.0 tag exists..."

# Test if the tarball is accessible
echo "📥 Testing download..."
if curl -f -L -o /tmp/nexadb-test.tar.gz https://github.com/krishcdbry/nexadb/archive/refs/tags/v1.0.0.tar.gz 2>/dev/null; then
    echo "✅ Tarball exists! Calculating SHA256..."
    SHA256=$(shasum -a 256 /tmp/nexadb-test.tar.gz | awk '{print $1}')
    echo ""
    echo "=================================================="
    echo "SHA256: $SHA256"
    echo "=================================================="
    echo ""
    echo "$SHA256" > sha256.txt
    echo "💾 SHA256 saved to sha256.txt"

    # Update formula
    echo "📝 Updating nexadb.rb..."
    sed -i '' "s/YOUR_SHA256_HASH_HERE/$SHA256/" nexadb.rb

    echo ""
    echo "✅ Formula updated!"
    echo ""
    echo "Next step:"
    echo "  bash create_homebrew_tap.sh"

    rm /tmp/nexadb-test.tar.gz
else
    echo "❌ Tarball not found at:"
    echo "   https://github.com/krishcdbry/nexadb/archive/refs/tags/v1.0.0.tar.gz"
    echo ""
    echo "This means the tag exists but the code isn't pushed."
    echo ""
    echo "Fix:"
    echo "1. Make sure code is pushed to main branch:"
    echo "   git push origin main"
    echo ""
    echo "2. Then re-push the tag:"
    echo "   git push origin v1.0.0 --force"
    echo ""
    echo "3. Then run this script again:"
    echo "   bash fix_release.sh"
fi
