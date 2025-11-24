# Publishing NexaDB to Homebrew

Make NexaDB installable via `brew install nexadb` on macOS and Linux.

---

## 🎯 Goal

Users can install NexaDB like MongoDB:

```bash
brew install nexadb
nexadb start
```

**This is HUGE for adoption!**

---

## 📋 Prerequisites

1. **GitHub repository** - Code must be on GitHub
2. **GitHub release** - v1.0.0 with tagged version
3. **Homebrew installed** - `brew --version`
4. **GitHub account** - For creating tap repository

---

## 🚀 Method 1: Homebrew Tap (Recommended for Start)

### Step 1: Create Release on GitHub

```bash
# 1. Push code to GitHub
cd /Users/krish/krishx/nexadb
git init
git add .
git commit -m "v1.0.0 - Initial release"
git remote add origin https://github.com/YOUR_USERNAME/nexadb.git
git push -u origin main

# 2. Create tag
git tag -a v1.0.0 -m "NexaDB v1.0.0 - Initial release"
git push origin v1.0.0

# 3. Create release on GitHub
# Go to: https://github.com/YOUR_USERNAME/nexadb/releases/new
# - Tag: v1.0.0
# - Title: NexaDB v1.0.0
# - Description: Zero-dependency database for quick apps
# - Click "Publish release"
```

### Step 2: Calculate SHA256

```bash
# Download the release tarball
curl -L https://github.com/YOUR_USERNAME/nexadb/archive/refs/tags/v1.0.0.tar.gz -o nexadb-1.0.0.tar.gz

# Calculate SHA256
shasum -a 256 nexadb-1.0.0.tar.gz

# Copy the hash (first part before the filename)
# Example: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

### Step 3: Update Formula

Edit `nexadb.rb` and replace:
- `YOUR_USERNAME` → your GitHub username
- `YOUR_SHA256_HASH_HERE` → the hash from step 2

### Step 4: Create Homebrew Tap Repository

```bash
# 1. Create new GitHub repo named "homebrew-nexadb"
# Go to: https://github.com/new
# Name: homebrew-nexadb
# Description: Homebrew tap for NexaDB
# Public
# Create repository

# 2. Clone the tap repository
cd ~/
git clone https://github.com/YOUR_USERNAME/homebrew-nexadb.git
cd homebrew-nexadb

# 3. Copy the formula
cp /Users/krish/krishx/nexadb/nexadb.rb Formula/nexadb.rb
# Or create Formula directory first
mkdir -p Formula
cp /Users/krish/krishx/nexadb/nexadb.rb Formula/nexadb.rb

# 4. Commit and push
git add Formula/nexadb.rb
git commit -m "Add NexaDB formula"
git push origin main
```

### Step 5: Test Installation

```bash
# Add your tap
brew tap YOUR_USERNAME/nexadb

# Install NexaDB
brew install nexadb

# Test it works
nexadb --version
nexadb --help
```

### Step 6: Users Install

Now users can install with:

```bash
# Add tap (one-time)
brew tap YOUR_USERNAME/nexadb

# Install NexaDB
brew install nexadb

# Use it
nexadb start
```

---

## 🚀 Method 2: Official Homebrew Core (After Viral)

**Note:** This is for after NexaDB becomes popular (1000+ stars)

### Requirements

- 30+ days since first release
- 75+ GitHub stars
- 30+ forks
- Notable watchers
- Significant usage

### Steps

```bash
# 1. Fork homebrew-core
# Go to: https://github.com/Homebrew/homebrew-core
# Click "Fork"

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/homebrew-core.git
cd homebrew-core

# 3. Create branch
git checkout -b nexadb

# 4. Add formula
cp /Users/krish/krishx/nexadb/nexadb.rb Formula/nexadb.rb

# 5. Test formula
brew install --build-from-source ./Formula/nexadb.rb
brew test nexadb
brew audit --strict nexadb

# 6. Commit and create PR
git add Formula/nexadb.rb
git commit -m "nexadb: new formula"
git push origin nexadb

# 7. Create Pull Request
# Go to: https://github.com/Homebrew/homebrew-core
# Create PR from your branch
# Title: "nexadb 1.0.0 (new formula)"
```

**After merge (can take weeks):**

Users install with just:
```bash
brew install nexadb  # No tap needed!
```

---

## 🐧 Linux Support

Homebrew works on Linux too (Homebrew on Linux / Linuxbrew)

### Users on Linux

```bash
# 1. Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install NexaDB
brew tap YOUR_USERNAME/nexadb
brew install nexadb

# 3. Use it
nexadb start
```

---

## 📦 Alternative: Install Script (Before Homebrew)

For immediate use, create an install script:

```bash
#!/bin/bash
# install.sh - Install NexaDB

set -e

echo "Installing NexaDB..."

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Darwin*)    INSTALL_DIR="/usr/local/bin";;
    Linux*)     INSTALL_DIR="$HOME/.local/bin";;
    *)          echo "Unsupported OS: ${OS}"; exit 1;;
