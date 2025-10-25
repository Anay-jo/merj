#!/usr/bin/env bash
set -euo pipefail

# ── paths
ROOT="$(pwd)"
TMP_BASE="$(mktemp -d /tmp/merj-demo.XXXXXX)"
REMOTE="$TMP_BASE/remote.git"
WORK_MAIN="$TMP_BASE/work-main"
WORK_FEAT="$TMP_BASE/work-feature"

echo "📦 Creating bare remote at $REMOTE"
git init --bare "$REMOTE" >/dev/null

echo "Seeding repo (initial commit on main)"
SEED="$TMP_BASE/seed"
git clone "$REMOTE" "$SEED" >/dev/null
pushd "$SEED" >/dev/null
  git checkout -b main >/dev/null
  echo 'line1: base' > app.txt
  echo 'line2: stable' >> app.txt
  git add app.txt
  git commit -m "initial" >/dev/null
  git push -u origin main >/dev/null
popd >/dev/null

echo "🧭 Clone for main workflow → $WORK_MAIN"
git clone "$REMOTE" "$WORK_MAIN" >/dev/null

echo "Clone for feature workflow → $WORK_FEAT"
git clone "$REMOTE" "$WORK_FEAT" >/dev/null

echo " Make change on main (conflicting line)"
pushd "$WORK_MAIN" >/dev/null
  git checkout main >/dev/null
  sed -i '' 's/line1: base/line1: MAIN adds retry/' app.txt 2>/dev/null || true
  if ! grep -q 'MAIN adds retry' app.txt; then
    # Linux sed
    sed -i 's/line1: base/line1: MAIN adds retry/' app.txt
  fi
  git add app.txt
  git commit -m "main: change line1" >/dev/null
  git push >/dev/null
popd >/dev/null

echo "Create feature branch from old base and change same line differently"
pushd "$WORK_FEAT" >/dev/null
  git checkout -b feature >/dev/null
  sed -i '' 's/line1: base/line1: FEATURE adds async+logger/' app.txt 2>/dev/null || true
  if ! grep -q 'FEATURE adds async+logger' app.txt; then
    sed -i 's/line1: base/line1: FEATURE adds async+logger/' app.txt
  fi
  git add app.txt
  git commit -m "feature: change line1 differently" >/dev/null

  echo
  echo "Running: merj pull --main=origin/main  (should cause a conflict)"
  echo
  # Use your globally linked CLI
  merj pull --main=origin/main || true

  echo
  echo "Check for CodeRabbit outputs (if CLI installed):"
  ls -l /tmp/coderabbit_main.json /tmp/coderabbit_local.json 2>/dev/null || echo "(No CodeRabbit JSONs; either no CLI or no findings.)"
  echo

  echo "🔧 Resolve the conflict however your flow proceeds next (LLM/keep-local/keep-incoming), then:"
  echo "   git add app.txt && git merge --continue"
popd >/dev/null

echo
echo "Demo setup complete."
echo "   Feature repo: $WORK_FEAT"
echo "   Main repo:    $WORK_MAIN"
echo "   Remote:       $REMOTE"

