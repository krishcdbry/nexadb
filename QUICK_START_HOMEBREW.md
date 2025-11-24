# 🍺 Homebrew Setup - Quick Reference

**Run these commands in order:**

---

## 1️⃣ Push to GitHub (5 min)

```bash
cd /Users/krish/krishx/nexadb
bash setup_github.sh
```

✅ Pushes code to: git@gitkc:krishcdbry/nexadb.git

---

## 2️⃣ Create GitHub Release (2 min)

**Go to:** https://github.com/krishcdbry/nexadb/releases/new

- Tag: v1.0.0
- Title: NexaDB v1.0.0 - The Database for Quick Apps
- Copy description from `HOMEBREW_SETUP_GUIDE.md`
- Click "Publish release"

---

## 3️⃣ Calculate SHA256 (1 min)

```bash
cd /Users/krish/krishx/nexadb
bash calculate_sha256.sh
```

✅ Saves hash to `sha256.txt`

---

## 4️⃣ Update Formula (1 min)

```bash
# Automatic update
SHA256=$(cat sha256.txt)
sed -i '' "s/YOUR_SHA256_HASH_HERE/$SHA256/" nexadb.rb

# Verify
grep sha256 nexadb.rb
```

---

## 5️⃣ Create Tap Repo (2 min)

**First, create repo on GitHub:**
https://github.com/new
- Name: `homebrew-nexadb`
- Public

**Then run:**
```bash
bash create_homebrew_tap.sh
```

✅ Tap created at: https://github.com/krishcdbry/homebrew-nexadb

---

## 6️⃣ Test It! (2 min)

```bash
# Install
brew tap krishcdbry/nexadb
brew install nexadb

# Test
nexadb --version
nexadb start
```

**Open:** http://localhost:9999

---

## ✅ Done!

Users can now:

```bash
brew tap krishcdbry/nexadb
brew install nexadb
nexadb start
```

**Total time:** ~15 minutes

---

## 🚀 Share It!

**Tweet this:**
```
🎉 NexaDB is now on Homebrew!

  brew tap krishcdbry/nexadb
  brew install nexadb
  nexadb start

Zero-dependency database with vector search.
Perfect for MVPs and quick apps.

Try it: https://github.com/krishcdbry/nexadb
```

**Post on Hacker News:**
```
Show HN: NexaDB - MongoDB alternative that installs in 30 seconds

https://github.com/krishcdbry/nexadb
```

---

**Homebrew = Instant credibility!** 🎯
