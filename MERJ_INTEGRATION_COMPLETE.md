# Merj Integration Complete - AI-Powered Conflict Resolution

## What Was Done

The full AI-powered conflict resolution pipeline has been integrated into `merj pull`. The command now automatically:

1. **Detects conflicts** after `git pull`
2. **Generates RAG context** from Last Common Ancestor codebase
3. **Runs CodeRabbit analysis** on both branches
4. **Calls Claude AI** to analyze and resolve each conflict
5. **Prompts user** to accept/reject each resolution
6. **Applies changes** and stages resolved files in git

## Changes Made

### bin/merj.js

#### Added Helper Function (line 17-29)
```javascript
function listConflictedFiles() {
  const r = run('git', ['ls-files', '-u']);
  if (r.status !== 0 || !r.stdout.trim()) return [];

  const lines = r.stdout.trim().split('\n');
  const files = new Set();
  for (const ln of lines) {
    const parts = ln.trim().split(/\s+/);
    const file = parts[3];
    if (file) files.add(file);
  }
  return [...files];
}
```

#### Added Resolution Loop (lines 207-271)
After RAG and CodeRabbit analysis complete, the code now:

1. **Lists all conflicted files**
```javascript
const conflictedFiles = listConflictedFiles();
console.log(`📋 Found ${conflictedFiles.length} conflicted file(s)`);
```

2. **Processes each file**
```javascript
for (let i = 0; i < conflictedFiles.length; i++) {
  const file = conflictedFiles[i];

  // Calls resolve_with_prompt.js which:
  // - Runs resolve_with_claude.js (Claude AI analysis + resolution)
  // - Shows user the CLI confirmation prompt
  // - Applies changes if accepted
  const resolveCmd = run('node', [
    path.join(__dirname, 'resolve_with_prompt.js'),
    '--file',
    file
  ], { stdio: 'inherit' });

  // Track results
  if (resolveCmd.status === 0) resolvedCount++;
  else if (resolveCmd.status === 1) rejectedCount++;
  else failedCount++;
}
```

3. **Shows summary and appropriate exit message**
```javascript
console.log('📊 RESOLUTION SUMMARY');
console.log(`✅ Resolved and applied: ${resolvedCount}`);
console.log(`⚠️  Rejected by user: ${rejectedCount}`);
console.log(`❌ Failed: ${failedCount}`);

if (resolvedCount === conflictedFiles.length) {
  console.log('🎉 All conflicts resolved!');
  process.exit(0);
} else {
  console.log('⚠️ Some conflicts remain');
  process.exit(2);
}
```

## How It Works

### Complete Flow

```
merj pull
    ↓
git pull (detects conflicts)
    ↓
Extract diffs (local vs base, remote vs base)
    ↓
Send to RAG pipeline (Flask server)
    ↓  → Saves: rag_output/llm_context.txt
    ↓
Run CodeRabbit analysis
    ↓  → Saves: rag_output/coderabbit_review.json
    ↓
Display summaries to user
    ↓
For each conflicted file:
    ↓
    resolve_with_prompt.js
        ↓
        resolve_with_claude.js
            ↓
            Load RAG context (rag_output/llm_context.txt)
            Load CodeRabbit findings (rag_output/coderabbit_review.json)
            ↓
            Call Claude API (description prompt)
            → Shows analysis to user
            ↓
            Call Claude API (resolution prompt)
            → Generates clean merged code
            ↓
            Save to /tmp/merged_suggestions/
        ↓
        cli_resolution_handler.js
            ↓
            Show file info to user
            Offer to view resolved file (y/n)
            Ask to accept/reject (y/n)
            ↓
            If accepted:
                - Backup original file
                - Replace with resolved code
                - git add <file>
                - Delete temp file
            ↓
            Return status (0=accepted, 1=rejected)
    ↓
Track results (resolved/rejected/failed)
    ↓
Show summary
    ↓
Exit (0 if all resolved, 2 if some remain)
```

## Usage

### Basic Usage
```bash
# Run merj pull as usual
merj pull

# If conflicts detected, it will automatically:
# 1. Generate RAG context
# 2. Run CodeRabbit analysis
# 3. For each conflict:
#    - Show Claude's analysis
#    - Ask if you want to view the resolved file
#    - Ask to accept/reject the resolution
# 4. Show summary of all resolutions
```

### Environment Variables Required
```bash
# For Claude AI
export ANTHROPIC_API_KEY=your_key_here

# Optional: Custom model
export MODEL=claude-3-5-sonnet-20241022

# Optional: Custom output directory
export MERGE_OUTPUT_ROOT=/custom/path  # Default: /tmp/merged_suggestions
```

### For RAG Pipeline
The RAG pipeline must be running:
```bash
# In a separate terminal
cd rag_pipeline
python app.py
# Runs on http://127.0.0.1:5000
```

## Example Output

