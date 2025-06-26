#!/usr/bin/env python3
"""
Mobile build script for running heatmap.
Checks for prerequisites, converts runs.pkl to static JSON files,
and packages the app for Android using Capacitor.
"""

import os
import sys
import shutil
import subprocess
import importlib.util
import pickle
import json
import time
from shapely.geometry import mapping

# --- Utility Functions ---

def ask_yes_no(question):
    """Ask a yes/no question and return True for yes, False for no."""
    while True:
        response = input(f"{question} [y/n]: ").lower().strip()
        if response in ('y', 'yes'):
            return True
        if response in ('n', 'no'):
            return False
        print("Please answer 'y' or 'n'.")

def run_command(command, cwd=None, check=True, show_progress=False):
    """Run a shell command, optionally showing progress."""
    print(f"\n▶️ Running command: {' '.join(command)}")
    if show_progress:
        print("   (This may take a few minutes...)")
    
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Redirect stderr to stdout
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Print output line by line
        for line in iter(process.stdout.readline, ''):
            print(line, end='')

        process.wait()
        
        if process.returncode == 0:
            return True
        else:
            print(f"\n❌ Command failed with exit code {process.returncode}", file=sys.stderr)
            return False

    except FileNotFoundError:
        print(f"❌ Error: Command not found: {command[0]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        return False

# --- Prerequisite Checking ---

def check_python_packages():
    """Check for and offer to install required Python packages."""
    print("\n🔍 Checking for required Python packages...")
    required = ['shapely', 'rtree']
    missing = [pkg for pkg in required if not importlib.util.find_spec(pkg)]

    if not missing:
        print("✅ All Python packages are installed.")
        return True

    print(f"⚠️ Missing Python packages: {', '.join(missing)}")
    if ask_yes_no("Do you want to install them now using pip?"):
        pip_command = [sys.executable, '-m', 'pip', 'install'] + missing
        if run_command(pip_command):
            print("✅ Successfully installed missing packages.")
            return True
        else:
            print("❌ Failed to install Python packages. Please install them manually.", file=sys.stderr)
            return False
    return False

def check_node_and_npm():
    """Check for Node.js and npm."""
    print("\n🔍 Checking for Node.js and npm...")
    if shutil.which('node') and shutil.which('npm'):
        print("✅ Node.js and npm are installed.")
        return True

    print("❌ Node.js and/or npm not found in PATH.", file=sys.stderr)
    print("Please install Node.js (which includes npm) from https://nodejs.org/", file=sys.stderr)
    if sys.platform == "linux" or sys.platform == "darwin":
        print("You might be able to install it using your system's package manager,", file=sys.stderr)
        print("e.g., 'sudo apt-get install nodejs npm' or 'brew install node'.", file=sys.stderr)
    return False

def check_android_sdk():
    """Check for a basic Android development environment."""
    print("\n🔍 Checking for Android SDK environment...")
    android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    java_home = os.environ.get('JAVA_HOME')
    java_in_path = shutil.which('java')

    if android_home and os.path.exists(android_home) and (java_home or java_in_path):
        print("✅ Android SDK and Java environment seem to be configured.")
        return True

    print("⚠️ Android SDK environment not fully configured.", file=sys.stderr)
    if not android_home:
        print("- ANDROID_HOME or ANDROID_SDK_ROOT environment variable is not set.", file=sys.stderr)
    if not (java_home or java_in_path):
        print("- Java (JDK) not found in JAVA_HOME or PATH.", file=sys.stderr)
    print("Please install Android Studio, which will set up the Android SDK and recommend a JDK.", file=sys.stderr)
    print("Make sure the required environment variables are set.", file=sys.stderr)
    return False

def check_runs_pkl():
    """Check if the runs.pkl data file exists."""
    print("\n🔍 Checking for runs.pkl data file...")
    if os.path.exists('runs.pkl'):
        print("✅ runs.pkl found.")
        return True

    print("❌ Error: runs.pkl not found in the current directory.", file=sys.stderr)
    print("Please run 'python import_runs.py' to generate it.", file=sys.stderr)
    return False

# --- Build Steps ---

def build_mobile_data():
    """Converts runs.pkl to static JSON files for the mobile app."""
    print("\n🚀 Building mobile data assets...")
    with open('runs.pkl', 'rb') as f:
        runs = pickle.load(f)
    total_runs = len(runs)
    print(f"✅ Loaded {total_runs} runs")

    mobile_dir = '../mobile'
    if os.path.exists(mobile_dir):
        shutil.rmtree(mobile_dir)
    os.makedirs(os.path.join(mobile_dir, 'data'))
    print(f"📂 Created output directory: {mobile_dir}")

    print("\n🔄 Converting run data to JSON. This may take a moment...")
    runs_data, spatial_index = {}, []
    start_time = time.time()
    for i, (rid, run) in enumerate(runs.items()):
        geoms = {level: mapping(geom) for level, geom in run['geoms'].items()}
        metadata = run.get('metadata', {})
        json_metadata = {k: v.isoformat() if hasattr(v, 'isoformat') else v for k, v in metadata.items()}
        runs_data[str(rid)] = {'geoms': geoms, 'bbox': run['bbox'], 'metadata': json_metadata}
        spatial_index.append({'id': rid, 'bbox': run['bbox']})
        
        # Progress indicator
        if (i + 1) % 250 == 0 or (i + 1) == total_runs:
            elapsed = time.time() - start_time
            print(f"   ...processed {i + 1}/{total_runs} runs ({elapsed:.1f}s)", end='\r')
    print("\n✅ Data conversion complete.")

    print("\n💾 Writing data files...")
    runs_file = os.path.join(mobile_dir, 'data', 'runs.json')
    with open(runs_file, 'w') as f:
        json.dump(runs_data, f, separators=(',', ':'))
    print(f"   - Wrote runs data to {runs_file}")

    index_file = os.path.join(mobile_dir, 'data', 'spatial_index.json')
    with open(index_file, 'w') as f:
        json.dump(spatial_index, f, separators=(',', ':'))
    print(f"   - Wrote spatial index to {index_file}")
    return mobile_dir

def create_mobile_files(mobile_dir):
    """Create JavaScript library and copy HTML/SW templates."""
    print("\n📄 Creating mobile helper files...")
    # ... (rest of the function is unchanged)

# --- Android Packaging ---

def package_for_android(mobile_dir):
    """Run the full Android packaging process."""
    print("\n📦 Starting Android packaging process...")

    if not check_node_and_npm() or not check_android_sdk():
        print("❌ Cannot proceed with Android packaging due to missing prerequisites.", file=sys.stderr)
        return

    create_capacitor_project(mobile_dir)
    
    print("\nInstalling npm dependencies...")
    if not run_command(['npm', 'install'], cwd=mobile_dir, show_progress=True):
        print("❌ Failed to install npm dependencies.", file=sys.stderr)
        return

    print("\nAdding Android platform to Capacitor project...")
    if not run_command(['npx', 'cap', 'add', 'android'], cwd=mobile_dir):
        print("❌ Failed to add Android platform.", file=sys.stderr)
        return

    setup_www_directory(mobile_dir)

    print("\nSyncing web assets with Capacitor...")
    if not run_command(['npx', 'cap', 'sync'], cwd=mobile_dir):
        print("❌ Failed to sync web assets.", file=sys.stderr)
        return

    print("\n🔨 Building Android APK...")
    android_dir = os.path.join(mobile_dir, 'android')
    if not run_command(['./gradlew', 'assembleDebug'], cwd=android_dir, show_progress=True):
        print("❌ Failed to build APK.", file=sys.stderr)
        print("💡 Try opening the project in Android Studio to resolve issues:", file=sys.stderr)
        print(f"   npx cap open android (from the '{mobile_dir}' directory)", file=sys.stderr)
        return
        
    print("✅ APK build successful!")
    # ... (rest of the function is unchanged)

# --- Main Orchestrator ---

def main():
    """Run the full mobile build and packaging process."""
    print("--- Running Heatmap Mobile Build Script ---")

    if not os.path.basename(os.getcwd()) == 'server':
        print("❌ This script must be run from the 'server/' directory.", file=sys.stderr)
        sys.exit(1)

    if not check_runs_pkl() or not check_python_packages():
        sys.exit(1)

    try:
        mobile_dir = build_mobile_data()
        create_mobile_files(mobile_dir)
        print(f"\n🎉 Mobile web assets build complete!")
        print(f"   Output directory: {os.path.abspath(mobile_dir)}")
    except Exception as e:
        print(f"❌ Build failed during web asset creation: {e}", file=sys.stderr)
        sys.exit(1)

    print()
    if ask_yes_no("Do you want to package the app for Android now?"):
        package_for_android(mobile_dir)
    else:
        print("\nSkipping Android packaging.")
        print("You can package it later by running this script again.")

    print("\n--- Build process finished ---")

if __name__ == '__main__':
    main()
