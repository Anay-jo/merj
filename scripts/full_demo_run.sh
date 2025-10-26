#!/usr/bin/env bash
set -euo pipefail

echo "🧹 Cleaning old /tmp/merj-demo.* directories..."
rm -rf /tmp/merj-demo.*

echo "🚀 Running initial demo_conflict.sh..."
scripts/demo_conflict.sh

# 2️⃣ MAIN-side: rewrite app.txt with one implementation of the same functions
MAIN="$(ls -d /tmp/merj-demo.*/work-main | head -1)"
echo "🧭 MAIN repo detected at: $MAIN"
cd "$MAIN"

git checkout -B main

cat > app.txt <<'EOF'
export async function handle(input) {
  const max = 2;
  let attempts = 0;
  while (true) {
    try {
      const s = String(input);
      if (s.length < 3) throw new Error("short");
      return { ok: true, len: s.length };
    } catch (e) {
      attempts += 1;
      if (attempts > max) throw e;
      await new Promise(r => setTimeout(r, 50));
    }
  }
}

export function format(x) {
  return String(x).toUpperCase();
}
EOF

echo "📝 Committing MAIN-side code..."
git add app.txt
git commit -m "main: export handle with retry + format upper"
git push -u origin main

# 3️⃣ FEATURE-side: rewrite app.txt with a different implementation of the same functions
FEAT="$(ls -d /tmp/merj-demo.*/work-feature | head -1)"
echo "🧭 FEATURE repo detected at: $FEAT"
cd "$FEAT"

echo "🧼 Resetting FEATURE branch (abort merges/rebases, clean untracked)..."
git rebase --abort 2>/dev/null || true
git merge  --abort 2>/dev/null || true
git reset --hard
git clean -fd

git checkout -B feature

cat > app.txt <<'EOF'
export async function handle(input) {
  const payload = typeof input === "string" ? input : JSON.stringify(input);
  await new Promise(r => setTimeout(r, 25));
  return { ok: true, hash: payload.length };
}

export function format(x) {
  return JSON.stringify({ v: String(x) });
}
EOF

echo "📝 Committing FEATURE-side code..."
git add app.txt
git commit -m "feature: export handle async hash + format json"
git branch --set-upstream-to=origin/main feature

# 4️⃣ Simulate pull to produce conflict and run your resolver pipeline
echo "⚔️  Triggering merj pull to create conflict..."
merj pull --main origin/main || true

echo "✅ Full demo complete!"
echo "Main repo:    $MAIN"
echo "Feature repo: $FEAT"
echo "Remote repo:  $(ls -d /tmp/merj-demo.*/remote.git | head -1)"