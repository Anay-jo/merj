#!/usr/bin/env node

const { program } = require('commander');
const { storeToken, testAuthentication, getAuthenticatedClient } = require('../lib/auth');
const { pullFromRemote, checkMergeConflicts, getRepoInfo, pushToRemote } = require('../lib/git');
const inquirer = require('inquirer');

program
  .name('merj')
  .description('A CLI that automatically resolves merge conflicts upon git pulls')
  .version('1.0.0');

// Auth command to set up GitHub token
program
  .command('auth')
  .description('Set up GitHub authentication with Personal Access Token')
  .action(async () => {
    const questions = [
      {
        type: 'password',
        name: 'token',
        message: 'Enter your GitHub Personal Access Token:',
        mask: '*',
        validate: (input) => {
          if (!input || input.length === 0) {
            return 'Token cannot be empty';
          }
          if (!input.startsWith('ghp_') && !input.startsWith('github_pat_')) {
            return 'Invalid token format. Token should start with ghp_ or github_pat_';
          }
          return true;
        }
      }
    ];

    const answers = await inquirer.prompt(questions);
    
    if (storeToken(answers.token)) {
      console.log(' Token stored successfully');
      
      // Test the authentication
      console.log('Testing authentication...');
      const result = await testAuthentication();
      
      if (result.authenticated) {
        console.log(` Successfully authenticated as ${result.username}`);
      } else {
        console.log(` Authentication failed: ${result.error}`);
        console.log('Please check your token and try again.');
      }
    } else {
      console.log(' Failed to store token');
    }
  });

program
  .command('pull')
  .description('Pull changes from remote and automatically resolve merge conflicts')
  .option('-r, --remote <remote>', 'Remote name', 'origin')
  .option('-b, --branch <branch>', 'Branch name', null)
  .action(async (options) => {
    try {
      // Check authentication
      const authResult = await testAuthentication();
      
      if (!authResult.authenticated) {
        console.log(' Not authenticated. Please run: merj auth');
        console.log('   You need a GitHub Personal Access Token to use this feature.');
        process.exit(1);
      }
      
      console.log(` Authenticated as ${authResult.username}`);
      
      // Get repository info
      const repoInfo = await getRepoInfo();
      console.log(` Repository: ${repoInfo.owner}/${repoInfo.repo}`);
      console.log(` Current branch: ${repoInfo.currentBranch}`);
      
      // Get authenticated GitHub client
      const octokit = getAuthenticatedClient();
      
      // Check for existing conflicts first
      const existingConflicts = await checkMergeConflicts();
      if (existingConflicts.hasConflicts) {
        console.log('\n  MERGE CONFLICTS ALREADY EXIST!');
        console.log(`Found ${existingConflicts.conflictedFiles.length} conflicted file(s):\n`);
        
        existingConflicts.conflictedFiles.forEach((file, index) => {
          console.log(`  ${index + 1}. ${file}`);
        });
        
        console.log('\n🔧 Conflict resolution will be implemented here');
        // TODO: Implement conflict resolution logic
        return;
      }
      
      // Pull from remote
      const pullResult = await pullFromRemote(options.remote, options.branch);
      
      if (pullResult.success) {
        console.log('Pull completed successfully');
        if (pullResult.summary) {
          console.log(pullResult.summary);
        }
      } else if (pullResult.hasConflicts) {
        console.log('\n  MERGE CONFLICTS DETECTED!');
        console.log(`Found ${pullResult.conflictedFiles.length} conflicted file(s):\n`);
        
        pullResult.conflictedFiles.forEach((file, index) => {
          console.log(`  ${index + 1}. ${file}`);
        });
        
        console.log('\n🔧 Conflict resolution will be implemented here');
        // TODO: Implement conflict resolution logic
      }
      
    } catch (error) {
      console.error('Error:', error.message);
      process.exit(1);
    }
  });

program
  .command('push')
  .description('Push changes to remote repository')
  .option('-r, --remote <remote>', 'Remote name', 'origin')
  .option('-b, --branch <branch>', 'Branch name', null)
  .option('-f, --force', 'Force push', false)
  .action(async (options) => {
    try {
      // Check authentication
      const authResult = await testAuthentication();
      
      if (!authResult.authenticated) {
        console.log('Not authenticated. Please run: merj auth');
        console.log('   You need a GitHub Personal Access Token to use this feature.');
        process.exit(1);
      }
      
      console.log(`Authenticated as ${authResult.username}`);
      
      // Get repository info
      const repoInfo = await getRepoInfo();
      console.log(`Repository: ${repoInfo.owner}/${repoInfo.repo}`);
      console.log(`Current branch: ${repoInfo.currentBranch}`);
      
      // Get authenticated GitHub client
      const octokit = getAuthenticatedClient();
      
      // Push to remote
      const pushResult = await pushToRemote(options.remote, options.branch, options.force);
      
      if (pushResult.success) {
        console.log(`${pushResult.message}`);
      }
      
    } catch (error) {
      console.error('Error:', error.message);
      process.exit(1);
    }
  });

program.parse();
