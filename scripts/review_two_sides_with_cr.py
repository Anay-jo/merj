#!/usr/bin/env python3
import os, subprocess, sys, pathlib, tempfile

MAIN_REF = os.environ.get("MAIN_REF", "origin/main")

def sh(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"cmd failed: {' '.join(cmd)}\n{p.stderr or p.stdout}")
    return p.stdout.strip()

def git(*args, cwd=None):
    return sh(["git", *args], cwd=cwd)

def repo_root():
    return git("rev-parse", "--show-toplevel")

def detect_rebase_context(repo):
    """Return (base_sha, local_tip_sha, main_tip_ref)."""
    git_dir = git("rev-parse", "--git-dir", cwd=repo)
    gd = (pathlib.Path(repo) / git_dir)
    local_tip = None
    for d in ("rebase-merge", "rebase-apply"):
        p = gd / d / "orig-head"
        if p.exists():
            local_tip = p.read_text().strip()
            break
    if not local_tip:
        local_tip = git("rev-parse", "HEAD", cwd=repo)
    main_tip = MAIN_REF
    base = git("merge-base", local_tip, main_tip, cwd=repo)
    return base, local_tip, main_tip

def add_worktree(ref):
    """Create a detached worktree at the given ref; return path."""
    d = tempfile.mkdtemp(prefix="cr-")
    sh(["git", "worktree", "add", "--detach", d, ref])
    return d

def run_cr_committed(repo_dir, base_commit):
    """Ask CodeRabbit to diff committed changes since base_commit."""
    # Use plain output (easy to capture), no color.
    return sh([
        "coderabbit", "review",
        "--plain",
        "--type", "committed",
        "--base-commit", base_commit,
    ], cwd=repo_dir)

def main():
    repo = repo_root()
    # keep remotes fresh
    git("fetch", "--all", "--prune", cwd=repo)

    base, local_tip, main_tip = detect_rebase_context(repo)

    # Create read-only views at each tip; no patching needed
    wt_local = add_worktree(local_tip)
    wt_main  = add_worktree(main_tip)

    out_main  = "/tmp/coderabbit_main.txt"
    out_local = "/tmp/coderabbit_local.txt"

    try:
        # Run CodeRabbit on each side vs the shared base
        main_txt  = run_cr_committed(wt_main,  base)
        local_txt = run_cr_committed(wt_local, base)

        with open(out_main, "w",  encoding="utf-8") as f: f.write(main_txt or "No changes since base.")
        with open(out_local, "w", encoding="utf-8") as f: f.write(local_txt or "No changes since base.")

        # Paths for the Node caller
        print(out_main)
        print(out_local)

    finally:
        # Clean worktrees
        try: sh(["git", "worktree", "remove", "--force", wt_main])
        except: pass
        try: sh(["git", "worktree", "remove", "--force", wt_local])
        except: pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[merj] CodeRabbit side-review failed: {e}", file=sys.stderr)
        sys.exit(1)