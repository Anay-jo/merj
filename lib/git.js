const simpleGit = require('simple-git');
const path = require('path');
const fs = require('fs');

/**
 * Get git instance for current directory
 */
function getGitInstance() {
  // Check if we're in a git repository
  const cwd = process.cwd();
  const gitDir = path.join(cwd, '.git');
  
  if (!fs.existsSync(gitDir)) {
    throw new Error('Not a git repository. Please run this command in a git repository.');
  }
  
  return simpleGit(cwd);
}

/**
 * Get current repository information
 */
async function getRepoInfo() {
  const git = getGitInstance();
  
  try {
    const remotes = await git.getRemotes(true);
    const currentBranch = await git.revparse(['--abbrev-ref', 'HEAD']);
    
    // Try to find GitHub remote
    const githubRemote = remotes.find(r => r.refs.fetch.includes('github.com'));
    
    let owner = null;
    let repo = null;
    
    if (githubRemote) {
      // Extract owner and repo from URL
      const url = githubRemote.refs.fetch;
      const match = url.match(/github\.com[:/]([^/]+)\/([^/]+)\.git/);
      if (match) {
        owner = match[1];
        repo = match[2].replace('.git', '');
      }
    }
    
    return {
      currentBranch,
      remotes,
      githubRemote,
      owner,
      repo
    };
  } catch (error) {
    throw new Error(`Failed to get repository info: ${error.message}`);
  }
}

/**
 * Check if there are merge conflicts
 */
async function checkMergeConflicts() {
  const git = getGitInstance();
  
  try {
    // Check git status for conflicts
    const status = await git.status();
    
    // Check for conflicted files
    const conflictedFiles = status.conflicted || [];
    
    return {
      hasConflicts: conflictedFiles.length > 0,
      conflictedFiles: conflictedFiles
    };
  } catch (error) {
    throw new Error(`Failed to check merge conflicts: ${error.message}`);
  }
}

/**
 * Pull from remote branch
 */
async function pullFromRemote(remote = 'origin', branch = null) {
  const git = getGitInstance();
  
  try {
    // Get current branch if not specified
    if (!branch) {
      branch = await git.revparse(['--abbrev-ref', 'HEAD']);
    }
    
    console.log(`📥 Pulling from ${remote}/${branch}...`);
    
    // Fetch first
    await git.fetch(remote, branch);
    
    // Pull changes
    const pullResult = await git.pull(remote, branch);
    
    return {
      success: true,
      summary: pullResult.summary,
      files: pullResult.files || []
    };
  } catch (error) {
    // Check if error is due to merge conflicts
    const conflicts = await checkMergeConflicts();
    
    if (conflicts.hasConflicts) {
      return {
        success: false,
        hasConflicts: true,
        conflictedFiles: conflicts.conflictedFiles,
        error: 'Merge conflicts detected'
      };
    }
    
    throw error;
  }
}

/**
 * Get conflicted file contents
 */
async function getConflictedFileContent(filePath) {
  const fs = require('fs').promises;
  
  try {
    const content = await fs.readFile(filePath, 'utf8');
    
    // Parse conflict markers
    const conflictRegex = /^<<<<<<< (.*?)\n(.*?)^=======\n(.*?)^>>>>>>> (.*?)$/gms;
    const conflicts = [];
    
    let match;
    while ((match = conflictRegex.exec(content)) !== null) {
      conflicts.push({
        oursMarker: match[1],
        oursContent: match[2],
        theirsContent: match[3],
        theirsMarker: match[4]
      });
    }
    
    return {
      content,
      hasConflicts: conflicts.length > 0,
      conflicts
    };
  } catch (error) {
    throw new Error(`Failed to read conflicted file: ${error.message}`);
  }
}

/**
 * Push to remote branch
 */
async function pushToRemote(remote = 'origin', branch = null, force = false) {
  const git = getGitInstance();
  
  try {
    // Get current branch if not specified
    if (!branch) {
      branch = await git.revparse(['--abbrev-ref', 'HEAD']);
    }
    
    console.log(`📤 Pushing to ${remote}/${branch}...`);
    
    // Push changes
    if (force) {
      await git.push(remote, branch, ['--force']);
    } else {
      await git.push(remote, branch);
    }
    
    return {
      success: true,
      message: `Successfully pushed to ${remote}/${branch}`
    };
  } catch (error) {
    throw new Error(`Failed to push: ${error.message}`);
  }
}

module.exports = {
  getGitInstance,
  getRepoInfo,
  checkMergeConflicts,
  pullFromRemote,
  getConflictedFileContent,
  pushToRemote
};

