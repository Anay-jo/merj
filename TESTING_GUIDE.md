# Testing Guide for Merj CLI

## Prerequisites
1. Make sure you're authenticated: `node bin/index.js auth`
2. Have a GitHub repository to test with

## Test 1: Successful Pull (No Conflicts)

In your repository directory:
```bash
node bin/index.js pull
```

Expected output:
- ✅ Authentication success
- 📁 Repository information
- 🌿 Current branch
- ✅ Pull completed successfully

## Test 2: Merge Conflicts Detection

To test conflict detection, you need to create a conflict scenario:

### Option A: Use a Test Repository

1. Create a new GitHub repository or use an existing one
2. Create two branches:
   ```bash
   git checkout -b feature-branch
   echo "Hello from feature" > test.txt
   git add test.txt
   git commit -m "Add test file"
   git push origin feature-branch
   
   git checkout main
   echo "Hello from main" > test.txt
   git add test.txt
   git commit -m "Modify test file"
   git push origin main
   ```

3. Merge and create conflict:
   ```bash
   git merge feature-branch
   # This will create a conflict in test.txt
   ```

4. Check status:
   ```bash
   git status
   # Should show "Unmerged paths"
   ```

5. Now test your CLI (WITHOUT aborting the merge):
   ```bash
   # Test the CLI while conflicts exist
   node bin/index.js pull
   # Should detect: "MERGE CONFLICTS ALREADY EXIST!"
   ```

6. Clean up after testing:
   ```bash
   git merge --abort
   git branch -D feature-branch
   ```

### Option B: Using GitHub Pull Requests

1. Create a fork or use a test repo
2. Create a feature branch and make changes
3. Open a Pull Request on GitHub
4. Make conflicting changes on the main branch
5. Merge locally to see conflicts

## Test 3: Command Options

Test different command options:

```bash
# Specify remote
node bin/index.js pull -r origin

# Specify branch
node bin/index.js pull -b main

# Both options
node bin/index.js pull -r origin -b main
```

## Quick Conflict Test Script

Create a conflict quickly:

```bash
# Create a test file
echo "Line 1" > conflict-test.txt
git add conflict-test.txt
git commit -m "Initial commit"

# Create branch and modify
git checkout -b test-branch
echo "Line 1\nFeature change" > conflict-test.txt
git add conflict-test.txt
git commit -m "Feature change"

# Go back to main and modify same line
git checkout main
echo "Line 1\nMain change" > conflict-test.txt
git add conflict-test.txt
git commit -m "Main change"

# Try to merge
git merge test-branch
# This creates a conflict!

# Check status
git status

# Now test the CLI
node bin/index.js pull
```

## Expected Conflict Output

When conflicts are detected, you should see:
```
⚠️  MERGE CONFLICTS DETECTED!
Found X conflicted file(s):

  1. filename.txt

🔧 Conflict resolution will be implemented here
```

## Cleanup

After testing:
```bash
# If in middle of merge
git merge --abort

# Clean up test branches
git branch -D test-branch feature-branch
git checkout main
```

