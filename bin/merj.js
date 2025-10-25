#!/usr/bin/env node
/* eslint-disable no-console */
const { spawnSync } = require('child_process');
const fs = require('fs');

function run(cmd, args, opts = {}) {
  const res = spawnSync(cmd, args, { stdio: 'pipe', encoding: 'utf-8', ...opts });
  return res;
}

function hasConflicts() {
  const r = run('git', ['ls-files', '-u']);
  return r.status === 0 && r.stdout.trim().length > 0;
}

function pull(argv) {
  const args = ['pull', ...argv.slice(3)]; // pass-through flags
  console.log('➡️  git', args.join(' '));
  const r = run('git', args, { stdio: 'inherit' });

  if (r.status === 0) {
    console.log('✅ Pull completed with no conflicts.');
    process.exit(0);
  }

  // non-zero: could be conflicts or other error; check explicitly
  if (!hasConflicts()) {
    console.error('❌ Pull failed (no merge conflicts detected). Check the git error above.');
    process.exit(1);
  }

  console.log('⚠️  Merge conflicts detected — running CodeRabbit side reviews…');

  // allow MAIN_REF override via env or a flag like --main=origin/dev
  const mainFlag = process.argv.find(a => a.startsWith('--main='));
  const env = { ...process.env };
  if (mainFlag) env.MAIN_REF = mainFlag.split('=')[1];

  const py = run('python3', ['scripts/review_two_sides_with_cr.py'], { env });
  if (py.status !== 0) {
    console.error(py.stderr || py.stdout || 'CodeRabbit helper failed.');
    process.exit(1);
  }

  // helper prints the two output paths (each on its own line)
  const lines = py.stdout.trim().split('\n');
  const mainJsonPath = lines[0];
  const localJsonPath = lines[1];

  let mainReview = null;
  let localReview = null;

  try { mainReview = JSON.parse(fs.readFileSync(mainJsonPath, 'utf-8')); } catch {}
  try { localReview = JSON.parse(fs.readFileSync(localJsonPath, 'utf-8')); } catch {}

  // Render a compact summary from CodeRabbit output (be defensive about shape)
  function summarize(label, data) {
    console.log(`\n🧠 CodeRabbit (${label})`);
    if (!data) { console.log('  (no findings or parse error)'); return; }

    // Common shapes: either an array of findings, or an object with "issues"/"comments"
    const findings = Array.isArray(data) ? data
                  : Array.isArray(data?.issues) ? data.issues
                  : Array.isArray(data?.comments) ? data.comments
                  : [];

    if (findings.length === 0) {
      console.log('  (no issues found)');
      return;
    }

    findings.slice(0, 10).forEach((f, i) => {
      const path = f.file || f.path || f.filename || 'unknown';
      const line = f.line || f.start_line || f.position || '?';
      const msg  = f.message || f.body || f.summary || JSON.stringify(f).slice(0, 120);
      console.log(`  ${i+1}. ${path}:${line} — ${msg}`);
    });
    if (findings.length > 10) console.log(`  …and ${findings.length - 10} more`);
  }

  summarize('main since BASE',  mainReview);
  summarize('local since BASE', localReview);

  console.log('\n👉 Next: run your merge assistant to resolve conflicts, using the hints above.\n' +
              '   When done, stage changes and `git merge --continue` (or `git rebase --continue`).');

  // Keep non-zero exit so shell/CI knows merge not finished yet.
  process.exit(2);
}

function usage() {
  console.log(`merj – git pull wrapper with CodeRabbit side review
Usage:
  merj pull [--main=origin/main] [any git pull flags…]

Examples:
  merj pull
  merj pull --rebase
  merj pull --main=origin/dev
`);
}

function main() {
  const argv = process.argv;
  const cmd = argv[2];

  if (cmd === 'pull') return pull(argv);
  return usage();
}

main();

