#!/usr/bin/env node
// Enhanced tool: describe the merge conflict AND produce a merged file suggestion
// Usage:
//   node bin/resolve_with_claude.js               # auto-pick first conflicted file
//   node bin/resolve_with_claude.js --file path   # specify a file
// Env:
//   ANTHROPIC_API_KEY (or ANTHROPIC)
//   MODEL (optional, defaults to 'claude-3-5-sonnet-20241022' or 'claude-sonnet-4-5')

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const API_KEY = process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC;
const MODEL = process.env.MODEL || 'claude-3-5-sonnet-20241022';

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

function read(p) {
  try { return fs.readFileSync(p, 'utf-8'); } catch { return null; }
}

function buildDescriptionPrompt({ filePath, conflictedCode }) {
  const system = [
    'You are a senior software engineer and merge specialist.',
    'Task: Describe the merge conflict found in the provided file. Do not attempt to rewrite or resolve it; only analyze and explain.',
    'Explain clearly for a developer who will resolve it manually.',
  ].join(' ');

  const user = [
    '# File path',
    filePath,
    '',
    '# Instructions',
    '- Summarize where the conflict blocks occur.',
    '- For each conflict block, explain differences between OURS/HEAD (upper) and THEIRS/INCOMING (lower).',
    '- Note overlapping edits, removed/added functions, and any risky changes (e.g., API shape, return types, side effects).',
    '- Suggest a safe merge strategy at a high level (keep ours, keep theirs, or combine – and why).',
    '',
    '# Conflicted file with markers',
    '```',
    conflictedCode,
    '```'
  ].join('\n');

  return { system, messages: [{ role: 'user', content: user }] };
}

function buildResolutionPrompt({ filePath, conflictedCode }) {
  const system = [
    'You are an expert merge tool, who can only output code. Do not indicate lines by saying line1:, line2:, etc.',
    'Task: Resolve the merge conflict intelligently and return the final merged file, as just code, with no line indicators, or plain english anywhere.',
    'STRICT OUTPUT: Output ONLY the resolved code with all conflict markers removed. Do not include explanations, comments, markdown fences, or any english anywhere',
    'Preserve formatting and non-conflicted lines exactly as in the original file.',
    'Merge both sides when possible; if mutually exclusive, prefer safe combination rather than deletion.',
  ].join(' ');

  const user = [
    '# File path',
    filePath,
    '',
    '# Conflicted file',
    '```',
    conflictedCode,
    '```'
  ].join('\n');

  return { system, messages: [{ role: 'user', content: user }] };
}

async function callClaude({ model, system, messages }) {
  if (!API_KEY) {
    console.error('❌ Missing ANTHROPIC_API_KEY (or ANTHROPIC) in environment.');
    process.exit(1);
  }
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({ model, max_tokens: 2000, temperature: 0.2, system, messages })
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    console.error(`❌ Claude API error ${res.status}: ${text}`);
    process.exit(1);
  }
  const data = await res.json();
  const contentBlocks = data.content || [];
  const firstText = contentBlocks.map(b => b.text).filter(Boolean).join('\n');
  return firstText || '';
}

(async function main() {
  const repoRoot = assertInGitRepo();
  const argv = process.argv.slice(2);
  let fileFlag = null;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if ((a === '--file' || a === '-f') && argv[i+1]) { fileFlag = argv[++i]; }
    else if (a === '--help' || a === '-h') {
      console.log('Usage: resolve_with_claude [--file <path>]');
      process.exit(0);
    }
  }

  let targetFile = fileFlag;
  const conflicted = listConflictedFiles(repoRoot);
  if (!targetFile) {
    if (conflicted.length === 0) {
      console.error('❌ No conflicted files detected. Pass --file <path> to analyze a specific file.');
      process.exit(1);
    }
    targetFile = conflicted[0];
  }

  const absFile = path.join(repoRoot, targetFile);
  if (!fs.existsSync(absFile)) {
    console.error(`❌ File not found: ${targetFile}`);
    process.exit(1);
  }

  const conflictedCode = read(absFile);
  if (!conflictedCode || !conflictedCode.includes('<<<<<<<')) {
    console.error('❌ The selected file does not contain Git conflict markers.');
    process.exit(1);
  }

  // Step 1: Describe the conflict
  const describePrompt = buildDescriptionPrompt({ filePath: targetFile, conflictedCode });
  const description = await callClaude({ model: MODEL, system: describePrompt.system, messages: describePrompt.messages });

  console.log('\n🧠 Claude’s Analysis:\n');
  console.log(description.trim());

  // Step 2: Ask Claude to produce the merged file
  const resolvePrompt = buildResolutionPrompt({ filePath: targetFile, conflictedCode });
  const resolved = await callClaude({ model: MODEL, system: resolvePrompt.system, messages: resolvePrompt.messages });

  // Save merged file output as a separate copy; do NOT modify original
const OUTPUT_ROOT = process.env.MERGE_OUTPUT_ROOT || '/tmp/merged_suggestions';
const outPath = path.join(OUTPUT_ROOT, path.relative(repoRoot, absFile));
fs.mkdirSync(path.dirname(outPath), { recursive: true });
const resolvedCode = String(resolved).trim() + '\n';
fs.writeFileSync(outPath, resolvedCode, 'utf-8');
console.log(`\n✅ Wrote merged suggestion to: ${outPath}\n`);
// Print the merged file contents to STDOUT
process.stdout.write(resolvedCode);
})();
