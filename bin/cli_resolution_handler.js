#!/usr/bin/env node
/**
 * CLI Resolution Handler
 * Handles the final step of applying LLM-resolved conflicts
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');
const readline = require('readline');
const chalk = require('chalk');

// Create readline interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Promisify question for async/await
const question = (query) => new Promise((resolve) => rl.question(query, resolve));

/**
 * Main function to handle resolved conflict
 * @param {string} tempFilePath - Path to the temp .txt file with LLM resolution
 * @param {string} conflictFilePath - Path to the actual conflicted file
 */
async function handleResolvedConflict(tempFilePath, conflictFilePath) {
  try {
    console.log(chalk.cyan('\n' + '='.repeat(70)));
    console.log(chalk.cyan.bold('  🤖 AI Merge Conflict Resolution'));
    console.log(chalk.cyan('='.repeat(70) + '\n'));

    // Check if temp file exists
    try {
      await fs.access(tempFilePath);
    } catch {
      console.error(chalk.red(`❌ Error: Resolution file not found at ${tempFilePath}`));
      return false;
    }

    // Read the resolved content
    const resolvedContent = await fs.readFile(tempFilePath, 'utf8');

    // Get file size for display
    const stats = await fs.stat(tempFilePath);
    const sizeKB = (stats.size / 1024).toFixed(2);

    console.log(chalk.yellow(`📄 Conflicted file: ${conflictFilePath}`));
    console.log(chalk.green(`✨ AI resolution saved at: ${tempFilePath}`));
    console.log(chalk.gray(`   Size: ${sizeKB} KB, Lines: ${resolvedContent.split('\n').length}`));
    console.log();

    // Ask if user wants to see the content
    const showContent = await question(
      chalk.cyan('Would you like to view the resolved file? (y/n): ')
    );

    if (showContent.toLowerCase() === 'y' || showContent.toLowerCase() === 'yes') {
      console.log(chalk.gray('\n' + '-'.repeat(70)));
      console.log(chalk.white(resolvedContent));
      console.log(chalk.gray('-'.repeat(70) + '\n'));
    } else {
      console.log(chalk.gray(`\n💡 Tip: You can manually review at: ${tempFilePath}\n`));
    }

    // Ask for confirmation to apply
    console.log(chalk.yellow.bold('\n⚠️  This will replace the conflicted file with the AI resolution.'));
    const confirm = await question(
      chalk.cyan.bold('Accept and apply the AI resolution? (y/n): ')
    );

    if (confirm.toLowerCase() === 'y' || confirm.toLowerCase() === 'yes') {
      // Apply the resolution
      await applyResolution(tempFilePath, conflictFilePath);
      return true;
    } else {
      console.log(chalk.yellow('\n❌ Resolution rejected.'));
      console.log(chalk.gray('The conflicted file remains unchanged.'));
      console.log(chalk.gray(`The AI suggestion is still available at: ${tempFilePath}`));
      return false;
    }

  } catch (error) {
    console.error(chalk.red('\n❌ Error handling resolution:'), error.message);
    return false;
  } finally {
    rl.close();
  }
}

/**
 * Apply the resolution by replacing the conflicted file
 */
async function applyResolution(tempFilePath, conflictFilePath) {
  try {
    // Read the resolved content
    const resolvedContent = await fs.readFile(tempFilePath, 'utf8');

    // Backup the current conflicted file (just in case)
    const backupPath = `${conflictFilePath}.backup.${Date.now()}`;
    const conflictedContent = await fs.readFile(conflictFilePath, 'utf8');
    await fs.writeFile(backupPath, conflictedContent);
    console.log(chalk.gray(`\n📦 Backup saved: ${backupPath}`));

    // Write the resolved content to the original file
    await fs.writeFile(conflictFilePath, resolvedContent);
    console.log(chalk.green(`✅ Applied resolution to: ${conflictFilePath}`));

    // Stage the file in git
    try {
      execSync(`git add "${conflictFilePath}"`, { stdio: 'pipe' });
      console.log(chalk.green(`✅ File staged in git`));
    } catch (gitError) {
      console.log(chalk.yellow(`⚠️  Could not stage file: ${gitError.message}`));
    }

    // Delete the temp file
    await fs.unlink(tempFilePath);
    console.log(chalk.gray(`🗑️  Cleaned up temp file: ${tempFilePath}`));

    console.log(chalk.green.bold('\n✨ Success! The conflict has been resolved.'));
    console.log(chalk.cyan('Next step: Run "git commit" to complete the merge.\n'));

  } catch (error) {
    console.error(chalk.red('❌ Error applying resolution:'), error.message);
    throw error;
  }
}

/**
 * Cleanup function to remove temp file if user rejects
 */
async function cleanupTempFile(tempFilePath, keepFile = false) {
  if (!keepFile) {
    try {
      await fs.unlink(tempFilePath);
      console.log(chalk.gray(`\n🗑️  Temp file deleted: ${tempFilePath}`));
    } catch (error) {
      // File might not exist or already deleted
      if (error.code !== 'ENOENT') {
        console.log(chalk.yellow(`⚠️  Could not delete temp file: ${error.message}`));
      }
    }
  }
}

// Export for use in main CLI
module.exports = {
  handleResolvedConflict,
  applyResolution,
  cleanupTempFile
};

// If running directly (for testing)
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.log(chalk.yellow('Usage: node cli_resolution_handler.js <temp-file> <conflict-file>'));
    console.log(chalk.gray('Example: node cli_resolution_handler.js ./temp/resolved.txt ./src/auth.py'));
    process.exit(1);
  }

  const [tempFile, conflictFile] = args;

  handleResolvedConflict(tempFile, conflictFile).then(success => {
    process.exit(success ? 0 : 1);
  });
}