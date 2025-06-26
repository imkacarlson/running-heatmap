#!/usr/bin/env python3
"""
Android APK packaging script for running heatmap mobile app.
Uses Capacitor to create a native Android wrapper.
"""

import os
import json
import shutil
import subprocess
import sys
from pathlib import Path

def check_prerequisites():
    """Check if required tools are installed."""
    required_tools = ['node', 'npm', 'npx']
    
    print("🔍 Checking prerequisites...")
    
    for tool in required_tools:
        try:
            result = subprocess.run([tool, '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ {tool}: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {tool} not found. Please install Node.js and npm.")
            return False
    
    return True

def create_capacitor_project(mobile_dir):
    """Create Capacitor project structure."""
    
    print("📱 Creating Capacitor project...")
    
    # Create package.json
    package_json = {
        "name": "running-heatmap-mobile",
        "version": "1.0.0",
        "description": "Mobile version of running heatmap",
        "main": "index.js",
        "scripts": {
            "build": "echo 'Build complete'",
            "sync": "npx cap sync",
            "open": "npx cap open android",
            "run": "npx cap run android"
        },
        "dependencies": {
            "@capacitor/core": "^5.0.0",
            "@capacitor/android": "^5.0.0",
            "@capacitor/cli": "^5.0.0"
        },
        "devDependencies": {
            "@capacitor/cli": "^5.0.0"
        }
    }
    
    package_file = os.path.join(mobile_dir, 'package.json')
    with open(package_file, 'w') as f:
        json.dump(package_json, f, indent=2)
    
    print(f"📄 Created package.json")
    
    # Create capacitor.config.json
    capacitor_config = {
        "appId": "com.runningheatmap.mobile",
        "appName": "Running Heatmap",
        "webDir": "www",
        "bundledWebRuntime": False,
        "server": {
            "androidScheme": "https"
        },
        "android": {
            "allowMixedContent": True,
            "captureInput": True,
            "webContentsDebuggingEnabled": True
        },
        "plugins": {
            "SplashScreen": {
                "launchShowDuration": 2000,
                "backgroundColor": "#007bff",
                "showSpinner": True,
                "spinnerColor": "#ffffff"
            }
        }
    }
    
    config_file = os.path.join(mobile_dir, 'capacitor.config.json')
    with open(config_file, 'w') as f:
        json.dump(capacitor_config, f, indent=2)
    
    print(f"⚙️ Created capacitor.config.json")
    
    return package_file, config_file

def setup_www_directory(mobile_dir):
    """Set up the www directory with web assets."""
    
    www_dir = os.path.join(mobile_dir, 'www')
    os.makedirs(www_dir, exist_ok=True)
    
    # Copy mobile HTML template
    src_html = os.path.join(os.path.dirname(__file__), 'mobile_template.html')
    dst_html = os.path.join(www_dir, 'index.html')
    shutil.copy2(src_html, dst_html)
    
    # Copy service worker
    src_sw = os.path.join(os.path.dirname(__file__), 'sw_template.js')
    dst_sw = os.path.join(www_dir, 'sw.js')
    shutil.copy2(src_sw, dst_sw)
    
    # Create js directory and copy spatial library
    js_dir = os.path.join(www_dir, 'js')
    os.makedirs(js_dir, exist_ok=True)
    
    # The spatial.js file should have been created by build_mobile.py
    src_spatial = os.path.join(mobile_dir, 'js', 'spatial.js')
    if os.path.exists(src_spatial):
        dst_spatial = os.path.join(js_dir, 'spatial.js')
        shutil.copy2(src_spatial, dst_spatial)
        print("✅ Copied spatial.js")
    else:
        print("⚠️ spatial.js not found - make sure to run build_mobile.py first")
    
    # Copy data directory
    src_data = os.path.join(mobile_dir, 'data')
    dst_data = os.path.join(www_dir, 'data')
    if os.path.exists(src_data):
        shutil.copytree(src_data, dst_data, dirs_exist_ok=True)
        print("✅ Copied data directory")
    else:
        print("⚠️ data directory not found - make sure to run build_mobile.py first")
    
    # Update HTML to register service worker
    with open(dst_html, 'r') as f:
        html_content = f.read()
    
    # Add service worker registration
    sw_registration = '''
    <script>
      // Register service worker for offline functionality
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('./sw.js')
            .then((registration) => {
              console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
              console.log('SW registration failed: ', registrationError);
            });
        });
      }
    </script>
  </body>'''
    
    html_content = html_content.replace('</body>', sw_registration)
    
    with open(dst_html, 'w') as f:
        f.write(html_content)
    
    print(f"📁 Set up www directory: {www_dir}")
    return www_dir

def create_app_icons(www_dir):
    """Create basic app icons (placeholder)."""
    
    # Create simple SVG icons as placeholders
    # In a real app, you'd want proper PNG icons
    
    icon_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 192 192">
  <rect width="192" height="192" fill="#007bff"/>
  <circle cx="96" cy="96" r="60" fill="none" stroke="white" stroke-width="8"/>
  <path d="M96 56 L96 136 M76 76 L116 116 M116 76 L76 116" stroke="white" stroke-width="4" stroke-linecap="round"/>
</svg>'''
    
    icon_path = os.path.join(www_dir, 'icon-192.png')
    # For now, just create a placeholder text file
    # In production, you'd convert SVG to PNG
    with open(icon_path.replace('.png', '.svg'), 'w') as f:
        f.write(icon_svg)
    
    print("🎨 Created placeholder app icons")

def install_dependencies_and_init(mobile_dir):
    """Install npm dependencies and initialize Capacitor."""
    
    print("📦 Installing dependencies...")
    
    # Install npm dependencies
    try:
        subprocess.run(['npm', 'install'], cwd=mobile_dir, check=True)
        print("✅ npm dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install npm dependencies: {e}")
        return False
    
    # Initialize Capacitor
    try:
        subprocess.run(['npx', 'cap', 'add', 'android'], cwd=mobile_dir, check=True)
        print("✅ Android platform added")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to add Android platform: {e}")
        return False
    
    # Sync web assets
    try:
        subprocess.run(['npx', 'cap', 'sync'], cwd=mobile_dir, check=True)
        print("✅ Web assets synced")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to sync web assets: {e}")
        return False
    
    return True

def create_build_script(mobile_dir):
    """Create convenience scripts for building and running."""
    
    # Create build script
    build_script = '''#!/bin/bash
set -e

echo "🔨 Building Running Heatmap Mobile App..."

# Sync web assets
npx cap sync

echo "✅ Build complete!"
echo ""
echo "To run on Android:"
echo "  npx cap run android"
echo ""
echo "To open in Android Studio:"
echo "  npx cap open android"
'''
    
    build_path = os.path.join(mobile_dir, 'build.sh')
    with open(build_path, 'w') as f:
        f.write(build_script)
    os.chmod(build_path, 0o755)
    
    # Create README
    readme = '''# Running Heatmap Mobile App

This is the mobile version of your running heatmap, packaged as an Android app using Capacitor.

## Prerequisites

- Node.js and npm
- Android Studio
- Java Development Kit (JDK)

## Building the App

1. Make sure you've run the mobile build script first:
   ```bash
   cd ../server
   python build_mobile.py
   ```

2. Install dependencies and sync:
   ```bash
   npm install
   npx cap sync
   ```

3. Open in Android Studio:
   ```bash
   npx cap open android
   ```

4. Build and run from Android Studio, or use:
   ```bash
   npx cap run android
   ```

## Development

- Web assets are in the `www/` directory
- After making changes, run `npx cap sync` to update the native project
- The app data is bundled locally - no server required!

## Offline Support

The app includes a service worker for offline functionality:
- Static assets are cached
- Run data is cached for offline viewing
- Map tiles are cached as you browse

Enjoy your runs on mobile! 🏃‍♂️📱
'''
    
    readme_path = os.path.join(mobile_dir, 'README.md')
    with open(readme_path, 'w') as f:
        f.write(readme)
    
    print(f"📝 Created build scripts and documentation")

def build_apk(mobile_dir):
    """Build APK using Gradle."""
    
    print("🔨 Building APK...")
    
    android_dir = os.path.join(mobile_dir, 'android')
    
    # Build debug APK
    try:
        print("📦 Running Gradle assembleDebug...")
        result = subprocess.run(['./gradlew', 'assembleDebug'], 
                              cwd=android_dir, check=True, 
                              capture_output=True, text=True)
        print("✅ Debug APK built successfully")
        
        # Find the APK file
        apk_path = os.path.join(android_dir, 'app', 'build', 'outputs', 'apk', 'debug', 'app-debug.apk')
        if os.path.exists(apk_path):
            # Copy APK to mobile root with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_apk = os.path.join(mobile_dir, f'running-heatmap-{timestamp}.apk')
            shutil.copy2(apk_path, output_apk)
            print(f"📱 APK saved to: {output_apk}")
            return output_apk
        else:
            print(f"⚠️ APK not found at expected location: {apk_path}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ APK build failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout[-1000:])  # Last 1000 chars
        if e.stderr:
            print("STDERR:", e.stderr[-1000:])  # Last 1000 chars
        return None

def main():
    """Main packaging function."""
    
    print("🚀 Packaging Running Heatmap for Android...")
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Ensure mobile directory exists
    mobile_dir = '../mobile'
    if not os.path.exists(mobile_dir):
        print(f"❌ Mobile directory not found: {mobile_dir}")
        print("Please run build_mobile.py first to create the mobile data files.")
        sys.exit(1)
    
    try:
        # Create Capacitor project
        create_capacitor_project(mobile_dir)
        
        # Set up www directory
        www_dir = setup_www_directory(mobile_dir)
        
        # Create app icons
        create_app_icons(www_dir)
        
        # Install dependencies and initialize
        if not install_dependencies_and_init(mobile_dir):
            sys.exit(1)
        
        # Create build scripts
        create_build_script(mobile_dir)
        
        # Build APK automatically
        apk_path = build_apk(mobile_dir)
        
        print(f"\n🎉 Android packaging complete!")
        print(f"📱 Mobile app directory: {os.path.abspath(mobile_dir)}")
        
        if apk_path:
            print(f"📦 APK built: {os.path.abspath(apk_path)}")
            print(f"\nTo install on device:")
            print(f"  adb install {os.path.basename(apk_path)}")
        else:
            print(f"\n⚠️ APK build failed, but you can still:")
            print(f"1. cd {mobile_dir}")
            print(f"2. npx cap open android")
            print(f"3. Build and run in Android Studio")
        
    except Exception as e:
        print(f"❌ Packaging failed: {e}")
        raise

if __name__ == '__main__':
    main()