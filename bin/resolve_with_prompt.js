#!/usr/bin/env node
/**
 * Wrapper script that connects resolve_with_claude.js and cli_resolution_handler.js
 * Runs the full flow: Claude resolution -> User prompt -> Apply changes
 */

const fs = require('fs');
const path = require('path');
const { spawn, spawnSync } = require('child_process');
const chalk = require('chalk');

// Import the CLI resolution handler (same bin folder)
const { handleResolvedConflict } = require('./cli_resolution_handler');

// Get the directory where resolve_with_claude will save files
const OUTPUT_ROOT = process.env.MERGE_OUTPUT_ROOT || '/tmp/merged_suggestions';

function assertInGitRepo() {
  const r = spawnSync('git', ['rev-parse', '--show-toplevel'], { encoding: 'utf-8' });
  if (r.status !== 0) {
    console.error('❌ Not a git repository. Run inside a repo with .git present.');
    process.exit(1);
  }
  return r.stdout.trim();
}

function listConflictedFiles(cwd) {
  const r = spawnSync('git', ['ls-files', '-u'], { cwd, encoding: 'utf-8' });
  if (r.status !== 0) return [];
  const lines = r.stdout.trim().split('\n').filter(Boolean);
  const files = new Set();
  for (const ln of lines) {
    const parts = ln.trim().split(/\s+/);
    const file = parts[3];
    if (file) files.add(file);
  }
  return [...files];
}

/**
 * Run resolve_with_claude.js and capture the output file path
 */
async function runClaudeResolution(targetFile) {
  return new Promise((resolve, reject) => {
    console.log(chalk.cyan('\n🤖 Requesting AI resolution from Claude...\n'));

    const args = targetFile ? ['--file', targetFile] : [];
    const resolveProcess = spawn('node', [
      path.join(__dirname, 'resolve_with_claude.js'),
      ...args
    ], {
      encoding: 'utf-8',
      env: { ...process.env }
    });

    let stdout = '';
    let stderr = '';
    let outputPath = null;
    let analysisStarted = false;

    resolveProcess.stdout.on('data', (data) => {
      const str = data.toString();
      stdout += str;

      // Look for the output path in the console output
      const match = str.match(/Wrote merged suggestion to: (.+)/);
      if (match) {
        outputPath = match[1].trim();
      }

      // Show Claude's analysis to user (everything between analysis start and the "Wrote merged" line)
      if (str.includes('Claude\'s Analysis:') || str.includes('🧠')) {
        analysisStarted = true;
      }

      if (analysisStarted && !str.includes('Wrote merged suggestion')) {
        process.stdout.write(str);
      }

      if (str.includes('✅ Wrote merged suggestion')) {
        analysisStarted = false;
        // Don't print the resolved code to stdout, we'll handle it in the prompt
      }
    });

    resolveProcess.stderr.on('data', (data) => {
      stderr += data.toString();
      process.stderr.write(data);
    });

    resolveProcess.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`resolve_with_claude.js exited with code ${code}`));
      } else if (!outputPath) {
        reject(new Error('Could not find output path from resolve_with_claude.js'));
      } else {
        resolve(outputPath);
      }
    });

    resolveProcess.on('error', (err) => {
      reject(err);
    });
  });
}

/**
 * Main wrapper function
 */
async function main() {
  console.log(chalk.magenta.bold('='.repeat(70)));
  console.log(chalk.magenta.bold('  MERJ AI-POWERED CONFLICT RESOLUTION'));
  console.log(chalk.magenta.bold('='.repeat(70)));

  const repoRoot = assertInGitRepo();

  // Parse arguments
  const argv = process.argv.slice(2);
  let targetFile = null;

  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if ((a === '--file' || a === '-f') && argv[i+1]) {
      targetFile = argv[++i];
    } else if (a === '--help' || a === '-h') {
      console.log('\nUsage: resolve_with_prompt [--file <path>]');
      console.log('  Resolves merge conflicts with AI and prompts for user confirmation\n');
      console.log('Options:');
      console.log('  --file, -f <path>  Specify which conflicted file to resolve');
      console.log('  --help, -h         Show this help message\n');
      console.log('If no file is specified, the first conflicted file will be selected automatically.');
      process.exit(0);
    }
  }

  // If no file specified, get first conflicted file
  if (!targetFile) {
    const conflicted = listConflictedFiles(repoRoot);
    if (conflicted.length === 0) {
      console.error('\n❌ No conflicted files detected in the repository.');
      console.error('   Run this command after a merge conflict occurs.\n');
      process.exit(1);
    }
    targetFile = conflicted[0];
    console.log(chalk.yellow(`\n📄 Auto-selected conflicted file: ${targetFile}`));

    if (conflicted.length > 1) {
      console.log(chalk.gray(`   (${conflicted.length - 1} other conflicted file(s) remaining)`));
    }
  }

  const conflictFilePath = path.join(repoRoot, targetFile);

  try {
    // Step 1: Run Claude resolution
    const resolvedPath = await runClaudeResolution(targetFile);

    console.log(chalk.gray(`\n✨ AI resolution generated and saved`));

    // Step 2: Use the CLI resolution handler to prompt user
    console.log(chalk.cyan('\n' + '-'.repeat(70)));
    const success = await handleResolvedConflict(resolvedPath, conflictFilePath);

    // Step 3: Final status
    if (success) {
      console.log(chalk.green.bold('='.repeat(70)));
      console.log(chalk.green.bold('  🎉 SUCCESS: Conflict resolved with AI assistance!'));
      console.log(chalk.green.bold('='.repeat(70)));
      console.log(chalk.cyan('\nNext steps:'));
      console.log(chalk.white('  1. Review the changes: ') + chalk.yellow('git diff --cached'));
      console.log(chalk.white('  2. Commit the merge:  ') + chalk.yellow('git commit'));
      console.log();
      process.exit(0);
    } else {
      console.log(chalk.yellow.bold('\n' + '='.repeat(70)));
      console.log(chalk.yellow.bold('  ⚠️  Resolution rejected - manual merge required'));
      console.log(chalk.yellow.bold('='.repeat(70)));
      console.log(chalk.gray('\nThe AI suggestion was saved but not applied.'));
      console.log(chalk.gray('You can manually resolve the conflict or try again.\n'));
      process.exit(1);
    }

  } catch (error) {
    console.error(chalk.red('\n❌ Error:'), error.message);
    if (error.message.includes('ANTHROPIC_API_KEY')) {
      console.error(chalk.yellow('\nMake sure ANTHROPIC_API_KEY is set in your environment.'));
    }
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main().catch(err => {
    console.error(chalk.red('Fatal error:'), err);
    process.exit(1);
  });
}

module.exports = { runClaudeResolution };