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
    """Check for Node.js and npm, and verify the Node.js version."""
    print("\n🔍 Checking for Node.js and npm...")
    node_path = shutil.which('node')
    npm_path = shutil.which('npm')

    if not node_path or not npm_path:
        print("❌ Node.js and/or npm not found in PATH.", file=sys.stderr)
        print(
            "   Please install the latest LTS version of Node.js "
            "(which includes npm)",
            file=sys.stderr
        )
        print("   from https://nodejs.org/", file=sys.stderr)
        if sys.platform in ("linux", "darwin"):
            print(
                "   You might be able to use a package manager, e.g.,",
                file=sys.stderr
            )
            print(
                "   'sudo apt-get install nodejs npm' or 'brew install node'.",
                file=sys.stderr
            )
        return False

    # Check Node.js version
    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        version_str = result.stdout.strip().lstrip('v')
        major_version = int(version_str.split('.')[0])

        required_major = 20
        if major_version >= required_major:
            print(
                f"✅ Node.js (v{version_str}) and npm are installed and meet "
                f"version requirements (>= {required_major})."
            )
            return True

        print(
            f"❌ Node.js version is too old (v{version_str}). "
            f"Capacitor requires Node.js >= {required_major}.0.0.",
            file=sys.stderr
        )
        print("\n--- How to fix ---", file=sys.stderr)
        print(
            "   Please upgrade Node.js to the latest LTS version.",
            file=sys.stderr
        )
        print(
            "   We recommend using a version manager like nvm "
            "(Node Version Manager):",
            file=sys.stderr
        )
        print(
            "   1. Install nvm: "
            "https://github.com/nvm-sh/nvm#installing-and-updating",
            file=sys.stderr
        )
        print(
            "   2. Install and use the latest LTS Node.js: "
            "nvm install --lts && nvm use --lts",
            file=sys.stderr
        )
        print(
            "   Alternatively, download the latest version directly from "
            "https://nodejs.org/",
            file=sys.stderr
        )
        return False

    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
        print(f"❌ Could not determine Node.js version: {e}", file=sys.stderr)
        return False

def check_android_sdk():
    """Check for a basic Android development environment."""
    print("\n🔍 Checking for Android SDK environment...")
    android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    java_home = os.environ.get('JAVA_HOME')
    java_in_path = shutil.which('java')

    issues = []
    if not android_home or not os.path.exists(android_home):
        issues.append("- ANDROID_HOME or ANDROID_SDK_ROOT environment variable is not set or points to a non-existent directory.")
    if not (java_home and os.path.exists(java_home)) and not java_in_path:
        issues.append("- Java (JDK) not found. Set JAVA_HOME or ensure 'java' is in your PATH.")
    
    if not issues:
        print("✅ Android SDK and Java environment seem to be configured.")
        return True

    print("⚠️ Android SDK environment not fully configured.", file=sys.stderr)
    for issue in issues:
        print(issue, file=sys.stderr)
    
    print("\n--- How to fix ---", file=sys.stderr)
    print("1. Install Android Studio from https://developer.android.com/studio", file=sys.stderr)
    print("2. Use the SDK Manager in Android Studio to install the Android SDK.", file=sys.stderr)
    print("3. Set the ANDROID_HOME environment variable to the SDK location.", file=sys.stderr)
    print("   (e.g., export ANDROID_HOME=$HOME/Android/Sdk)", file=sys.stderr)
    print("4. Install a Java Development Kit (JDK). Android Studio often bundles one.", file=sys.stderr)
    print("5. Set the JAVA_HOME environment variable to the JDK location.", file=sys.stderr)
    print("   (e.g., export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64)", file=sys.stderr)
    print("6. Make sure to add the Android SDK's command-line tools, platform-tools, and emulator to your PATH.", file=sys.stderr)
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
        print(f"   - Removing existing directory: {mobile_dir}")
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
        
        if (i + 1) % 250 == 0 or (i + 1) == total_runs:
            elapsed = time.time() - start_time
            print(f"   ...processed {i + 1}/{total_runs} runs ({elapsed:.1f}s)", end='\r')
    print(f"\n✅ Data conversion complete. ({time.time() - start_time:.1f}s)")

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
    
    shutil.copy('mobile_template.html', os.path.join(mobile_dir, 'index.html'))
    shutil.copy('sw_template.js', os.path.join(mobile_dir, 'sw.js'))
    
    mobile_main_js = os.path.join(os.path.dirname(__file__), 'mobile_main.js')
    if os.path.exists(mobile_main_js):
        shutil.copy(mobile_main_js, os.path.join(mobile_dir, 'main.js'))
        print("   - Copied index.html, sw.js, and main.js")
    else:
        print("   - Warning: mobile_main.js not found. The mobile app may not work correctly.")

