# Mobile App Testing Framework

This directory contains the automated testing framework for the Running Heatmap mobile application, focused on validating the complete offline mobile app experience.

## 🚀 Quick Start

**Simple test execution:**
```bash
python run_tests.py                  # Run all tests
python run_tests.py --fast           # Skip expensive operations (APK builds)
python run_tests.py --one-test       # Interactive single test selection
```

**Key Features:**
- 📱 **Mobile-focused testing**: End-to-end validation of Android APK functionality
- 🔄 **Complete data pipeline**: GPX → process_data.py → APK → Mobile visualization  
- 🏗️ **Isolated environment**: Never touches production data
- 📊 **Automated validation**: Map rendering, lasso selection, upload functionality
- 🤖 **Infrastructure management**: Automatic Appium server and device detection

## Prerequisites

The test framework will check for and help install:
- **Python testing packages**: pytest, appium-python-client
- **Android tools**: ADB for device communication
- **Node.js**: For Appium server
- **Test data**: Sample GPX files in `test_data/`

## Running Tests

### Basic Commands

```bash
# Run all mobile tests (recommended)
python run_tests.py

# Fast mode - skip APK building, use existing APK
python run_tests.py --fast

# Interactive mode - select specific test
python run_tests.py --one-test
```

### What Gets Tested

**Core Mobile Functionality:**
- ✅ APK build process from GPS data
- ✅ Mobile app startup and map rendering
- ✅ Lasso selection and area queries
- ✅ GPX file upload through mobile interface
- ✅ Activity toggling and metadata display
- ✅ Offline operation validation

**Data Processing Pipeline:**
- ✅ GPS file parsing (GPX, FIT, TCX formats)
- ✅ PMTiles generation for offline maps
- ✅ Spatial indexing for fast queries
- ✅ Mobile app data bundling

## Test Environment

### Device Requirements
- Android device or emulator connected via ADB
- USB debugging enabled
- Sufficient storage for test APK installation

### Test Data
Tests use isolated sample data in `test_data/`:
- `sample_run.gpx` - Basic GPS track for functionality testing
- `eastside_run.gpx` - Complex route for advanced testing
- `manual_upload_run.gpx` - File for upload testing

### Automated Setup
The test framework automatically:
1. Detects connected Android devices
2. Starts Appium server for mobile automation
3. Builds test APK with sample data
4. Installs and tests the mobile app
5. Generates HTML test reports
6. Cleans up test installations

## Test Structure

```
testing/
├── run_tests.py              # Main test runner (simplified)
├── test_*.py                 # Individual test modules
├── test_data/                # Sample GPS files
├── smoke_tests/              # Quick validation tests
├── reports/                  # HTML test reports
└── cached_test_*/            # Cached test artifacts
```

**Key Test Modules:**
- `test_00_infrastructure_setup.py` - Environment validation
- `test_01_activity_visibility.py` - Basic mobile app functionality
- `test_basic_lasso_selection.py` - Area selection testing
- `test_upload_functionality.py` - Mobile file upload testing
- `test_end_to_end_gpx_mobile.py` - Complete workflow validation

## Development Workflow

### Adding New Tests
1. Create test file following naming convention: `test_<feature>.py`
2. Use `base_mobile_test.py` as foundation for mobile tests
3. Focus on mobile app functionality and user workflows
4. Test with both `--fast` and full build modes

### Test Development Tips
- Use page object pattern for mobile UI interactions
- Test offline functionality - no network dependencies
- Validate data persistence between app restarts
- Include both positive and negative test cases

### Debugging Tests
```bash
# Run single test interactively
python run_tests.py --one-test

# Check test reports
open testing/reports/test_report.html

# View mobile app logs (if device connected)
adb logcat -s chromium AndroidRuntime CapacitorConsole
```

## Architecture

### Mobile Test Flow
1. **Build Phase**: Create test APK with sample GPS data
2. **Install Phase**: Deploy APK to connected Android device
3. **Test Phase**: Automate mobile app interactions via Appium
4. **Validate Phase**: Check map rendering, data accuracy, offline functionality
5. **Cleanup Phase**: Remove test app and temporary files

### Key Components
- **process_data.py**: Consolidated GPS processing for test data
- **build_mobile.py**: APK generation with bundled test data
- **Appium WebDriver**: Mobile app automation and interaction
- **Capacitor**: Native Android app framework being tested

## Troubleshooting

### Common Issues

**No Android devices found:**
```bash
# Check device connection
adb devices

# Start emulator manually if needed
emulator -avd YourAVDName
```

**APK build failures:**
```bash
# Check prerequisites
python build_mobile.py

# Run with verbose output
python run_tests.py --one-test  # Select infrastructure test
```

**Test timeouts:**
- Ensure device has sufficient performance
- Use `--fast` mode to skip expensive operations
- Check that test APK installed successfully

**Appium connection issues:**
- Verify Node.js and npm are installed
- Check that Android device allows USB debugging
- Restart ADB server: `adb kill-server && adb start-server`

### Getting Help

1. Check test reports in `testing/reports/test_report.html`
2. Run infrastructure test: `python run_tests.py --one-test` → select test_00
3. Verify mobile build works: `cd server && python build_mobile.py`
4. Check mobile app logs: `adb logcat -s CapacitorConsole`

## Contributing

When adding new mobile functionality:
1. Add corresponding tests for the new feature
2. Test both build and fast modes: `python run_tests.py` and `python run_tests.py --fast`
3. Ensure tests work on different Android devices/emulators
4. Update test documentation if adding new test patterns

---

**Focus**: This testing framework validates the complete mobile GPS visualization experience - from raw GPS files to working offline Android app. 📱🗺️