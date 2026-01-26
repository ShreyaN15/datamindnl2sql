# Git Large File Handling

This document explains how large model files are handled in this repository.

## Summary

✅ **Successfully pushed to GitHub** - All large model files have been removed from git history  
✅ **Models are gitignored** - Future model files won't be accidentally committed  
✅ **Local models preserved** - Your local `datamind_t5/` and `models/` directories are intact

## What Was Done

1. **Removed from Git Tracking:**
   - `models/nl2sql-t5/model.safetensors` (850 MB)
   - All other model binary files
   - These files are now in `.gitignore`

2. **Cleaned Git History:**
   - Used `git filter-branch` to remove large files from all commits
   - Force pushed cleaned history to `first-iteration` branch
   - Repository size reduced significantly

3. **Added Documentation:**
   - `models/README.md` - Explains where models are located
   - Updated `.gitignore` - Prevents future accidental commits

## Files Excluded from Git

The following are now gitignored:

```
# Directories
datamind_t5/          # Training data and model checkpoints
models/               # Model artifacts (except README.md)

# File types
*.safetensors         # PyTorch model weights
*.bin                 # Binary model files
*.pt, *.pth           # PyTorch checkpoint files
*.onnx                # ONNX model files
*.h5                  # HDF5 model files
```

## Model Location

The application uses models from:

```
datamind_t5/final_finetuned/
├── model.safetensors      # ~850 MB (gitignored)
├── config.json
├── tokenizer_config.json
└── ... other files
```

These files exist **locally only** and are **not pushed to GitHub**.

## For New Team Members

If you clone this repository, you'll need to:

1. **Option 1: Train the model yourself**

   ```bash
   cd datamind_t5
   python train.py
   ```

2. **Option 2: Get the model from team member**
   - Ask a team member to share their `datamind_t5/final_finetuned/` directory
   - Copy it to the same location in your local repo

3. **Option 3: Download from cloud storage** (recommended for production)
   - Upload model to S3/GCS/Azure Blob
   - Download during deployment
   - Add download script to setup

## Best Practices for Large Files

### ❌ Don't Do This:

```bash
git add models/          # Will try to add large files
git add datamind_t5/     # Will try to add large files
git add *.safetensors    # Large model files
```

### ✅ Do This Instead:

```bash
# Models are already gitignored, so git add . is safe
git add .

# If you need to add specific files from ignored directories
git add -f models/README.md
```

## Production Deployment

For production, consider:

1. **Model Registry**
   - MLflow Model Registry
   - Weights & Biases
   - DVC (Data Version Control)

2. **Cloud Storage**

   ```python
   # Download model at startup
   import boto3
   s3 = boto3.client('s3')
   s3.download_file('my-bucket', 'models/model.safetensors',
                    'datamind_t5/final_finetuned/model.safetensors')
   ```

3. **Container with Pre-loaded Model**
   ```dockerfile
   # Copy model into Docker image
   COPY datamind_t5/final_finetuned /app/datamind_t5/final_finetuned
   ```

## Troubleshooting

### "File size limit exceeded" error

This means a large file is in your git history. Solution:

```bash
# Remove from git tracking
git rm --cached path/to/large/file

# Remove from history
git filter-branch --force --index-filter \
  'git rm -rf --cached --ignore-unmatch path/to/large/file' \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin branch-name --force
```

### Model file accidentally committed

```bash
# Before pushing
git reset HEAD path/to/model/file
git checkout -- path/to/model/file

# After pushing
# Follow the filter-branch steps above
```

## Current Repository Status

✅ All large files removed from git history  
✅ `.gitignore` properly configured  
✅ Local models intact and working  
✅ Successfully pushed to GitHub  
✅ Documentation added for future reference

## Git LFS Alternative (Optional)

For future consideration, you could use Git LFS (Large File Storage):

```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.safetensors"
git lfs track "*.bin"

# Add and commit
git add .gitattributes
git commit -m "Configure Git LFS"
```

**Note:** Git LFS requires storage quota and may have costs for large repos. The current approach (gitignoring models) is simpler and free.

---

**Last Updated:** January 17, 2026  
**Status:** ✅ All large files successfully removed from git
