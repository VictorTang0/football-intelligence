import os
import sys
import subprocess

def run_script(script_name, args=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_dir, "scripts", script_name)
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
        
    print(f"\n======== Running {script_name} ========")
    # Run with UTF-8 encoding environment variable
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    result = subprocess.run(cmd, env=env, capture_output=False)
    if result.returncode != 0:
        print(f"❌ Error: {script_name} failed with return code {result.returncode}")
        return False
    print(f"✅ Success: {script_name} completed.")
    return True

def main():
    print("🚀 Starting 'Analyze Today's Matches' Master Workflow...")
    
    # Step 1: Fetch latest Sporttery matches and odds
    if not run_script("fetch_sporttery_matches.py"):
        sys.exit(1)
        
    # Step 2: Clean up obsolete pending matches in matches.json
    if not run_script("cleanup_matches.py"):
        sys.exit(1)
        
    # Step 3: Initialize new matches with complete schema skeletal structure
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_json_path = os.path.join(base_dir, "data", "new_matches_input.json")
    if not run_script("initialize_match.py", [input_json_path]):
        sys.exit(1)
        
    # Step 4: Run odds and news update (automatically loads fresh odds & computes recommendations/reasonings)
    if not run_script("update_odds_and_news.py"):
        sys.exit(1)
        
    print("\n🎉 Master 'Analyze Today's Matches' Workflow Completed Successfully!")

if __name__ == "__main__":
    main()
