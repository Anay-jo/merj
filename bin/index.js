#!/usr/bin/env node
/* eslint-disable no-console */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { program } = require('commander');
const inquirer = require('inquirer');
const simpleGit = require('simple-git');
const { Octokit } = require('@octokit/rest');
require('dotenv').config();

const PKG = safeRequire(path.join(__dirname, '..', 'package.json')) || { version: '1.0.0' };
const SCRIPT_HELPER = path.resolve(__dirname, '..', 'scripts', 'review_two_sides_with_cr.py');

/* --------------------------- small utilities --------------------------- */

function safeRequire(p) {
  try { return require(p); } catch { return null; }
}

function run(cmd, args, opts = {}) {
  return spawnSync(cmd, args, { encoding: 'utf-8', stdio: 'pipe', ...opts });
}

function runInherit(cmd, args, opts = {}) {
  return spawnSync(cmd, args, { stdio: 'inherit', ...opts });
}

function assertInGitRepo() {
  const r = run('git', ['rev-parse', '--show-toplevel']);
  if (r.status !== 0) {
    console.error('❌ Not a git repository. Run inside a repo with .git present.');
    process.exit(1);
  }
  return r.stdout.trim();
}

function hasConflicts(cwd = process.cwd()) {
  const r = run('git', ['ls-files', '-u'], { cwd });
  return r.status === 0 && r.stdout.trim().length > 0;
}

function getCurrentBranch() {
  const r = run('git', ['rev-parse', '--abbrev-ref', 'HEAD']);
  return r.status === 0 ? r.stdout.trim() : 'unknown';
}

function getRemoteUrl(remote = 'origin') {
  const r = run('git', ['remote', 'get-url', remote]);
  return r.status === 0 ? r.stdout.trim() : null;
}

function getRepoInfo() {
  const remoteUrl = getRemoteUrl('origin') || '';
  const m = remoteUrl.match(/github\.com[:/](.+?)\/(.+?)(?:\.git)?$/i);
  const owner = m ? m[1] : 'unknown';
  const repo = m ? m[2] : 'unknown';
  return {
    remoteUrl,
    owner,
    repo,
    currentBranch: getCurrentBranch(),
  };
}

function ensureDotenvAt(repoRoot) {
  const envPath = path.join(repoRoot, '.env');
  if (!fs.existsSync(envPath)) fs.writeFileSync(envPath, '', 'utf-8');
  return envPath;
}

function getAuthenticatedClient() {
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || process.env.GITHUB_PAT;
  if (!token) return null;
  try {
    return new Octokit({ auth: token });
  } catch {
    return null;
  }
}

async function checkAuth(octokit) {
  try {
    const { data } = await octokit.rest.users.getAuthenticated();
    return { authenticated: true, username: data.login };
  } catch (e) {
    return { authenticated: false, error: e.message };
  }
}

async function pushToRemote(remote = 'origin', branch = getCurrentBranch(), opts = {}) {
  const git = simpleGit();
  try {
    await git.push(remote, branch, opts.force ? ['--force-with-lease'] : []);
    return { success: true, message: `Pushed ${branch} to ${remote}` };
  } catch (e) {
    return { success: false, message: e.message };
  }
}

function getUpstream() {
  const r = run('git', ['rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}']);
  if (r.status !== 0) return null;
  const s = r.stdout.trim(); // "origin/main"
  const slash = s.indexOf('/');
  if (slash === -1) return null;
  return { remote: s.slice(0, slash), branch: s.slice(slash + 1) };
}

function readJsonSafe(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf-8')); }
  catch { return null; }
}

function readTextSafe(p) {
  try { return fs.readFileSync(p, 'utf-8'); }
  catch { return null; }
}

/* ----------------------- CodeRabbit side-review hook ------------------- */

function runCodeRabbitSideReviews(mainRef = 'origin/main', repoRoot = process.cwd()) {
  if (!fs.existsSync(SCRIPT_HELPER)) {
    console.error(`⚠️  Helper not found at ${SCRIPT_HELPER}`);
    return null;
  }
  const env = { ...process.env, MAIN_REF: mainRef };
  const py = run('python3', [SCRIPT_HELPER], { env, cwd: repoRoot });

  if (py.status !== 0) {
    const msg = (py.stderr || py.stdout || 'CodeRabbit helper failed.').trim();
    console.error(`⚠️  ${msg}`);
    return null;
  }

  const lines = py.stdout.trim().split('\n').filter(Boolean);
  if (lines.length < 2) return null;

  const mainPath  = lines[0];
  const localPath = lines[1];

  // The helper now writes plain text (.txt). Try JSON first; fallback to text display.
  const mainTxt  = readTextSafe(mainPath);
  const localTxt = readTextSafe(localPath);

  let mainReview = null, localReview = null;
  try { mainReview = JSON.parse(mainTxt || ''); } catch {}
  try { localReview = JSON.parse(localTxt || ''); } catch {}

  return { mainReview, localReview, mainTxt, localTxt };
}

function summarizeCodeRabbit(label, data, rawText) {
  console.log(`\n🧠 CodeRabbit (${label})`);

  const arr = Array.isArray(data) ? data
            : Array.isArray(data?.issues) ? data.issues
            : Array.isArray(data?.comments) ? data.comments
            : [];

  if (arr.length > 0) {
    arr.slice(0, 10).forEach((f, i) => {
      const file = f.file || f.path || f.filename || 'unknown';
      const line = f.line || f.start_line || f.position || '?';
      const msg  = f.message || f.body || f.summary || (typeof f === 'string' ? f : JSON.stringify(f).slice(0, 140));
      console.log(`  ${i + 1}. ${file}:${line} — ${msg}`);
    });
    if (arr.length > 10) console.log(`  …and ${arr.length - 10} more`);
    return;
  }

  // Fallback: print plain text lines from the CLI output
  if (rawText && rawText.trim()) {
    rawText.trim().split('\n').slice(0, 30).forEach(ln => console.log('  ' + ln));
  } else {
    console.log('  (no findings or parse error)');
  }
}