def create_capacitor_project(mobile_dir):
    """Initialize a Capacitor project."""
    print("\n⚡️ Creating Capacitor project...")

    if not run_command(['npm', 'init', '-y'], cwd=mobile_dir):
        print("❌ Failed to create package.json.", file=sys.stderr)
        return False

    config = {
        "appId": "com.run.heatmap",
        "appName": "Running Heatmap",
        "webDir": "www",
        "bundledWebRuntime": False
    }
    config_path = os.path.join(mobile_dir, 'capacitor.config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"   - Created capacitor.config.json")
    return True

def setup_www_directory(mobile_dir):
    """Create the 'www' directory and move web assets into it."""
    print("\n🏗 Setting up 'www' directory for Capacitor...")
    www_dir = os.path.join(mobile_dir, 'www')
    if os.path.exists(www_dir):
        shutil.rmtree(www_dir)
    os.makedirs(www_dir)

    assets = ['index.html', 'main.js', 'sw.js', 'data']
    
    all_moved = True
    for asset in assets:
        src = os.path.join(mobile_dir, asset)
        dst = os.path.join(www_dir, asset)
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"   - Moved {asset} to {www_dir}")
        else:
            print(f"   - Warning: Asset not found to move: {asset}")
            all_moved = False
    
    return all_moved

def fix_java_compatibility(mobile_dir):
    """Fix Java compatibility issues by adding compileOptions to both app and root build.gradle."""
    print("\n🔧 Configuring Java compatibility...")
    
    # Fix app/build.gradle
    app_build_gradle = os.path.join(mobile_dir, 'android', 'app', 'build.gradle')
    app_fixed = False
    if os.path.exists(app_build_gradle):
        with open(app_build_gradle, 'r') as f:
            content = f.read()
        
        if 'compileOptions' not in content:
            import re
            pattern = r'(compileSdk\s+[^\n]+\n)'
            replacement = r'\1    \n    compileOptions {\n        sourceCompatibility JavaVersion.VERSION_17\n        targetCompatibility JavaVersion.VERSION_17\n    }\n    '
            new_content = re.sub(pattern, replacement, content)
            
            if new_content != content:
                with open(app_build_gradle, 'w') as f:
                    f.write(new_content)
                app_fixed = True
    
    # Fix root build.gradle for all subprojects (including Capacitor modules)
    root_build_gradle = os.path.join(mobile_dir, 'android', 'build.gradle')
    root_fixed = False
    if os.path.exists(root_build_gradle):
        with open(root_build_gradle, 'r') as f:
            content = f.read()
        
        if 'subprojects {' not in content:
            # Add subprojects configuration before the clean task
            subprojects_config = '''
subprojects {
    afterEvaluate { project ->
        if (project.hasProperty('android')) {
            project.android {
                compileOptions {
                    sourceCompatibility JavaVersion.VERSION_17
                    targetCompatibility JavaVersion.VERSION_17
                }
            }
        }
    }
}
'''
            # Insert before the clean task
            pattern = r'(task clean\(type: Delete\))'
            replacement = subprojects_config + r'\n\1'
            new_content = re.sub(pattern, replacement, content)
            
            if new_content != content:
                with open(root_build_gradle, 'w') as f:
                    f.write(new_content)
                root_fixed = True
    
    if app_fixed or root_fixed:
        print("   - Added Java 17 compatibility configuration")
        return True
    else:
        print("   - Java compatibility already configured")
        return True

# --- Android Packaging ---

def package_for_android(mobile_dir):
    """Run the full Android packaging process."""
    print("\n" + "-"*20)
    print("📦 Starting Android Packaging Process")
    print("-"*20)

    if not check_node_and_npm() or not check_android_sdk():
        print("\n❌ Cannot proceed with Android packaging due to missing prerequisites.", file=sys.stderr)
        return

    if not create_capacitor_project(mobile_dir):
        return

    print("\nInstalling Capacitor dependencies...")
    if not run_command(['npm', 'install', '@capacitor/core', '@capacitor/cli', '@capacitor/android'], cwd=mobile_dir, show_progress=True):
        print("❌ Failed to install Capacitor dependencies.", file=sys.stderr)
        return

    print("\nAdding Android platform to Capacitor project...")
    if not run_command(['npx', 'cap', 'add', 'android'], cwd=mobile_dir):
        print("❌ Failed to add Android platform.", file=sys.stderr)
        return

    if not setup_www_directory(mobile_dir):
        print("❌ Could not set up 'www' directory. Aborting.", file=sys.stderr)
        return

    print("\nSyncing web assets with Capacitor...")
    if not run_command(['npx', 'cap', 'sync'], cwd=mobile_dir):
        print("❌ Failed to sync web assets.", file=sys.stderr)
        return

    # Fix Java compatibility issues
    fix_java_compatibility(mobile_dir)

    print("\n🔨 Building Android APK...")
    android_dir = os.path.join(mobile_dir, 'android')
    gradlew_cmd = 'gradlew.bat' if sys.platform == 'win32' else './gradlew'
    
    if not run_command([gradlew_cmd, 'assembleDebug'], cwd=android_dir, show_progress=True):
        print("❌ Failed to build APK.", file=sys.stderr)
        print("\n💡 Try opening the project in Android Studio to resolve issues:", file=sys.stderr)
        print(f"   npx cap open android (from the '{mobile_dir}' directory)", file=sys.stderr)
        return
        
    apk_path = os.path.join(android_dir, 'app', 'build', 'outputs', 'apk', 'debug', 'app-debug.apk')
    print("\n🎉 APK build successful!")
    print(f"   Find it at: {os.path.abspath(apk_path)}")

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