```
➡️  git pull
Auto-merging src/auth.py
CONFLICT (content): Merge conflict in src/auth.py
⚠️  Merge conflicts detected — running CodeRabbit side reviews…

📡 Sending diff data to RAG pipeline...
✅ RAG processing completed successfully
   - Found 3 similar code patterns
   - Saved context to rag_output/llm_context.txt

📝 Saved CodeRabbit findings to rag_output/coderabbit_review.json

🧠 CodeRabbit (main since BASE)
  1. src/auth.py:45 — Missing error handling in authenticate method

🧠 CodeRabbit (local since BASE)
  1. src/auth.py:52 — Consider using bcrypt for password hashing

🤖 Starting AI-powered conflict resolution...

📋 Found 1 conflicted file(s):
   1. src/auth.py

======================================================================
📄 Processing file 1/1: src/auth.py
======================================================================

📚 Loaded RAG context from: rag_output/llm_context.txt
   Size: 2.4KB, Lines: 89
🐰 Loaded CodeRabbit findings from: rag_output/coderabbit_review.json
   Found 2 total findings

Claude Analysis:

The conflict occurs in the UserManager class around lines 29-48.

OURS (local branch) added:
- New password hashing method using simplified approach

THEIRS (main branch) added:
- Complete authentication system with session management
- Multiple helper methods (_hash_password, _verify_password, _generate_token)

Recommendation: Accept the main branch changes as they provide a more complete
authentication implementation. The local branch's simpler approach is already
included in the main branch's more comprehensive solution.

✅ Wrote merged suggestion to: /tmp/merged_suggestions/src/auth.py

======================================================================
  🤖 AI Merge Conflict Resolution
======================================================================

📄 Conflicted file: src/auth.py
✨ AI resolution saved at: /tmp/merged_suggestions/src/auth.py
   Size: 3.2 KB, Lines: 95

Would you like to view the resolved file? (y/n): n

💡 Tip: You can manually review at: /tmp/merged_suggestions/src/auth.py

⚠️  This will replace the conflicted file with the AI resolution.
Accept and apply the AI resolution? (y/n): y

📦 Backup saved: src/auth.py.backup.1698765432
✅ Applied resolution to: src/auth.py
✅ File staged in git
🗑️  Cleaned up temp file

✅ File 1/1 resolved successfully

======================================================================
📊 RESOLUTION SUMMARY
======================================================================
✅ Resolved and applied: 1
⚠️  Rejected by user: 0
❌ Failed: 0
📋 Total conflicts: 1

🎉 All conflicts resolved! Complete the merge:
   git merge --continue
   (or git rebase --continue if rebasing)
```

## Data Flow

### RAG Context Format (rag_output/llm_context.txt)
```
============================================================
MERGE CONFLICT CONTEXT FOR LLM
============================================================

LOCAL CHANGES (Your Branch):
----------------------------------------

[1] File: sample_app.py
    Lines: 29-48
    Type: function
    Code:
    def add_user(self, username: str, email: str, password: str) -> Dict:
        ...

REMOTE CHANGES (Main Branch):
----------------------------------------

[1] File: sample_app.py
    Lines: 20-73
    Type: class
    Code:
    class UserManager:
        ...
```

### CodeRabbit Format (rag_output/coderabbit_review.json)
```json
{
  "mainBranchReview": {
    "issues": [
      {
        "file": "src/auth.py",
        "line": 45,
        "message": "Missing error handling"
      }
    ]
  },
  "localBranchReview": {
    "issues": [
      {
        "file": "src/auth.py",
        "line": 52,
        "message": "Consider using bcrypt"
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Claude AI Input
Both `buildDescriptionPrompt()` and `buildResolutionPrompt()` receive:
```javascript
{
  filePath: "src/auth.py",
  conflictedCode: "...file content with <<<<<<< markers...",
  ragContext: "...content from llm_context.txt..." || null,
  codeRabbitContext: "...formatted findings..." || null
}
```

## Exit Codes

- **0**: All conflicts resolved successfully
- **1**: Pull failed (no conflicts detected)
- **2**: Conflicts remain (partial resolution or user rejection)

## Testing

### Test with Real Conflict
```bash
# Run the test script
./test_claude_merge_resolution.sh

# This creates a test repo with a real conflict and runs the full flow
```

### Manual Test
```bash
# 1. Create a branch and make changes
git checkout -b test-feature
echo "local change" >> test.txt
git add test.txt && git commit -m "local"

# 2. Go back to main and make conflicting change
git checkout main
echo "main change" >> test.txt
git add test.txt && git commit -m "main"

# 3. Run merj pull to trigger AI resolution
merj pull origin main
```

## Troubleshooting

### "Missing ANTHROPIC_API_KEY"
```bash
export ANTHROPIC_API_KEY=your_key_here
```

### "Error connecting to RAG pipeline"
```bash
# Start the RAG pipeline server
cd rag_pipeline
python app.py
```

### "CodeRabbit helper failed"
Check that `scripts/review_two_sides_with_cr.py` exists and is executable.

### Resolution Rejected Multiple Times
If Claude's resolutions don't match your expectations:
1. Check the RAG context quality in `rag_output/llm_context.txt`
2. Review CodeRabbit findings in `rag_output/coderabbit_review.json`
3. Consider adjusting the prompts in `resolve_with_claude.js`

## Next Steps

1. **Test with real conflicts**: Run `merj pull` in your actual repository
2. **Verify RAG pipeline**: Ensure the Flask server is running and returning good context
3. **Check API limits**: Monitor your Anthropic API usage
4. **Iterate on prompts**: Adjust `buildDescriptionPrompt()` and `buildResolutionPrompt()` based on results

## Files Modified

- `bin/merj.js` - Added integration code (lines 17-29, 207-271)

## Files Used (No Changes)

- `bin/resolve_with_prompt.js` - Wrapper that connects Claude + CLI handler
- `bin/resolve_with_claude.js` - Claude AI integration with RAG/CodeRabbit loading
- `bin/cli_resolution_handler.js` - User confirmation and file application
- `rag_output/llm_context.txt` - RAG context (generated by pipeline)
- `rag_output/coderabbit_review.json` - CodeRabbit findings (generated by merj)

## Architecture Benefits

1. **Separation of Concerns**: Each component has a single responsibility
2. **No Modifications to Working Code**: Integration uses existing components
3. **Graceful Degradation**: Continues if RAG/CodeRabbit unavailable
4. **User Control**: Always asks for confirmation before applying changes
5. **Safety**: Creates backups before modifying files
6. **Git Integration**: Automatically stages resolved files