/* --------------------------------- CLI -------------------------------- */

program
  .name('merj')
  .description('A CLI that automatically resolves merge conflicts upon git pulls')
  .version(PKG.version || '1.0.0');

program
  .command('auth')
  .description('Set up GitHub authentication with Personal Access Token')
  .action(async () => {
    const repoRoot = assertInGitRepo();
    const envPath = ensureDotenvAt(repoRoot);

    const { token } = await inquirer.prompt([
      {
        type: 'password',
        name: 'token',
        message: 'Enter your GitHub Personal Access Token (classic or fine-grained):',
        mask: '*',
        validate: (s) => (s && s.length > 10) || 'Token looks too short',
      },
    ]);

    let envBody = fs.readFileSync(envPath, 'utf-8');
    const line = `GITHUB_TOKEN=${token}`;
    if (/^GITHUB_TOKEN=/m.test(envBody)) {
      envBody = envBody.replace(/^GITHUB_TOKEN=.*$/m, line);
    } else {
      envBody = envBody.length ? `${envBody.trim()}\n${line}\n` : `${line}\n`;
    }
    fs.writeFileSync(envPath, envBody, 'utf-8');
    console.log(`✅ Saved token to ${path.relative(repoRoot, envPath)}.`);

    const octokit = getAuthenticatedClient();
    if (!octokit) {
      console.log('⚠️  Could not initialize Octokit. Ensure your shell loads .env (restart terminal if needed).');
      return;
    }
    const authResult = await checkAuth(octokit);
    if (authResult.authenticated) {
      console.log(`🔐 Authenticated as ${authResult.username}`);
    } else {
      console.log(`⚠️  Auth check failed: ${authResult.error}`);
    }
  });

program
  .command('pull')
  .description('Pull changes from remote and automatically resolve merge conflicts')
  .option('--main <ref>', 'Remote ref to compare against for CodeRabbit side-reviews', 'origin/main')
  .option('--rebase', 'Use git pull --rebase', false)
  .option('-r, --remote <name>', 'Remote to pull from (if no upstream)', 'origin')
  .option('-b, --branch <name>', 'Branch to pull (if no upstream)', 'main')
  .action(async (opts) => {
    const repoRoot = assertInGitRepo();

    // Build pull args. Prefer upstream if set; else use provided remote/branch.
    const upstream = getUpstream();
    let pullArgs = ['pull'];
    if (opts.rebase) pullArgs.push('--rebase');

    if (!upstream) {
      pullArgs = ['pull', opts.remote, opts.branch, ...(opts.rebase ? ['--rebase'] : [])];
      console.log(`ℹ️  No upstream set for this branch. Using explicit source: ${opts.remote}/${opts.branch}`);
    }

    console.log(`➡️  git ${pullArgs.join(' ')}`);
    const r = runInherit('git', pullArgs, { cwd: repoRoot });

    if (r.status === 0) {
      console.log('✅ Pull completed with no conflicts.');
      process.exit(0);
    }

    if (!hasConflicts(repoRoot)) {
      console.error('❌ Pull failed and no merge conflicts were detected. Check git output above.');
      process.exit(1);
    }

    console.log('⚠️  Merge conflicts detected.');
    console.log('🔎 Running CodeRabbit side-reviews for BASE→main and BASE→local…');

    const cr = runCodeRabbitSideReviews(opts.main, repoRoot);
    if (cr) {
      summarizeCodeRabbit('main since BASE',  cr.mainReview,  cr.mainTxt);
      summarizeCodeRabbit('local since BASE', cr.localReview, cr.localTxt);
    } else {
      console.log('⚠️  Skipping CodeRabbit summary (helper not available or produced no output).');
    }

    console.log('\n👉 Next steps:\n' +
      '   • Use your merge assistant / editor to resolve remaining conflicts.\n' +
      '   • When done:  git add <files> && git merge --continue\n' +
      '   • If you pulled with --rebase, run: git rebase --continue\n');

    // Non-zero so shells/CI know the merge isn’t finished yet.
    process.exit(2);
  });

program
  .command('push')
  .description('Push changes to remote repository')
  .option('-r, --remote <name>', 'Remote name', 'origin')
  .option('-b, --branch <name>', 'Branch name', getCurrentBranch())
  .option('-f, --force', 'Force with lease', false)
  .action(async (options) => {
    try {
      assertInGitRepo();

      const octokit = getAuthenticatedClient();
      if (!octokit) {
        console.log('ℹ️  No GitHub token found in env (.env). You can still push via git.');
      } else {
        const authResult = await checkAuth(octokit);
        if (!authResult.authenticated) {
          console.log('⚠️  Auth failed. Run: merj auth');
        } else {
          console.log(`🔐 Authenticated as ${authResult.username}`);
        }
      }

      const info = getRepoInfo();
      console.log(`Repository: ${info.owner}/${info.repo}`);
      console.log(`Current branch: ${info.currentBranch}`);

      const pushResult = await pushToRemote(options.remote, options.branch, { force: options.force });
      if (pushResult.success) {
        console.log(`✅ ${pushResult.message}`);
      } else {
        console.error(`❌ Push failed: ${pushResult.message}`);
        process.exit(1);
      }
    } catch (err) {
      console.error('Error:', err.message || err);
      process.exit(1);
    }
  });

program.parse();
