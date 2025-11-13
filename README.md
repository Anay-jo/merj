# Merj - AI-Powered Git Merge Conflict Resolver

Merj automatically detects and resolves Git merge conflicts using Claude AI, CodeRabbit code reviews, and intelligent code context from your repository.

## Table of Contents
- [What is Merj?](#what-is-merj)
- [Quick Start](#quick-start)
- [Complete Setup Guide](#complete-setup-guide)
- [Getting API Keys](#getting-api-keys)
- [Running Merj](#running-merj)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [Testing Your Setup](#testing-your-setup)
- [Cost Estimates](#cost-estimates)

## What is Merj?

Merj transforms the tedious process of resolving Git merge conflicts into an intelligent, semi-automated workflow:

1. **Detects** merge conflicts automatically after `git pull`
2. **Analyzes** both sides of the conflict using CodeRabbit
3. **Understands** your codebase using RAG (Retrieval-Augmented Generation)
4. **Resolves** conflicts intelligently using Claude AI
5. **Presents** solutions for your review and approval

Instead of manually editing conflict markers, you get AI-powered resolutions with explanations.

## Quick Start

Get Merj running in 5 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/Anay-jo/MergeConflictResolver.git
cd MergeConflictResolver

# 2. Run quick setup (Node.js dependencies only)
npm install && npm link

# 3. Set up GitHub authentication
merj auth

# 4. Set Claude AI key (required)
export ANTHROPIC_API_KEY="sk-ant-..."

# 5. Try it!
cd your-git-repo
merj pull
```

For full functionality with CodeRabbit and RAG, continue to [Complete Setup Guide](#complete-setup-guide).

## Complete Setup Guide

### Prerequisites

- **Node.js** v18+ ([Download](https://nodejs.org/))
- **Python** 3.8+ ([Download](https://www.python.org/downloads/))
- **Git** 2.0+
- **GitHub Account** with Personal Access Token
- **API Keys** for Claude AI and Voyage AI (see [Getting API Keys](#getting-api-keys))

### Step 1: Clone and Install Node.js Components

```bash
# Clone the repository
git clone https://github.com/Anay-jo/MergeConflictResolver.git
cd MergeConflictResolver

# Install Node.js dependencies
npm install

# Make 'merj' command available globally
npm link

# Verify installation
merj --help
```

### Step 2: Set Up Python Environment (for RAG Pipeline)

```bash
# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
pip install -r flask_backend/requirements.txt
```

### Step 3: Install CodeRabbit CLI

```bash
# Install CodeRabbit CLI globally
curl -fsSL https://cli.coderabbit.ai/install.sh | sh

# Reload your shell configuration
source ~/.zshrc  # or ~/.bashrc for bash users

# Verify installation
coderabbit --version

# Log in to CodeRabbit (opens browser)
coderabbit auth login
```

### Step 4: Configure All API Keys

Create a `.env` file in the project root (or set environment variables):

```bash
# Required API Keys
export ANTHROPIC_API_KEY="sk-ant-api03-xxxxx"  # Claude AI (Required)
export VOYAGE_API_KEY="pa-xxxxx"                # Embeddings (Required for RAG)

# Optional Configuration
export MAIN_REF="origin/main"                   # Your main branch
export MODEL="claude-3-5-sonnet-20241022"       # Claude model to use
```

### Step 5: Authenticate GitHub

```bash
# Run authentication command
merj auth

# Enter your GitHub Personal Access Token when prompted
# The token will be stored securely in ~/.merjrc
```

### Step 6: Start the Flask Backend (for RAG)

```bash
# In a separate terminal, activate Python environment
source venv/bin/activate

# Start Flask backend
cd flask_backend
python app.py

# You should see: "Running on http://127.0.0.1:5000"
```

## Getting API Keys

### 1. Anthropic (Claude AI) - **REQUIRED**

Claude AI analyzes and resolves your merge conflicts.

1. Visit [https://console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Go to **API Keys** section
4. Click **Create Key**
5. Copy the key (starts with `sk-ant-api03-`)
6. Set it: `export ANTHROPIC_API_KEY="your-key-here"`

**Pricing**: ~$0.01-0.02 per conflict resolution

### 2. Voyage AI (Code Embeddings) - **Required for RAG**

Voyage AI creates semantic embeddings of your code for intelligent context retrieval.

1. Visit [https://www.voyageai.com](https://www.voyageai.com)
2. Sign up for an account
3. Go to Dashboard → **API Keys**
4. Create a new key
5. Copy the key (starts with `pa-`)
6. Set it: `export VOYAGE_API_KEY="your-key-here"`

**Pricing**: ~$0.001 per 1000 tokens

### 3. GitHub Personal Access Token - **REQUIRED**

1. Visit [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Name it (e.g., "Merj CLI")
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `read:org` (Read org and team membership)
5. Click **Generate token**
6. Copy immediately (won't be shown again!)
7. Use with: `merj auth`

### 4. CodeRabbit Account - 

CodeRabbit provides intelligent code review insights for both sides of the conflict.

1. Visit [https://coderabbit.ai](https://coderabbit.ai)
2. Sign up for free account
3. Install CLI (see Step 3 above)
4. Authenticate: `coderabbit auth login`

## Running Merj

### Basic Workflow

```bash
# 1. Ensure Flask backend is running (in separate terminal)
cd flask_backend && python app.py

# 2. Navigate to your git repository
cd /path/to/your/repo

# 3. Pull changes (Merj will handle conflicts)
merj pull

# 4. Follow the prompts to review and accept/reject resolutions
```

### What Happens During Conflict Resolution

When you run `merj pull` and conflicts are detected:

1. **Detection Phase**
   - Git pull executes and conflicts are identified
   - Conflicted files are listed

2. **Analysis Phase** (for each conflict)
   - CodeRabbit reviews changes on both branches
   - RAG pipeline extracts relevant code context
   - Context is saved to `rag_output/`

3. **Resolution Phase**
   - Claude AI receives:
     - The conflicted file with markers
     - CodeRabbit's analysis
     - Similar code patterns from your codebase
   - Claude generates a clean, merged version

4. **Review Phase**
   - You're shown the AI's resolution
   - Options: Accept, Reject, or View details
   - Accepted resolutions are staged in git

5. **Completion**
   - All accepted files are committed
   - Summary shows resolved/rejected counts

### Example Session

```bash
$ merj pull

🔍 Checking authentication...
✅ Authenticated as: joshuachen

📦 Repository: merj/test-repo
🌿 Current branch: feature-branch
🎯 Remote: origin

Pulling from origin...

⚠️  Merge conflicts detected in 2 files:
  - src/auth.py
  - src/database.py

Starting AI-powered resolution...

[1/2] Resolving: src/auth.py
📊 CodeRabbit: Found 3 code quality issues
🧠 Claude AI: Analyzing conflict...
✨ Resolution ready!

The conflict is between:
- LOCAL: Added password hashing with bcrypt
- REMOTE: Added rate limiting for login attempts

Proposed resolution combines both features safely.

Accept this resolution? (Y/n): Y
✅ Resolution applied to src/auth.py

[2/2] Resolving: src/database.py
...

Summary:
✅ Resolved: 2 files
❌ Rejected: 0 files
⚠️  Failed: 0 files
```

### Advanced Commands

```bash
# Force push changes
merj push --force

# Use a different Claude model
MODEL=claude-3-opus-20240229 merj pull

# Debug mode (verbose output)
DEBUG=true merj pull

# Skip CodeRabbit analysis
SKIP_CODERABBIT=true merj pull
```

## How It Works

```
┌─────────────┐
│  merj pull  │
└─────┬───────┘
      ↓
┌─────────────────────────┐
│ Git Pull & Detect       │
│ Conflicts               │
└─────┬───────────────────┘
      ↓
┌─────────────────────────┐
│ CodeRabbit Analysis     │
│ (Review both branches)  │
└─────┬───────────────────┘
      ↓
┌─────────────────────────┐
│ RAG Pipeline            │
│ (Find similar code)     │
└─────┬───────────────────┘
      ↓
┌─────────────────────────┐
│ Claude AI               │
│ (Generate resolution)   │
└─────┬───────────────────┘
      ↓
┌─────────────────────────┐
│ User Review             │
│ (Accept/Reject)         │
└─────┬───────────────────┘
      ↓
┌─────────────────────────┐
│ Git Commit              │
│ (Stage accepted files)  │
└─────────────────────────┘
```

## Troubleshooting

### Installation Issues

**"merj: command not found"**
```bash
# Re-link the CLI
npm link

# Or use npx
npx merj pull
```

**"Python module not found"**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**"CodeRabbit: command not found"**
```bash
# Reinstall CodeRabbit CLI
curl -fsSL https://cli.coderabbit.ai/install.sh | sh

# Restart terminal or reload shell
source ~/.zshrc  # or ~/.bashrc
```

### API Key Issues

**"Claude API error 401: Unauthorized"**
- Check your Anthropic API key is correct
- Ensure it starts with `sk-ant-api03-`
- Verify at [https://console.anthropic.com](https://console.anthropic.com)

**"Voyage AI authentication failed"**
- Verify your Voyage API key
- Should start with `pa-`
- Check key has access to `voyage-code-3` model

**"GitHub authentication failed"**
- Regenerate token at [GitHub Settings](https://github.com/settings/tokens)
- Ensure token has `repo` scope
- Run `merj auth` again

### Runtime Issues

**"Flask backend connection refused"**
```bash
# Check if Flask is running
curl http://127.0.0.1:5000/api/health

# If not, start it:
cd flask_backend
python app.py
```

**"No conflicts detected"**
```bash
# Verify conflicts exist
git status

# Should show:
# both modified:   filename.py
```

**"ChromaDB error"**
```bash
# Clear ChromaDB cache
rm -rf rag_pipeline/demo_chroma_db/

# Restart Flask backend
```

**"Resolution looks wrong"**
- Check RAG context: `cat rag_output/llm_context.txt`
- Review CodeRabbit findings: `cat rag_output/coderabbit_review.json`
- Try different Claude model: `MODEL=claude-3-opus-20240229`

### Performance Issues

- **Slow resolution**: Reduce RAG context chunks (default: 5)
- **High API costs**: Use smaller Claude model (sonnet vs opus)
- **Memory issues**: Process one conflict at a time

## Testing Your Setup

### 1. Dry Run Test (No API Keys Needed)

Test your installation without making API calls:

```bash
./test_dry_run.sh
```

This validates:
- ✅ All files installed correctly
- ✅ Dependencies are present
- ✅ File permissions are correct

### 2. Full Integration Test

Test with real API calls using a mock conflict:

```bash
export ANTHROPIC_API_KEY="your-key"
./test_full_integration.sh
```

This tests:
- Complete conflict resolution flow
- API integrations
- User approval workflow

### 3. Create a Test Conflict

```bash
# Create test repository
mkdir test-merge && cd test-merge
git init

# Create initial file
echo "original content" > test.txt
git add test.txt
git commit -m "Initial commit"

# Create conflicting changes
git checkout -b feature
echo "feature change" > test.txt
git add test.txt
git commit -m "Feature change"

git checkout main
echo "main change" > test.txt
git add test.txt
git commit -m "Main change"

# Merge with conflicts
git merge feature  # Creates conflict

# Now use Merj
merj pull
```

## Cost Estimates

Per conflict resolution:
- **Claude AI**: $0.01-0.02 (2 API calls)
- **Voyage AI**: <$0.001 (embeddings)
- **CodeRabbit**: Free tier available
- **Total**: ~$0.02 per conflict

Monthly estimates (100 conflicts):
- Light usage: ~$2
- Regular usage: ~$5-10
- Heavy usage: ~$20-30

## Common Workflows

### Working with Feature Branches

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and push
git add .
git commit -m "Add new feature"
merj push

# Later, pull with conflict resolution
git checkout main
git pull origin main
git checkout feature/new-feature
merj pull origin main  # Merj handles conflicts
```

### CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/merge.yml
- name: Setup Merj
  run: |
    npm install -g merj
    merj auth

- name: Resolve conflicts
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    merj pull --auto-accept
```

## Project Structure

```
MergeConflictResolver/
├── bin/
│   ├── index.js                 # CLI entry point
│   ├── merj.js                  # Main commands
│   └── resolve_with_claude.js   # Claude AI integration
├── lib/
│   ├── auth.js                  # GitHub authentication
│   └── git.js                   # Git operations
├── rag_pipeline/
│   ├── chunker.py               # Code parser
│   ├── embedder.py              # Voyage AI integration
│   ├── chroma.py                # Vector database
│   └── local_remote_rag.py      # RAG retrieval
├── flask_backend/
│   └── app.py                   # REST API server
├── scripts/
│   └── review_two_sides_with_cr.py  # CodeRabbit integration
├── rag_output/                  # Generated context files
│   ├── llm_context.txt
│   └── coderabbit_review.json
└── package.json                 # Node dependencies
```

## Support

- **Issues**: [GitHub Issues](https://github.com/Anay-jo/MergeConflictResolver/issues)
- **Documentation**: This README
- **Updates**: Watch the repository for new features

## License

ISC License - See LICENSE file

## Authors

Anay, Sam, Ayush, and Josh

---

**Ready to resolve conflicts intelligently?** Follow the [Quick Start](#quick-start) to begin!