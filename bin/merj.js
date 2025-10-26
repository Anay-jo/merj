#!/usr/bin/env node
/* eslint-disable no-console */
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function run(cmd, args, opts = {}) {
  const res = spawnSync(cmd, args, { stdio: 'pipe', encoding: 'utf-8', ...opts });
  return res;
}

function hasConflicts() {
  const r = run('git', ['ls-files', '-u']);
  return r.status === 0 && r.stdout.trim().length > 0;
}

//This function gives us the diff information source: ChatGPT
async function getDiffs() {
  const mergeBase = (await git.raw(['merge-base', 'HEAD', 'origin/main'])).trim();

  //UTF Javascript strings
  const diffLocalVsBase = await git.diff([`${mergeBase}..HEAD`]);
  const diffRemoteVsBase = await git.diff([`${mergeBase}..origin/main`]);
  const diffLocalVsRemote = await git.diff(['HEAD..origin/main']); // may show conflicts


  //Turns each of the Javascript strings into JSON strings
  const parseddiffLocalVsBase = parseDiff(diffLocalVsBase);
  const parseddiffRemoteVsBase = parseDiff(diffRemoteVsBase);
  const parseddiffLocalVsRemote = parseDiff(diffLocalVsRemote);

  return {
    mergeBase,
    parseddiffLocalVsBase,
    parseddiffRemoteVsBase,
    parseddiffLocalVsRemote
  };
}

async function pull(argv) {

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


  const {
  mergeBase,
  parseddiffLocalVsBase,
  parseddiffRemoteVsBase,
  parseddiffLocalVsRemote
} = await getDiffs();

  lvb_diff = []
  //file
  parseddiffLocalVsBase.forEach((diff) => {
      //for each chunk/function
      changes = []
      diff.chunks.forEach((d) => {
          d.changes.forEach((change) => {
              changes.push(change.ln)
          });
      });
      lvb_diff.push({filefrom: diff.from, lns: changes})
  });

  rvb_diff = []

  parseddiffRemoteVsBase.forEach((diff) => {
    //for each chunk/function
    changes = []
    diff.chunks.forEach((d) => {
        d.changes.forEach((change) => {
            changes.push(change.ln)
        });
    });
    rvb_diff.push({filefrom: diff.from, lns: changes})
  });

  const jumbo_json = {
    lbd: lvb_diff,
    rbd: rvb_diff
  }

  console.log('📡 Sending diff data to RAG pipeline...');
  try {
    const response = await fetch('http://127.0.0.1:5000/api/data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(jumbo_json)
    });
    const data = await response.json(); // get JSON data

    if (response.ok && data.status === 'success') {
      console.log('✅ RAG processing completed successfully');
      console.log(`   - Found ${data.similar_code_found || 0} similar code patterns`);
      console.log(`   - Saved context to rag_output/llm_context.txt`);
    } else {
      console.log('⚠️  RAG processing returned with warning:', data.warning || 'Unknown issue');
    }
  } catch (error) {
    console.error("❌ Error connecting to RAG pipeline:", error.message);
    console.log("⚠️  Continuing without RAG context...");
  }


  // allow MAIN_REF override via env or a flag like --main=origin/dev
  const mainFlag = process.argv.find(a => a.startsWith('--main='));
  const env = { ...process.env };
  if (mainFlag) env.MAIN_REF = mainFlag.split('=')[1];

//Line below is where the script with code rabbit logic is called
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

  // Save CodeRabbit findings for Claude to use
  const codeRabbitOutput = {
    mainBranchReview: mainReview,
    localBranchReview: localReview,
    timestamp: new Date().toISOString()
  };

  // Ensure rag_output directory exists
  const ragOutputDir = path.join(process.cwd(), 'rag_output');
  if (!fs.existsSync(ragOutputDir)) {
    fs.mkdirSync(ragOutputDir, { recursive: true });
  }

  // Save CodeRabbit findings to file
  const codeRabbitPath = path.join(ragOutputDir, 'coderabbit_review.json');
  try {
    fs.writeFileSync(codeRabbitPath, JSON.stringify(codeRabbitOutput, null, 2), 'utf-8');
    console.log('📝 Saved CodeRabbit findings to rag_output/coderabbit_review.json');
  } catch (e) {
    console.error('⚠️  Failed to save CodeRabbit findings:', e.message);
  }

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

