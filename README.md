# MergeConflictResolver (Merj)

A CLI that automatically resolves merge conflicts upon git pulls with GitHub integration.

## Quick Start

### 1. Clone and Install
```bash
git clone https://github.com/Anay-jo/MergeConflictResolver.git
cd MergeConflictResolver
npm install
npm link
```

### 2. Authenticate
```bash
merj auth
```
Enter your GitHub Personal Access Token (create one at https://github.com/settings/tokens)

### 3. Use It
```bash
# Pull changes (detects conflicts)
merj pull

# Push changes
merj push
```

## Setup Guide

**For detailed setup instructions, see [SETUP.md](SETUP.md)**

The setup guide includes:
- Prerequisites
- Step-by-step installation
- GitHub authentication setup
- Troubleshooting common issues
- Command reference

## Features

- ✅ GitHub authentication with Personal Access Tokens
- ✅ Pull changes from remote repositories
- ✅ Detect merge conflicts automatically
- ✅ Push changes to remote repositories
- ✅ Force push support
- ✅ Repo info display (owner/repo/branch)

## Commands

- `merj auth` - Set up GitHub authentication
- `merj pull` - Pull changes and detect conflicts
- `merj push` - Push changes to remote

## Authors

Anay Sam Ayush and Josh

## License

ISC
