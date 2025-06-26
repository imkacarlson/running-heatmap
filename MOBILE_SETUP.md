# Running Heatmap Mobile Setup Guide

This guide will help you create a native Android APK of your running heatmap that works entirely offline on your phone.

## Overview

Your existing PC web server remains unchanged! This process creates a separate, native Android app that bundles all your run data locally.

## WSL Prerequisites (Windows Users)

If you're running this in WSL (Windows Subsystem for Linux), install these prerequisites first:

```bash
# Update package list
sudo apt update

# Install Java Development Kit (required for Android builds)
sudo apt install openjdk-17-jdk

# Install Node.js and npm (if not already installed)
sudo apt install nodejs npm

# Install Android SDK command line tools
sudo apt install wget unzip
mkdir -p ~/android-sdk/cmdline-tools
cd ~/android-sdk/cmdline-tools
wget https://dl.google.com/android/repository/commandlinetools-linux-latest.zip
unzip commandlinetools-linux-*.zip
mv cmdline-tools latest # This step is still crucial for correct SDK setup
cd ~

# Set up environment variables (add to ~/.bashrc)
echo 'export ANDROID_HOME=~/android-sdk' >> ~/.bashrc
echo 'export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools' >> ~/.bashrc
source ~/.bashrc

# Accept licenses and install SDK components
yes | sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-33" "build-tools;33.0.0"

# Verify installations
java -version
node --version  
npm --version
echo $ANDROID_HOME
```

**Installing APKs from WSL:**
- Copy APK to Windows: `cp mobile/running-heatmap-*.apk /mnt/c/Users/YourName/Desktop/`
- Or use `adb install mobile/running-heatmap-*.apk` directly from WSL

## Quick Start (Fully Automated)

The fastest way to build a complete APK:

```bash
cd server
python build_mobile.py --full
```

This single command will:
- ✅ Convert your `runs.pkl` to JSON format
- ✅ Create a JavaScript spatial library  
- ✅ Generate mobile-optimized HTML/CSS
- ✅ Add an offline service worker
- ✅ Set up Capacitor Android project
- ✅ Install npm dependencies
- ✅ **Build the APK automatically using Gradle**
- ✅ Output a timestamped APK file ready to install

**Output:** You'll get a file like `mobile/running-heatmap-20250626_143022.apk`

## Prerequisites

Before running the automated build, make sure you have:

```bash
# Node.js and npm
node --version
npm --version

# Java Development Kit (JDK) for Android builds
java -version

# Optional: Android SDK tools (if you want to install directly)
adb --version
```

## Manual Step-by-Step Process

If you prefer more control or want to understand each step:

### Step 1: Build Mobile Data Files

```bash
cd server
python build_mobile.py
```

This creates the mobile web assets in `../mobile/` directory.

### Step 2: Package and Build APK

```bash
python package_android.py
```

This will:
- ✅ Set up Capacitor Android project
- ✅ Install npm dependencies
- ✅ Sync web assets to Android project
- ✅ **Build APK using Gradle**
- ✅ Output timestamped APK file

### Step 3: Alternative Android Studio Method

If you prefer using Android Studio:

```bash
cd ../mobile
npx cap open android
```

Then build manually in Android Studio (`Build > Build Bundle(s) / APK(s) > Build APK(s)`).

## Step 3: Test Mobile Features

### Core Features
- ✅ **Pan/zoom:** Touch gestures work smoothly
- ✅ **Heatmap display:** All your runs visible with proper styling
- ✅ **Offline mode:** Works without internet after first load
- ✅ **Performance:** Optimized for mobile hardware

### Advanced Features
- ✅ **Lasso selection:** Touch and drag to select areas
- ✅ **Run filtering:** View runs in selected areas
- ✅ **Metadata display:** Date, distance, duration for each run
- ✅ **Touch controls:** Mobile-optimized buttons and interactions

## Step 4: Keep Both Versions

### Your PC Version (Unchanged)
```bash
cd server
flask run
# Visit http://127.0.0.1:5000
```

### Your Mobile Version
- Completely standalone native Android app
- All data bundled locally
- No server required
- Works offline

## File Structure

After building, you'll have:

```
running-heatmap/
├── server/              # Your original PC version (unchanged)
│   ├── app.py          # Flask server
│   ├── runs.pkl        # Your run data
│   ├── build_mobile.py # Mobile build script
│   └── package_android.py # Android packaging script
├── web/                # Original web interface (unchanged)
└── mobile/             # NEW: Mobile project
    ├── www/            # Web assets for the app
    ├── android/        # Native Android project
    ├── node_modules/   # Dependencies
    └── ...
```

## Installing the APK

Once you have your APK file:

### Option 1: Direct Install (if you have adb)
```bash
adb install mobile/running-heatmap-YYYYMMDD_HHMMSS.apk
```

### Option 2: Manual Install
1. Copy the APK file to your Android device
2. Enable "Install from unknown sources" in Android settings
3. Tap the APK file to install

## Updating Mobile Data

When you add new runs to your PC version:

**Quick Update (Recommended):**
```bash
cd server
python import_runs.py           # Import new runs
python build_mobile.py --full   # Rebuild everything + new APK
```

**Manual Update Process:**
1.  **Import new runs on PC:**
    ```bash
    cd server
    python import_runs.py
    ```

2.  **Rebuild mobile assets:**
    ```bash
    python build_mobile.py
    ```

3.  **Rebuild the APK:**
    ```bash
    python package_android.py
    ```

## Troubleshooting

### Performance Issues
- The app should work smoothly offline. If you experience initial slowness, it might be related to the initial data load.
- The Pixel 7A has plenty of power for this app.

### Missing Features
- Polygon selection uses simplified geometry intersection for performance.
- All core features from the PC version are preserved.
- Touch interactions are optimized for mobile.

## Security & Privacy

- ✅ **All data stays local** - no cloud/server required.
- ✅ **No tracking** - completely offline after the first load.
- ✅ **Your runs stay private** - the data never leaves your device.

Enjoy your runs on mobile! 🏃‍♂️📱
