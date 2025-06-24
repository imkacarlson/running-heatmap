# Running Heatmap Mobile Setup Guide

This guide will help you create a mobile version of your running heatmap that works entirely offline on your Android phone.

## Overview

Your existing PC web server remains unchanged! This creates a separate mobile app that bundles all your run data locally.

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
- ✅ Add offline service worker
- ✅ Create a complete `../mobile/` directory

**Note:** This may take a few minutes with thousands of runs. The script will show progress and final file sizes.

## Step 2: Choose Your Mobile Option

### Option A: Progressive Web App (Recommended)

Easiest option - no Android development tools required:

1. **Test locally first:**
   ```bash
   cd ../mobile
   python -m http.server 8080
   ```
   
2. **Visit http://localhost:8080 on your phone**
   - Connect phone to same WiFi network
   - Open browser and navigate to your computer's IP:8080
   - Test all features work correctly

3. **Deploy to phone:**
   - Copy the entire `mobile/` folder to your phone
   - Use any file manager app to serve the HTML
   - OR upload to a simple web host and access via browser
   - Add to home screen when prompted for app-like experience

### Option B: Native Android APK

For a true native app experience:

1. **Install prerequisites:**
   ```bash
   # Install Node.js if not already installed
   # Install Android Studio
   # Install Java Development Kit (JDK)
   ```

2. **Package as Android app:**
   ```bash
   cd server
   python package_android.py
   ```

3. **Build in Android Studio:**
   ```bash
   cd ../mobile
   npx cap open android
   ```
   - Build and run from Android Studio
   - Install APK on your phone

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
- Completely standalone
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
│   └── build_mobile.py # Mobile build script
├── web/                # Original web interface (unchanged)
└── mobile/             # NEW: Mobile version
    ├── index.html      # Mobile-optimized interface
    ├── sw.js          # Service worker for offline
    ├── data/          # Your runs in JSON format
    └── js/            # Client-side spatial library
```

## Updating Mobile Data

When you add new runs:

1. **Import new runs on PC:**
   ```bash
   cd server
   python import_runs.py
   ```

2. **Rebuild mobile version:**
   ```bash
   python build_mobile.py
   ```

3. **Update phone app:**
   - Copy new `mobile/` folder to phone
   - OR rebuild APK if using Android Studio

## Troubleshooting

### Large File Sizes
- Check `mobile/data/` directory size
- Consider reducing run data if needed
- Service worker will cache for fast loading

### Performance Issues
- Ensure good WiFi for initial data load
- Once cached, should work smoothly offline
- Pixel 7A has plenty of power for this app

### Missing Features
- Polygon selection uses simplified geometry intersection
- All core features preserved from PC version
- Touch interactions optimized for mobile

## Security & Privacy

- ✅ **All data stays local** - no cloud/server required
- ✅ **No tracking** - completely offline after first load  
- ✅ **Your runs stay private** - never leaves your device

## Need Help?

1. **Check console logs** in mobile browser for errors
2. **Test PC version first** to ensure data is good
3. **Verify file sizes** in mobile/data/ directory
4. **Try PWA option first** before Android APK

Enjoy your runs on mobile! 🏃‍♂️📱