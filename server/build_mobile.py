#!/usr/bin/env python3
"""
Mobile build script for running heatmap.
Checks for prerequisites and packages the app for Android using Capacitor.
"""

import os
import sys
import shutil
import subprocess
import configparser

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

def check_node_and_npm():
    """Check for Node.js and npm."""
    print("\n🔍 Checking for Node.js and npm...")
    if shutil.which('node') and shutil.which('npm'):
        print("✅ Node.js and npm are installed.")
        return True

    print("❌ Node.js and/or npm not found in PATH.", file=sys.stderr)
    print("Please install Node.js (which includes npm) from https://nodejs.org/", file=sys.stderr)
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
    return False

# --- Build Steps ---

def setup_mobile_project(mobile_dir):
    """Copy mobile source files and inject credentials."""
    print("\n🚀 Setting up mobile project...")
    
    # Create www directory
    www_dir = os.path.join(mobile_dir, 'www')
    os.makedirs(www_dir, exist_ok=True)

    # Copy HTML
    shutil.copy2(os.path.join('..', 'mobile', 'index.html'), os.path.join(www_dir, 'index.html'))

    # Read, inject credentials, and write JS
    config = configparser.ConfigParser()
    config.read('config.ini')
    client_id = config.get('strava', 'client_id')
    client_secret = config.get('strava', 'client_secret')

    with open(os.path.join('..', 'mobile', 'js', 'main.js'), 'r') as f:
        js_content = f.read()
    
    js_content = js_content.replace('YOUR_MOBILE_CLIENT_ID', client_id)
    js_content = js_content.replace('YOUR_MOBILE_CLIENT_SECRET', client_secret)

    os.makedirs(os.path.join(www_dir, 'js'), exist_ok=True)
    with open(os.path.join(www_dir, 'js', 'main.js'), 'w') as f:
        f.write(js_content)

    print("✅ Mobile project setup complete.")

# --- Main Orchestrator ---

def main():
    """Run the full mobile build and packaging process."""
    print("--- Running Heatmap Mobile Build Script ---")

    if not os.path.basename(os.getcwd()) == 'server':
        print("❌ This script must be run from the 'server/' directory.", file=sys.stderr)
        sys.exit(1)

    if not check_node_and_npm() or not check_android_sdk():
        sys.exit(1)

    mobile_dir = '../mobile'
    setup_mobile_project(mobile_dir)

    print()
    if ask_yes_no("Do you want to package the app for Android now?"):
        print("\n📦 Starting Android packaging process...")
        if not run_command(['npx', 'cap', 'sync'], cwd=mobile_dir):
            print("❌ Failed to sync web assets.", file=sys.stderr)
            sys.exit(1)
        
        if not run_command(['npx', 'cap', 'update'], cwd=mobile_dir):
            print("❌ Failed to update Android project.", file=sys.stderr)
            sys.exit(1)

        print("\n🔨 Building Android APK...")
        if not run_command(['npx', 'cap', 'run', 'android', '--no-open'], cwd=mobile_dir, show_progress=True):
            print("❌ Failed to build APK.", file=sys.stderr)
            sys.exit(1)
        
        print("\n🎉 APK build successful!")
    else:
        print("\nSkipping Android packaging.")

    print("\n--- Build process finished ---")

if __name__ == '__main__':
    main()