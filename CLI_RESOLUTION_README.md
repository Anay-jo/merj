# CLI Resolution Handler for Merj Pull

## Overview
This module handles the final step of the AI-powered merge conflict resolution in `merj pull`. It takes the LLM's resolved file and manages user interaction, confirmation, and application of the changes.

## Components

### 1. `cli_resolution_handler.js`
The main handler module with:
- `handleResolvedConflict(tempFilePath, conflictFilePath)` - Main function
- `applyResolution()` - Applies changes and stages in git
- `cleanupTempFile()` - Removes temporary files

### 2. `resolve_with_prompt.js`
Wrapper script that connects both components:
- Runs `resolve_with_claude.js` to get AI resolution
- Calls `cli_resolution_handler.js` for user confirmation
- Handles the complete flow seamlessly

### 3. `test_claude_merge_resolution.sh`
Complete test script that:
- Creates a test git repo with real merge conflicts
- Runs the full AI resolution flow
- Tests the complete integration

## Quick Start

### Test the Integration
```bash
# Run the test script to see the full flow
chmod +x test_claude_merge_resolution.sh
./test_claude_merge_resolution.sh

# Or test with a real conflict in your repo
node bin/resolve_with_prompt.js
```

### Integration into Merj Pull

In your existing merj pull command, after the LLM generates a resolution:

```javascript
const { handleResolvedConflict } = require('./cli_resolution_handler');
const fs = require('fs').promises;

// After LLM resolves the conflict...
const tempFile = `.merj-temp/resolved-${Date.now()}.txt`;
await fs.writeFile(tempFile, llmResolution);

// Handle user interaction and apply changes
const accepted = await handleResolvedConflict(tempFile, conflictedFile);

if (accepted) {
  console.log('✅ Conflict resolved!');
} else {
  console.log('⚠️ Manual resolution needed');
}
```

## Flow

1. **LLM Output**: LLM writes resolved file to temp `.txt` file
2. **Display**: Shows user where the file is located
3. **Optional View**: User can choose to view the full resolved file
4. **Confirmation**: User types 'y' or 'n' to accept/reject
5. **Apply**: If accepted:
   - Backs up current file
   - Replaces with LLM resolution
   - Stages file in git
   - Deletes temp file
6. **Cleanup**: Temp file is removed (or kept if rejected for reference)

## Features

✅ **Simple** - Just pass temp file path and conflict file path
✅ **Safe** - Creates backup before applying changes
✅ **Git Integration** - Automatically stages resolved file
✅ **User-Friendly** - Clear prompts and colored output
✅ **Clean** - Handles temp file cleanup

## Customization

You can easily modify the behavior:

- **Change prompts**: Edit the `question()` calls in `handleResolvedConflict()`
- **Skip file display**: Remove the "view file" prompt
- **Keep temp files**: Pass `keepFile: true` to `cleanupTempFile()`
- **Add diff display**: Use `git diff` to show changes before applying

## Next Steps

1. **Test with real LLM output**: Replace mock content with actual LLM resolution
2. **Add to main CLI**: Integrate into your `merj pull` command
3. **Handle multiple files**: Extend to handle multiple conflicted files
4. **Add diff view**: Show side-by-side or unified diff before confirmation

## Example Output

```
======================================================================
  🤖 AI Merge Conflict Resolution
======================================================================

📄 Conflicted file: ./src/auth.py
✨ AI resolution saved at: ./temp/resolved-123456.txt
   Size: 2.34 KB, Lines: 89

Would you like to view the resolved file? (y/n): n

💡 Tip: You can manually review at: ./temp/resolved-123456.txt

⚠️  This will replace the conflicted file with the AI resolution.
Accept and apply the AI resolution? (y/n): y

📦 Backup saved: ./src/auth.py.backup.1698765432
✅ Applied resolution to: ./src/auth.py
✅ File staged in git
🗑️  Cleaned up temp file: ./temp/resolved-123456.txt

✨ Success! The conflict has been resolved.
Next step: Run "git commit" to complete the merge.
```