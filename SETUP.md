# Setup Guide - Merj CLI

Follow these steps to set up and use the Merj CLI after cloning the repository.

## Prerequisites

- Node.js (v14 or higher recommended)
- npm (comes with Node.js)
- Git
- A GitHub account

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Anay-jo/MergeConflictResolver.git
cd MergeConflictResolver
```

### 2. Install Dependencies

```bash
npm install
```

This will install all required packages:
- `commander` - CLI framework
- `@octokit/rest` - GitHub API client
- `dotenv` - Environment variables
- `inquirer` - Interactive prompts
- `simple-git` - Git operations

### 3. Link the CLI

Make the `merj` command available globally:

```bash
npm link
```

Now you can use `merj` from any directory!

### 4. Set Up GitHub Authentication

**Create a GitHub Personal Access Token:**

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name (e.g., "Merj CLI")
4. Select scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (if you need to access organization repos)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)

**Authenticate with Merj:**

```bash
merj auth
```

Enter your Personal Access Token when prompted. The CLI will validate it and store it securely.

### 5. Verify Installation

Check that everything works:

```bash
merj --help
```

You should see:
```
Usage: merj [options] [command]

A CLI that automatically resolves merge conflicts upon git pulls

Commands:
  auth            Set up GitHub authentication with Personal Access Token
  pull [options]  Pull changes from remote and automatically resolve merge conflicts
  push [options]  Push changes to remote repository
```

### 6. Test the Commands

Navigate to a git repository:

```bash
cd /path/to/your/repo
merj pull
```

You should see:
- Authentication confirmation
- Repository information
- Pull status

## Common Issues

### Issue: `merj: command not found`

**Solution:**
```bash
npm link
```

If that doesn't work, check your PATH or use:
```bash
npx merj
```

### Issue: Authentication Failed

**Solution:**
1. Verify your token is correct
2. Check that token has the required scopes
3. Try running `merj auth` again

### Issue: Not a git repository

**Solution:**
Make sure you're in a directory that contains a `.git` folder.

### Issue: Push fails with "divergent branches"

**Solution:**
Use force push (be careful!):
```bash
merj push --force
```

## Project Structure

```
MergeConflictResolver/
├── bin/
│   └── index.js          # Main CLI entry point
├── lib/
│   ├── auth.js           # GitHub authentication
│   └── git.js            # Git operations
├── package.json          # Dependencies and config
├── README.md             # Project overview
├── SETUP.md             # This file
└── TESTING_GUIDE.md     # How to test features
```

## What Each Command Does

### `merj auth`
- Sets up GitHub authentication
- Stores your Personal Access Token securely
- Validates the token with GitHub

### `merj pull`
- Authenticates with GitHub
- Shows repository information
- Checks for existing merge conflicts
- Pulls changes from remote
- Detects conflicts after pull

### `merj push`
- Authenticates with GitHub
- Shows repository information
- Pushes changes to remote
- Supports force push with `--force` flag

## Environment Variables

The CLI stores authentication in:
- **macOS/Linux**: `~/.merjrc`
- File permissions: `600` (owner read/write only)

No additional environment variables needed!

## Next Steps

1. Read `TESTING_GUIDE.md` to learn how to test features
2. Try the commands in a test repository
3. Report issues on GitHub

## Support

For issues or questions:
- GitHub Issues: https://github.com/Anay-jo/MergeConflictResolver/issues
- Check `TESTING_GUIDE.md` for testing scenarios

## Development

If you want to contribute:

```bash
# After cloning and npm install
npm link

# Make changes to files in bin/ or lib/
# Test your changes
merj --help
```

## Uninstall

To remove the global link:

```bash
npm unlink -g merj
```

To remove local dependencies:

```bash
npm uninstall
```

