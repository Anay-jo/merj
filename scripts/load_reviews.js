#!/usr/bin/env node
// ESM-compatible (package.json has "type": "module")
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

// ---------- config & helpers ----------
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const argv = process.argv.slice(2);

// Defaults (can be overridden by flags)
let MAIN_IN = process.env.CR_MAIN_IN || '/tmp/coderabbit_main.json';
let LOCAL_IN = process.env.CR_LOCAL_IN || '/tmp/coderabbit_local.json';
let OUT_DIR  = process.env.CR_OUT_DIR  || path.resolve(__dirname, '..', 'context');

// Allow text fallbacks if JSON isn’t present
const ALT_MAIN = ['/tmp/coderabbit_main.txt'];
const ALT_LOCAL = ['/tmp/coderabbit_local.txt'];

// Flags:
//   --main <path>      override main input path
//   --local <path>     override local input path
//   --outDir <path>    override output directory
//   --suffix <text>    append suffix to output filenames (e.g., run id)
let SUFFIX = '';

for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--main' && argv[i+1]) MAIN_IN = argv[++i];
  else if (a === '--local' && argv[i+1]) LOCAL_IN = argv[++i];
  else if (a === '--outDir' && argv[i+1]) OUT_DIR = argv[++i];
  else if (a === '--suffix' && argv[i+1]) SUFFIX = argv[++i];
}

// Output filenames
const mainOut  = path.join(OUT_DIR, `main_review${SUFFIX ? '_' + SUFFIX : ''}.txt`);
const localOut = path.join(OUT_DIR, `local_review${SUFFIX ? '_' + SUFFIX : ''}.txt`);
const comboOut = path.join(OUT_DIR, `combined${SUFFIX ? '_' + SUFFIX : ''}.txt`);

async function ensureDir(p) {
  await fs.mkdir(p, { recursive: true });
}

async function exists(p) {
  try {
    await fs.stat(p);
    return true;
  } catch {
    return false;
  }
}

function toNiceTextFromJSON(obj) {
  // Try to extract a human-friendly summary from common shapes.
  try {
    // 1) If it looks like CodeRabbit’s structured list of comments/issues
    if (Array.isArray(obj?.comments)) {
      return obj.comments.map((c, idx) => {
        const file = c.file || c.path || 'unknown';
        const line = c.line != null ? `:${c.line}` : '';
        const type = c.type ? ` [${c.type}]` : '';
        const body = c.body || c.comment || JSON.stringify(c, null, 2);
        return `#${idx+1}${type} ${file}${line}\n${body}\n`;
      }).join('\n');
    }

    // 2) If it has an issues/findings array
    const list = obj.issues || obj.findings || obj.results;
    if (Array.isArray(list)) {
      return list.map((it, idx) => {
        const file = it.file || it.path || 'unknown';
        const line = it.line != null ? `:${it.line}` : '';
        const type = it.type ? ` [${it.type}]` : '';
        const msg  = it.message || it.comment || it.text || JSON.stringify(it, null, 2);
        return `#${idx+1}${type} ${file}${line}\n${msg}\n`;
      }).join('\n');
    }

    // 3) Fallback: stringify
    return JSON.stringify(obj, null, 2);
  } catch (e) {
    return JSON.stringify(obj, null, 2);
  }
}

async function readReviewFlexible(primary, alts = []) {
  const tried = [primary, ...alts];

  for (const candidate of tried) {
    if (!(await exists(candidate))) continue;

    const raw = await fs.readFile(candidate, 'utf8').catch(() => null);
    if (!raw) continue;

    const trimmed = raw.trim();

    // If JSON, try to pretty-extract
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      try {
        const obj = JSON.parse(trimmed);
        const text = toNiceTextFromJSON(obj);
        return { source: candidate, text, raw, isJSON: true };
      } catch {
        // Not valid JSON; treat as plain text
      }
    }

    // Plain text path
    return { source: candidate, text: trimmed, raw, isJSON: false };
  }

  // Nothing found
  return { source: null, text: '', raw: '', isJSON: false };
}

async function main() {
  await ensureDir(OUT_DIR);

  const [mainRes, localRes] = await Promise.all([
    readReviewFlexible(MAIN_IN, ALT_MAIN),
    readReviewFlexible(LOCAL_IN, ALT_LOCAL),
  ]);

  // Write individual files (even if empty; helps pipelines)
  await fs.writeFile(
    mainOut,
    mainRes.text ? mainRes.text + '\n' : '(no main review content)\n',
    'utf8'
  );
  await fs.writeFile(
    localOut,
    localRes.text ? localRes.text + '\n' : '(no local review content)\n',
    'utf8'
  );

  // Build combined
  const combined = [
    '=== CodeRabbit Review (MAIN since BASE) ===',
    mainRes.source ? `(source: ${mainRes.source})` : '(no source found)',
    '',
    mainRes.text || '(no main review content)',
    '',
    '=== CodeRabbit Review (LOCAL since BASE) ===',
    localRes.source ? `(source: ${localRes.source})` : '(no source found)',
    '',
    localRes.text || '(no local review content)',
    '',
  ].join('\n');

  await fs.writeFile(comboOut, combined, 'utf8');

  // Nice console summary
  console.log('🗂  Wrote review artifacts:');
  console.log(`   • ${mainOut}`);
  console.log(`   • ${localOut}`);
  console.log(`   • ${comboOut}`);

  // Optionally echo a friendly hint for LLM ingestion
  console.log('\n👉 Next: feed context/combined.txt (or the two individuals) to your LLM helper.');
}

main().catch((err) => {
  console.error('load_reviews.js failed:', err?.message || err);
  process.exit(1);
});