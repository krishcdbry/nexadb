#!/bin/bash
# Create GitHub release using gh CLI
# Requires: brew install gh

set -e

echo "🏷️  Creating GitHub release v1.0.0..."

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not found. Install it with:"
    echo "   brew install gh"
    echo ""
    echo "Or create the release manually at:"
    echo "   https://github.com/krishcdbry/nexadb/releases/new"
    exit 1
fi

# Login check
if ! gh auth status &> /dev/null; then
    echo "🔐 Logging into GitHub..."
    gh auth login
fi

# Create release
echo "📦 Creating release..."
gh release create v1.0.0 \
    --repo krishcdbry/nexadb \
    --title "NexaDB v1.0.0 - The Database for Quick Apps" \
    --notes "🚀 **NexaDB v1.0.0 - Initial Release**

The database for quick apps, MVPs, and POCs.

## ✨ Features

- ⚡ **30-second installation** - \`brew install nexadb\`
- 🎯 **Zero dependencies** - Pure Python standard library
- 🧠 **Vector search built-in** - For AI/ML applications
- 🎨 **Professional admin UI** - Beautiful dark theme
- 🔍 **MongoDB-like queries** - Familiar syntax
- 📊 **Aggregation pipelines** - Group, sort, filter data
- 🚀 **Production-ready** - LSM-Tree storage with WAL

## 🚀 Quick Start

### Homebrew (macOS/Linux)
\`\`\`bash
brew tap krishcdbry/nexadb
brew install nexadb
nexadb start
\`\`\`

### Direct Run
\`\`\`bash
git clone https://github.com/krishcdbry/nexadb.git
cd nexadb
python3 nexadb_server.py
\`\`\`

## 🎯 Perfect For

- MVPs and POCs
- Weekend projects
- Hackathons
- AI/ML applications
- Learning backend development

---

**Happy building!** 🎉"

echo ""
echo "✅ Release created!"
echo ""
echo "📍 View release: https://github.com/krishcdbry/nexadb/releases/tag/v1.0.0"
echo ""
echo "Next steps:"
echo "1. bash calculate_sha256.sh"
echo "2. Update nexadb.rb with SHA256"
echo "3. bash create_homebrew_tap.sh"
