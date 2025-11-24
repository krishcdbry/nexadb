# 🍺 Homebrew Setup Guide for NexaDB

**Step-by-step guide to make NexaDB installable via Homebrew**

---

## 📋 Overview

After completing these steps, users will be able to install NexaDB with:

```bash
brew tap krishcdbry/nexadb
brew install nexadb
nexadb start
```

---

## ✅ Step 1: Push Code to GitHub

```bash
cd /Users/krish/krishx/nexadb

# Run the setup script
bash setup_github.sh
```

**What this does:**
- Initializes git repository
- Adds all NexaDB files
- Creates commit (with YOUR name from git config)
- Pushes to git@gitkc:krishcdbry/nexadb.git
- Creates v1.0.0 tag

**After running:**
- ✅ Code is on GitHub
- ✅ v1.0.0 tag created

**Verify:** Go to https://github.com/krishcdbry/nexadb

---

## ✅ Step 2: Create GitHub Release

**Manual step on GitHub:**

1. Go to: https://github.com/krishcdbry/nexadb/releases/new

2. **Choose tag:** v1.0.0 (should exist from step 1)

3. **Release title:** NexaDB v1.0.0 - The Database for Quick Apps

4. **Description:**
```markdown
🚀 **NexaDB v1.0.0 - Initial Release**

The database for quick apps, MVPs, and POCs.

## ✨ Features

- ⚡ **30-second installation** - `brew install nexadb`
- 🎯 **Zero dependencies** - Pure Python standard library
- 🧠 **Vector search built-in** - For AI/ML applications
- 🎨 **Professional admin UI** - Beautiful dark theme
- 🔍 **MongoDB-like queries** - Familiar syntax
- 📊 **Aggregation pipelines** - Group, sort, filter data
- 🚀 **Production-ready** - LSM-Tree storage with WAL

## 🚀 Quick Start

### Homebrew (macOS/Linux)
```bash
brew tap krishcdbry/nexadb
brew install nexadb
nexadb start
```

### pip (Python)
```bash
pip install nexadb
nexadb-server
```

### npm (Node.js)
```bash
npx nexadb-server
```

### Direct Run
```bash
python3 nexadb_server.py
```

## 📚 Documentation

- [Installation Guide](INSTALLATION.md)
- [Getting Started](GET_STARTED.md)
- [API Documentation](README.md)
- [Framework Examples](examples/)

## 🎯 Perfect For

- MVPs and POCs
- Weekend projects
- Hackathons
- AI/ML applications
- Learning backend development
- Quick prototypes

## 🆚 vs MongoDB/Redis/SQLite

See [COMPARISON_GUIDE.md](COMPARISON_GUIDE.md)

---

**Happy building!** 🎉
```

5. **Click:** "Publish release"

**After publishing:**
- ✅ GitHub release created
- ✅ Release tarball available at: https://github.com/krishcdbry/nexadb/archive/refs/tags/v1.0.0.tar.gz

---

## ✅ Step 3: Calculate SHA256 Hash

```bash
cd /Users/krish/krishx/nexadb

# Run the SHA256 calculation script
bash calculate_sha256.sh
```

**What this does:**
- Downloads the v1.0.0 release tarball
- Calculates SHA256 hash
- Saves hash to `sha256.txt`
- Displays the hash

**Output will look like:**
```
SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

**Copy this hash!** You'll need it in the next step.

---

## ✅ Step 4: Update Homebrew Formula

Open `nexadb.rb` and replace this line:

```ruby
sha256 "YOUR_SHA256_HASH_HERE"  # Generate after creating release
```

With the actual hash from Step 3:

```ruby
sha256 "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```

**Or use this command:**
```bash
# Replace with actual SHA256 from sha256.txt
SHA256=$(cat sha256.txt)
sed -i '' "s/YOUR_SHA256_HASH_HERE/$SHA256/" nexadb.rb
```

**Verify the update:**
```bash
grep sha256 nexadb.rb
# Should show actual hash, not "YOUR_SHA256_HASH_HERE"
```

---

