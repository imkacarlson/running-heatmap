# Running Heatmap

Transform your GPS activity history into an interactive offline Android app.

This mobile-focused project processes GPS files from Strava, Garmin Connect, and other sources to create a native Android application that visualizes your running routes as an interactive heatmap. The app works completely offline with all your data bundled locally.

## Features

### Core Functionality
- **Offline mobile app**: Native Android application built with Capacitor framework
- **Multi-format GPS import**: Support for FIT, GPX, and TCX files from various sources
- **Interactive heatmap**: Visualize all your activities on an OpenStreetMap-based mobile interface
- **Lasso selection**: Draw polygons to select and analyze activities in specific areas
- **Activity management**: Toggle individual runs on/off, view metadata (distance, duration, date)
- **Local data storage**: All data stays on your device - no cloud or internet required after install

### Technical Features  
- **Smart geometry processing**: Pre-computed simplified routes at multiple zoom levels for smooth performance
- **Spatial indexing**: R-tree implementation for fast area queries and selection
- **PMTiles vector tiles**: Efficient offline map rendering with nearby tile prefetching
- **On-device uploads**: Add new GPX files directly through the mobile app
- **Persistent storage**: Uploaded activities remain after app restarts

## Quick Start

### 1. Set up your environment

**Requirements:**
- Linux/WSL with Python 3.10+
- Node.js for mobile build tools
- Android development tools (for APK building)

**Install system dependencies:**
```bash
sudo apt update
sudo apt install python3-venv libspatialindex-dev tippecanoe
```

### 2. Import your GPS data

Place your GPS files in `data/raw/` (this directory is git-ignored):

**Supported formats:**
- Strava exports: `.fit.gz`, `.gpx.gz`, `.fit`, `.gpx`
- Garmin Connect: `.zip` archives containing `.fit` or `.tcx` files
- Individual files: `.gpx`, `.fit`, `.tcx`

**For Garmin Connect exports:**
1. Request export at https://www.garmin.com/en-US/account/datamanagement/exportdata/
2. Extract `UploadedFiles*.zip` files from `DI_CONNECT/DI-Connect-Fitness-Uploaded-Files/`
3. Copy these zip files directly to `data/raw/`

### 3. Process your data

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python process_data.py
```

This consolidated script:
- Imports and parses all GPS files in `data/raw/`
- Creates spatial indexes for fast queries
- Generates PMTiles for efficient offline rendering
- Outputs `runs.pkl` with processed data and `runs.pmtiles` for the mobile app

### 4. Build the mobile app

```bash
python build_mobile.py
```

The build script will:
- Check prerequisites and offer to install missing dependencies
- Convert your GPS data to mobile-compatible format
- Create a Capacitor-based Android project
- Build the final APK with all data bundled

**Quick rebuild option:**
```bash
python build_mobile.py --quick
```
Use this for faster rebuilds when only templates or JavaScript change.

### 5. Install on your device

```bash
# From WSL/Linux
APK=mobile/android/app/build/outputs/apk/debug/app-debug.apk
adb install -r $(wslpath -w "$APK")
```

See [MOBILE_SETUP.md](MOBILE_SETUP.md) for detailed setup instructions including emulator configuration and debugging.

## Using the Mobile App

### Basic Navigation
- **Pan and zoom**: Standard touch gestures to explore your activity map
- **Activity visibility**: All activities are visible by default as colored polylines
- **Zoom-dependent detail**: More route detail appears as you zoom in

### Lasso Selection
1. Tap the **⊙** button to enable lasso mode
2. Draw a polygon around activities you want to analyze
3. View the sidebar list of intersecting activities with metadata
4. Toggle individual activities on/off using the checkboxes
5. Clear selection to return to viewing all activities

### Adding New Activities
1. Tap the **⤴** upload button in the app
2. Select GPX files from your device storage
3. Activities are processed and stored locally
4. New activities persist between app restarts

## Development Workflow

### Adding New GPS Data
1. Copy new files to `data/raw/`
2. Run `python process_data.py` to update the dataset
3. Rebuild the mobile app with `python build_mobile.py`
4. Install the updated APK

### Testing

**Simplified test runner:**
```bash
cd testing
python run_tests.py                  # Run all tests
python run_tests.py --fast           # Skip expensive operations
python run_tests.py --one-test       # Interactive single test selection
```

The test framework validates:
- Mobile app functionality end-to-end
- GPS data processing pipeline
- APK build process
- UI interactions and lasso selection

### Architecture

**Project structure:**
```
├── data/raw/           # Your GPS files (git-ignored)
├── server/             # Backend processing and build scripts
│   ├── process_data.py # Consolidated GPS processing
│   ├── build_mobile.py # Mobile app build script
│   ├── app.py         # API server for uploads
│   └── *.template.*   # Mobile app templates
├── mobile/             # Generated Capacitor Android project
├── testing/            # Test framework for mobile app
└── docs/              # Setup and usage documentation
```

**Data flow:**
1. Raw GPS files → `process_data.py` → `runs.pkl` + `runs.pmtiles`
2. Processed data → `build_mobile.py` → Android APK
3. APK installation → Offline mobile app with bundled data

## Performance Notes

- **Dataset size**: ~5,000 activities typically result in ~40MB PMTiles file
- **Query performance**: Spatial indexing enables fast lasso queries on mobile devices
- **Offline operation**: No internet required after initial app install
- **Memory efficiency**: Progressive geometry simplification based on zoom level

## Privacy & Security

- **Local-only data**: All GPS data remains on your device
- **No tracking**: App works completely offline after installation  
- **No cloud storage**: Your activity history never leaves your device
- **Open source**: Full codebase available for review

## Troubleshooting

**Build issues:**
- Ensure all prerequisites are installed via `python build_mobile.py`
- Check that Android SDK and Java are properly configured
- See [MOBILE_SETUP.md](MOBILE_SETUP.md) for detailed setup instructions

**Performance issues:**
- Large datasets (>10k activities) may require additional optimization
- Consider filtering old or low-quality GPS tracks
- PMTiles compression helps but very large datasets may need chunking

**Testing issues:**
- Use `python run_tests.py --fast` to skip expensive APK rebuilding
- Ensure Android device/emulator is connected before running tests
- Check test reports in `testing/reports/test_report.html`

## Contributing

This project focuses on mobile-only GPS visualization. When contributing:
1. Maintain the mobile-first architecture
2. Test changes with the simplified test runner
3. Update documentation to reflect mobile app functionality
4. Ensure offline operation remains intact

---

**Ready to explore your running history on mobile?** 🏃‍♂️📱

Start with the Quick Start guide above and refer to [MOBILE_SETUP.md](MOBILE_SETUP.md) for detailed mobile development instructions.