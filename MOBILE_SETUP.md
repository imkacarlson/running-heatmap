# Running Heatmap Mobile Setup Guide

This guide will help you create a native Android APK of your running heatmap that works entirely offline on your phone.

## Overview

Your existing PC web server remains unchanged! This process creates a separate, native Android app that bundles all your run data locally.

## Step 1: Build Mobile Data Files

From your `server/` directory, run the mobile build script:

```bash
cd server
python build_mobile.py
```

This will:
- ✅ Convert your `runs.pkl` to JSON format
- ✅ Create a JavaScript spatial library
- ✅ Generate mobile-optimized HTML/CSS
- ✅ Add an offline service worker
- ✅ Create a complete `../mobile/` directory with all necessary web assets.

**Note:** This may take a few minutes with thousands of runs. The script will show progress.

## Step 2: Package as a Native Android APK

This step bundles the web assets into a native Android application using Capacitor.

1.  **Install prerequisites:**
    ```bash
    # Install Node.js and npm if not already installed
    # Install Android Studio
    # Install the Java Development Kit (JDK)
    ```

2.  **Package the Android app:**
    From the `server/` directory, run the packaging script:
    ```bash
    python package_android.py
    ```
    This script will create an Android project in the `mobile/` directory.

3.  **Build the APK in Android Studio:**
    ```bash
    cd ../mobile
    npx cap open android
    ```
    - This command will open the project in Android Studio.
    - From Android Studio, you can build the APK (`Build > Build Bundle(s) / APK(s) > Build APK(s)`) and run it on an emulator or a connected device.
    - Once built, you can find the APK in `mobile/android/app/build/outputs/apk/debug/`.

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

## Updating Mobile Data

When you add new runs to your PC version:

1.  **Import new runs on PC:**
    ```bash
    cd server
    python import_runs.py
    ```

2.  **Rebuild mobile assets:**
    ```bash
    python build_mobile.py
    ```

3.  **Sync and rebuild the APK:**
    ```bash
    cd ../mobile
    npx cap sync android
    npx cap open android
    ```
    - Rebuild the APK in Android Studio to include the new data.

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
