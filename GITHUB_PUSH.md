# 🚀 Quick GitHub Push Guide

Follow these steps to push your bot to GitHub:

## 1. Initialize Git Repository

```bash
cd "c:\Users\IdeaPad\Desktop\file store bot"
git init
```

## 2. Add Files

```bash
git add .
```

## 3. Create Initial Commit

```bash
git commit -m "Initial commit: File Storage Bot with admin message customization"
```

## 4. Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Create a new repository (e.g., `telegram-file-storage-bot`)
3. **DO NOT** initialize with README (we already have one)
4. Copy the repository URL

## 5. Link and Push

```bash
# Replace <your-username> and <repo-name> with your actual values
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

## Example:

```bash
git remote add origin https://github.com/johndoe/telegram-file-storage-bot.git
git branch -M main
git push -u origin main
```

## ⚠️ Before Pushing - Security Check

Make sure you've:
- [ ] Removed or changed the hardcoded BOT_TOKEN in `filestore_bot.py`
- [ ] Verified `.gitignore` is working (run `git status` to check)
- [ ] NOT committed `.env` file (should be in .gitignore)
- [ ] Reviewed files to be committed

## 🔒 Secure Your Token

### Option 1: Use Environment Variables Only
Edit `filestore_bot.py` line 21 and remove the fallback token:

```python
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Remove the fallback value
```

### Option 2: Use Placeholder
Replace the token with a placeholder:

```python
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
```

## ✅ Verify Push

After pushing, check:
1. Go to your GitHub repository
2. Verify all files are there
3. Check that `.env` and `file_cache.json` are NOT in the repo
4. Verify README.md displays correctly

## 🎉 You're Done!

Your bot is now on GitHub and ready for deployment!

Next steps:
- Choose a deployment platform (see DEPLOYMENT.md)
- Set up environment variables
- Deploy and test