esac

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3.8+ required"
    exit 1
fi

# Download files
echo "Downloading NexaDB..."
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR

curl -L https://github.com/YOUR_USERNAME/nexadb/archive/refs/tags/v1.0.0.tar.gz | tar xz
cd nexadb-1.0.0

# Install files
mkdir -p ~/.nexadb
cp *.py ~/.nexadb/
cp *.html ~/.nexadb/

# Create executable
mkdir -p $INSTALL_DIR
cat > $INSTALL_DIR/nexadb << 'EOF'
#!/bin/bash
NEXADB_DIR="$HOME/.nexadb"

case "$1" in
    start|server)
        shift
        python3 "$NEXADB_DIR/nexadb_server.py" "$@"
        ;;
    admin|ui)
        shift
        python3 "$NEXADB_DIR/nexadb_admin_server.py" "$@"
        ;;
    *)
        echo "NexaDB - The database for quick apps"
        echo ""
        echo "Usage:"
        echo "  nexadb start    Start database server"
        echo "  nexadb admin    Start admin UI"
        ;;
esac
EOF

chmod +x $INSTALL_DIR/nexadb

# Cleanup
cd ~
rm -rf $TEMP_DIR

echo "✅ NexaDB installed successfully!"
echo ""
echo "Quick Start:"
echo "  nexadb start    # Start database server"
echo "  nexadb admin    # Start admin UI"
echo ""
echo "Open: http://localhost:9999"
```

**Users install with:**

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/nexadb/main/install.sh | bash
```

---

## 🎯 Recommended Strategy

### Phase 1: Install Script (Week 1)

```bash
# Users run:
curl -fsSL https://nexadb.io/install.sh | bash
```

**Pros:**
- Works immediately
- No Homebrew tap setup
- Cross-platform

### Phase 2: Homebrew Tap (Week 2)

```bash
# Users run:
brew tap YOUR_USERNAME/nexadb
brew install nexadb
```

**Pros:**
- Updates via `brew upgrade`
- More professional
- Better dependency management

### Phase 3: Homebrew Core (After Viral)

```bash
# Users run:
brew install nexadb
```

**Pros:**
- Maximum credibility
- Discoverable via `brew search`
- Official package

---

## 📝 Update Formula for New Versions

```bash
# 1. Create new release on GitHub (v1.1.0)
git tag -a v1.1.0 -m "Version 1.1.0"
git push origin v1.1.0

# 2. Calculate new SHA256
curl -L https://github.com/YOUR_USERNAME/nexadb/archive/refs/tags/v1.1.0.tar.gz | shasum -a 256

# 3. Update Formula/nexadb.rb
# - Change version number
# - Update SHA256
# - Update release notes

# 4. Commit to tap
cd ~/homebrew-nexadb
git add Formula/nexadb.rb
git commit -m "nexadb: update to 1.1.0"
git push

# 5. Users upgrade
brew update
brew upgrade nexadb
```

---

## 🔧 Testing Locally

Before publishing, test the formula:

```bash
# 1. Install from local formula
brew install --build-from-source /path/to/nexadb.rb

# 2. Test commands
nexadb --version
nexadb start &
sleep 5
curl http://localhost:6969/status
killall python3

# 3. Run Homebrew audit
brew audit --strict nexadb

# 4. Run Homebrew test
brew test nexadb

# 5. Uninstall
brew uninstall nexadb
```

---

## 📊 Comparison: Distribution Methods

| Method | Ease | Credibility | Update | Cross-Platform |
|--------|------|-------------|--------|----------------|
| **Install Script** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Manual | ✅ |
| **Homebrew Tap** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | `brew upgrade` | macOS/Linux |
| **Homebrew Core** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | `brew upgrade` | macOS/Linux |
| **pip install** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | `pip upgrade` | All |
| **npm install** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | `npm update` | All |

**Recommendation:** Start with **Homebrew Tap** + **pip** + **npm**

---

## 🎯 Quick Checklist

- [ ] Code pushed to GitHub
- [ ] v1.0.0 release created
- [ ] SHA256 calculated
- [ ] nexadb.rb updated with correct info
- [ ] homebrew-nexadb repository created
- [ ] Formula pushed to tap
- [ ] Local testing passed
- [ ] Documentation updated
- [ ] Announcement ready

---

## 📢 Marketing After Homebrew

**Title:** "NexaDB is now on Homebrew!"

**Post:**
```
🎉 NexaDB is now brewable!

  brew tap USERNAME/nexadb
  brew install nexadb
  nexadb start

Zero-dependency database with:
✅ MongoDB-like API
✅ Vector search built-in
✅ Beautiful admin UI
✅ 30-second install

Perfect for MVPs, POCs, and quick apps.

Try it: https://github.com/USERNAME/nexadb
```

---

**Homebrew support = MASSIVE credibility boost!** 🚀

*Homebrew Publishing Guide v1.0*
