#!/usr/bin/env bash
set -euo pipefail

echo "🧹 Cleaning old /tmp/merj-demo.* directories..."
rm -rf /tmp/merj-demo.*

echo "🚀 Running initial demo_conflict.sh..."
scripts/demo_conflict.sh

# 2️⃣ MAIN-side risky changes
MAIN="$(ls -d /tmp/merj-demo.*/work-main | head -1)"
echo "🧭 MAIN repo detected at: $MAIN"
cd "$MAIN"

cat >> app.txt <<'EOF'
function risky() {
  console.log("debug");
  const secret = "hardcoded-api-key-123";
  eval("console.log('danger')");
}
EOF

echo "📝 Committing MAIN-side risky code..."
git add app.txt
git commit -m "main: risky eval + debug + hardcoded secret"
git push origin main

# 3️⃣ FEATURE-side conflicting/smelly changes
FEAT="$(ls -d /tmp/merj-demo.*/work-feature | head -1)"
echo " FEATURE repo detected at: $FEAT"
cd "$FEAT"

echo "🧼 Resetting FEATURE branch (abort merges/rebases, clean untracked)..."
git rebase --abort 2>/dev/null || true
git merge  --abort 2>/dev/null || true
git reset --hard
git clean -fd

git checkout -B feature
sed -i '' 's/line1: base/line1: FEATURE async+logger/' app.txt 2>/dev/null || sed -i 's/line1: base/line1: FEATURE async+logger/' app.txt

cat >> app.txt <<'EOF'

// feature adds minor smells
function featureStuff() {
  var unused = 123;
  try { JSON.parse("{bad json"); } catch (e) {}
}
EOF

echo " Committing FEATURE-side conflicting code..."
git add app.txt
git commit -m "feature: unused var + empty catch + conflict"
git branch --set-upstream-to=origin/main feature

# 4️⃣ Run merj to simulate pull + conflict resolution
echo "⚔️  Triggering merj pull to produce conflict & run CodeRabbit..."
merj pull --main origin/main || true

echo "Full demo complete!"
echo
echo "Main repo:    $MAIN"
echo "Feature repo: $FEAT"
echo "Remote repo:  $(ls -d /tmp/merj-demo.*/remote.git | head -1)"