# Running Heatmap Mobile

Create a native Android app to visualize your entire GPS activity history on an interactive offline map.

This project processes raw GPS files (Strava export, Garmin Connect, etc.) and packages them into a native Android application that works completely offline. The app features an interactive map with heatmap-style polylines, activity selection tools, and the ability to upload new GPX files directly on your device.

## Features

- Import **FIT**, **GPX**, and **TCX** files (Garmin archives are handled automatically)
- Precompute simplified geometries at several zoom levels for fast drawing
- R-tree spatial index for quick bounding-box and lasso queries
- **PMTiles** vector tiles for smooth offline rendering
- Heatmap style polylines on an OpenStreetMap basemap
- Draw a polygon to select an area and list the intersecting activities
- Sidebar shows metadata (type, date, distance, duration) and lets you toggle individual runs
- Upload new **GPX** files directly on your device—they are stored locally and persist between sessions
- Completely offline operation - no internet connection required after installation
- All data stays private on your device

## Prerequisites

- Linux/WSL with Python 3.10+
- System packages:

  ```bash
  sudo apt update
  sudo apt install python3-venv libspatialindex-dev
  sudo apt install tippecanoe nodejs npm openjdk-17-jdk
  ```

- Android device with USB debugging enabled (for installation)
- Windows `adb` server (if using WSL) or Linux `adb` tools

## Quick Start

### 1. Import your activities

Put your raw GPS files under `data/raw/` (git ignored):
- Strava exports: `.fit.gz`, `.gpx.gz`, `.fit`, `.gpx`
- Garmin Connect exports: `.zip` containing `.fit` or `.txt`/`.tcx`
  - After requesting a Garmin export at https://www.garmin.com/en-US/account/datamanagement/exportdata/, look under
    `DI_CONNECT/DI-Connect-Fitness-Uploaded-Files/` for many
    `UploadedFiles*.zip` archives. Drop these zip files into
    `data/raw/` to import them.

### 2. Process your data

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r mobile/requirements.txt

# Process your GPS files into the mobile-ready format
python mobile/data_processor.py --all
```

This creates `mobile/runs.pkl` and `mobile/runs.pmtiles` files containing your processed activity data.

### 3. Build the mobile app

```bash
python mobile/build.py
```

The script will guide you through:
- ✅ Checking prerequisites (Node.js, Android SDK, etc.)
- ✅ Offering to install missing components
- ✅ Building the mobile app assets
- ✅ Creating the Android APK

The final APK will be created as `mobile/running-heatmap-*.apk`.

### 4. Install on your device

```bash
# Install the APK on your connected Android device
APK=mobile/android/app/build/outputs/apk/debug/app-debug.apk
adb install -r $(wslpath -w "$APK")  # WSL
# or
adb install -r "$APK"  # Linux
```

## Using the Mobile App

### Selecting activities

Use the **⊙** button to draw a lasso polygon. The sidebar lists each activity in that area with distance and duration. You can toggle activities on/off or clear the selection to return to viewing everything.

### Uploading new runs

After installing the app, you can add new activities directly on your device:
1. Open the app and tap the **⤴** upload button
2. Choose one or more GPX files from your device
3. The runs are parsed and stored locally, remaining visible even after restarting the app

## Data Processing Options

The consolidated data processor supports flexible workflows:

```bash
# Import GPS files only (creates mobile/runs.pkl)
python mobile/data_processor.py --import-only

# Generate PMTiles only (requires existing mobile/runs.pkl)
python mobile/data_processor.py --pmtiles-only

# Process everything (default - import + PMTiles)
python mobile/data_processor.py --all

# Custom paths
python mobile/data_processor.py --raw-dir custom/path --output-pkl mobile/runs.pkl --output-pmtiles mobile/runs.pmtiles
```

### Adding new activities

1. Drop new GPS files into `data/raw/`
2. Rerun `python mobile/data_processor.py --all`
3. Rebuild the mobile app: `python mobile/build.py --quick`
4. Reinstall the APK on your device

## Development and Testing

### Fast rebuild cycle

For development, use the `--quick` flag to skip data processing when only code changes:

```bash
python mobile/build.py --quick
adb install -r $(wslpath -w mobile/android/app/build/outputs/apk/debug/app-debug.apk)
```

### Running tests

The project includes a comprehensive test suite for mobile functionality:

```bash
# Run all mobile tests
python testing/run_tests.py

# Run tests in fast mode (skip expensive operations)
python testing/run_tests.py --fast

# Interactive single test selection
python testing/run_tests.py --one-test

# Run specific test files
python testing/run_tests.py testing/test_basic_lasso_selection.py
```

### Debugging with Chrome DevTools

1. Enable ADB over Wi-Fi on your device
2. Connect via `adb connect <device-ip>:5555`
3. Set up port forwarding: `adb reverse tcp:9222 tcp:9222`
4. Launch the app and go to `chrome://inspect/#devices` in desktop Chrome
5. Click **inspect** under the Running Heatmap app

## WSL Setup Guide

### One-time Windows host preparation

1. Download Google Platform-Tools and unzip to `C:\sdk\platform-tools\`
2. Add that folder to your Windows **Path**
3. Enable **USB debugging** on your phone and accept the RSA fingerprint
4. In **PowerShell** run `adb devices` and verify the device shows up as `device`

### Configure WSL to use Windows ADB

```bash
sudo ln -sf /mnt/c/sdk/platform-tools/adb.exe /usr/local/bin/adb
adb version    # should match the version in PowerShell
```

### Switch to ADB over Wi-Fi

```bash
# Find your phone's IP address
adb shell ip route | grep -E "src [0-9.]+"

# Enable TCP mode and connect wirelessly
adb tcpip 5555
# Unplug USB cable
PHONE_IP=192.168.1.73  # Replace with your phone's IP
adb connect $PHONE_IP:5555
adb devices  # Should show $PHONE_IP:5555 device
```

## Performance and Storage

- A dataset of ~5k runs fits in a PMTiles file around 40 MB
- PMTiles enable smooth offline map rendering with fast lasso queries
- All data processing uses memory-efficient chunked operations
- Spatial indexing provides fast bounding-box queries even with large datasets

## Security & Privacy

- ✅ **All data stays local** - no cloud or server required
- ✅ **No tracking** - the app works completely offline
- ✅ **Your runs stay private** - data never leaves your device
- ✅ **No internet required** - full functionality works offline

## Project Structure

```
running-heatmap/
├── mobile/                    # Mobile app components
│   ├── api.py                # Mobile API server
│   ├── build.py              # Mobile build script
│   ├── data_processor.py     # Consolidated data processing
│   ├── requirements.txt      # Mobile dependencies
│   ├── runs.pkl             # Processed activity data
│   ├── runs.pmtiles         # Vector tiles for offline rendering
│   └── android/             # Native Android project (generated)
├── testing/                  # Test framework
│   ├── run_tests.py         # Simplified test runner
│   └── test_*.py            # Mobile functionality tests
├── data/
│   └── raw/                 # Your GPS files (git ignored)
└── README.md                # This file
```

Enjoy exploring your activity history on mobile! 🏃‍♂️📱