## ✅ Step 5: Create Homebrew Tap Repository

**5a. Create GitHub repository:**

1. Go to: https://github.com/new

2. **Settings:**
   - **Name:** `homebrew-nexadb`
   - **Description:** `Homebrew tap for NexaDB - The database for quick apps`
   - **Visibility:** Public ✅
   - **Initialize:** DON'T add README/license/gitignore

3. **Click:** "Create repository"

**5b. Run the tap creation script:**

```bash
cd /Users/krish/krishx/nexadb

# Run the Homebrew tap script
bash create_homebrew_tap.sh
```

**What this does:**
- Clones homebrew-nexadb repository
- Creates `Formula/` directory
- Copies nexadb.rb formula
- Updates URLs with your GitHub username
- Commits and pushes

**After running:**
- ✅ Homebrew tap repository created
- ✅ Formula published

**Verify:** Go to https://github.com/krishcdbry/homebrew-nexadb

---

## ✅ Step 6: Test Installation

**Test locally:**

```bash
# Add your tap
brew tap krishcdbry/nexadb

# Install NexaDB
brew install nexadb

# Verify installation
nexadb --version
# Should output: NexaDB v1.0.0

# Test help command
nexadb --help

# Start server
nexadb start
# Should start server on port 6969

# In another terminal, start admin UI
nexadb admin
# Should start admin UI on port 9999

# Test with curl
curl http://localhost:6969/status
# Should return: {"status":"ok","version":"1.0.0","database":"NexaDB"}

# Open admin UI
open http://localhost:9999
```

**If everything works:**
✅ Homebrew installation successful!

---

## 🎉 Done! Users Can Now Install

Share these commands with users:

```bash
# Install NexaDB via Homebrew
brew tap krishcdbry/nexadb
brew install nexadb

# Start using it
nexadb start          # Start database server
nexadb admin          # Start admin UI (in another terminal)
```

---

## 🔄 For Future Updates

When you release v1.1.0:

1. **Create new tag and release on GitHub**
   ```bash
   git tag -a v1.1.0 -m "Version 1.1.0"
   git push origin v1.1.0
   ```

2. **Calculate new SHA256**
   ```bash
   curl -L https://github.com/krishcdbry/nexadb/archive/refs/tags/v1.1.0.tar.gz | shasum -a 256
   ```

3. **Update Formula:**
   - Change `url` to v1.1.0
   - Update `sha256` with new hash
   - Update version if needed

4. **Push to tap:**
   ```bash
   cd homebrew-nexadb
   git add Formula/nexadb.rb
   git commit -m "nexadb: update to 1.1.0"
   git push origin main
   ```

5. **Users upgrade:**
   ```bash
   brew update
   brew upgrade nexadb
   ```

---

## 🐛 Troubleshooting

### Issue: "Formula not found"

**Fix:**
```bash
brew update
brew tap krishcdbry/nexadb
```

### Issue: "SHA256 mismatch"

**Fix:**
- Recalculate SHA256 with `bash calculate_sha256.sh`
- Update nexadb.rb with correct hash
- Push update to homebrew-nexadb

### Issue: "Python not found"

**Fix:**
```bash
brew install python@3.11
```

### Issue: "Port already in use"

**Fix:**
```bash
# Find what's using port 6969
lsof -i :6969

# Kill it or use different port
nexadb start --port 8080
```

---

## 📊 Summary

After all steps:

✅ **NexaDB code:** https://github.com/krishcdbry/nexadb
✅ **Homebrew tap:** https://github.com/krishcdbry/homebrew-nexadb
✅ **Installation:** `brew tap krishcdbry/nexadb && brew install nexadb`

---

## 🎯 Next Steps

1. ✅ Homebrew setup complete
2. 📢 Announce on Twitter/X
3. 📝 Post to Hacker News
4. 🚀 Publish to PyPI and npm
5. 🐳 Build Docker image

See `VIRAL_STRATEGY.md` for full launch plan!

---

**Homebrew makes NexaDB super easy to install. This is huge for adoption!** 🎉
