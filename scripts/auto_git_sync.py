# -*- coding: utf-8 -*-
import subprocess
import time
import os
import sys

def run_git_sync():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("🚀 [Auto Git Sync] Starting robust git sync workflow...")
    
    try:
        # 1. git add .
        subprocess.run(["git", "add", "."], cwd=base_dir, check=True)
        
        # 2. git commit (allow no changes)
        commit_res = subprocess.run(["git", "commit", "-m", "update: autopilot live odds & predictions auto sync"], cwd=base_dir, capture_output=True, text=True)
        if "nothing to commit" in commit_res.stdout or "nothing to commit" in commit_res.stderr:
            print("✨ [Auto Git Sync] No file changes to commit.")
        else:
            print("✅ [Auto Git Sync] Committed local changes successfully.")

        # 3. Retry push with pull --no-rebase -X ours for up to 3 attempts
        for attempt in range(1, 4):
            print(f"🔄 [Auto Git Sync] Attempt {attempt}/3 pulling & pushing to GitHub origin main...")
            pull_res = subprocess.run(["git", "pull", "origin", "main", "--no-rebase", "-X", "ours"], cwd=base_dir, capture_output=True, text=True)
            
            push_res = subprocess.run(["git", "push", "origin", "main"], cwd=base_dir, capture_output=True, text=True)
            if push_res.returncode == 0:
                print("🎉 [Auto Git Sync] 100% SUCCESS! Successfully pushed changes to GitHub Pages.")
                return True
            else:
                print(f"⚠️ [Auto Git Sync] Push attempt {attempt} failed: {push_res.stderr.strip()}")
                time.sleep(3)

    except Exception as e:
        print(f"❌ [Auto Git Sync] Exception during git sync: {e}")
        
    return False

if __name__ == "__main__":
    success = run_git_sync()
    sys.exit(0 if success else 1)
