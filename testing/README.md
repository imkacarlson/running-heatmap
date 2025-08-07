# Mobile App Testing Framework

This directory contains the **enhanced automated testing framework** for the Running Heatmap mobile app using Appium and Python.

## 🚀 **NEW: Single Command Test Runner** 

**Just run one command and the framework handles everything automatically:**

```bash
python run_tests.py --core --fast
```

**Key Features:**
- 🎯 **Single Command Testing**: Automatically starts emulator, Appium server, runs tests, generates report, and opens it in your browser
- 🔄 **End-to-End Testing**: GPX → PMTiles → APK → Mobile visualization  
- 🏗️ **Isolated Build Environment**: Never touches production data
- ⚡ **Session-Scoped Fixtures**: Expensive APK builds done once per test session
- 📊 **Feature Detection**: Automated map feature and rendering verification
- 🤖 **Automatic Infrastructure**: No manual Appium server or emulator management needed

---

## 📚 Table of Contents
- [🚀 Quick Start](#-complete-setup-guide-first-time-users) - Get running in 5 minutes
- [🎯 Running Tests](#-running-tests---enhanced-single-command-approach) - All command options
- [🔧 Troubleshooting](#-troubleshooting) - Solutions to common issues
- [📋 Test Structure](#test-structure) - Understanding the test suites
- [✍️ Writing Tests](#writing-new-tests) - Adding new test cases

---

## ⚡ **Most Important Commands**

```bash
# 🏆 COMPLETE AUTOMATION: Tests + automatic cleanup 
python run_tests.py --core --fast --auto-emulator

# 🚀 DEVELOPMENT: Fast iteration for UI changes  
python run_tests.py --core --fast

# 🏗️ FULL BUILD: Complete APK build + all tests (first time)
python run_tests.py --core

# 🔄 KEEP ENVIRONMENT: Don't shutdown emulator or uninstall app
python run_tests.py --core --fast --keep-emulator --keep-app

# 📖 HELP: See all available options
python run_tests.py --help
```

## Prerequisites

### 1. Android Development Environment

You need either:
- **Android Emulator**: Install Android Studio and create an AVD (Android Virtual Device)
- **Physical Android Device**: Enable USB debugging in Developer Options

### 2. Android SDK Tools

Make sure `adb` (Android Debug Bridge) is installed and available in your PATH:
```bash
adb version
```

If not available, install Android SDK platform-tools.

### 3. No Manual APK Building Required!

**✅ The new testing framework handles APK building automatically!**

Tests use session-scoped fixtures that:
- Create isolated test environments with test data only
- Build APKs with test data automatically 
- Never touch your production data
- Reuse expensive builds across multiple tests

## Setup

### 1. Install Dependencies

From the testing directory:

```bash
# Install Python dependencies
source test_venv/bin/activate
pip install -r requirements.txt

# Install Node dependencies (Appium)
npm install
```

### 2. Start Android Device/Emulator

**Option A: Android Emulator**
```bash
# List available AVDs  
emulator -list-avds

# Start an emulator with extended controls fix (for WSL/Windows)
emulator -avd TestDevice -no-audio -gpu swiftshader_indirect -skin 1080x1920 &

# Or use the setup script for guided setup
./setup_emulator.sh
```

**📱 Extended Controls Fix for WSL/Windows Users:**
If the Extended Controls panel (tall thin window) buttons don't respond to clicks:
1. **Recommended**: Launch emulator from Android Studio > Tools > AVD Manager (▶️ button)
2. **Alternative**: Use the command above with `-skin 1080x1920` parameter
3. This fixes WSLg compatibility issues with emulator controls (volume, rotation, location, etc.)

**Option B: Physical Device**
1. Enable Developer Options on your Android device
2. Enable USB Debugging
3. Connect via USB
4. Accept debugging prompt on device

### 3. Set Up ChromeDriver for WebView Testing

**Important**: WebView automation requires a ChromeDriver that matches your Android WebView version.

```bash
# Check your device's WebView version
adb shell dumpsys package com.android.webview | grep versionName

# Download matching ChromeDriver (example for version 101.0.4951.x)
VER=101.0.4951.41
curl -O https://chromedriver.storage.googleapis.com/$VER/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver vetted-drivers/chromedriver-101

# Update config.py to point to your ChromeDriver
# (The path should already be correct if using version 101)
```

### 4. Verify Device Connection

```bash
adb devices
```

Should show your device/emulator listed.

## 🎯 Running Tests - Enhanced Single Command Approach

### **Quick Start (Recommended)**

```bash
cd testing
source test_venv/bin/activate

# 🏆 BEST: Quick core tests (30 seconds)
python run_tests.py --core --fast

# 🚀 With automatic emulator startup
python run_tests.py --core --fast --auto-emulator
```

**That's it!** The enhanced runner handles everything automatically:
- ✅ Checks prerequisites 
- ✅ Starts emulator if needed (`--auto-emulator`)
- ✅ Starts Appium server with health checks
- ✅ Runs your chosen test suite
- ✅ Generates HTML report
- ✅ Opens report in browser
- ✅ **NEW**: Automatically cleans up and shuts down for fresh runs

### **All Available Commands**

```bash
# 🏆 RECOMMENDED: Core tests (essential functionality)
python run_tests.py --core --fast              # Quick core tests (30 seconds)
python run_tests.py --core                     # Full build + core tests (10+ minutes)

# 📱 Full mobile test suites
python run_tests.py --mobile --fast            # All mobile tests (skip builds)
python run_tests.py --mobile                   # Full mobile tests with APK build

# 🔧 Legacy and integration tests
python run_tests.py --legacy --fast            # Legacy tests only
python run_tests.py --integration --fast       # Integration tests only

# 🤖 Automatic infrastructure management
python run_tests.py --core --auto-emulator     # Auto-start emulator if needed
python run_tests.py --core --emulator-name MyTestDevice  # Use specific AVD

# 🧹 Cleanup control (default: automatic cleanup for fresh runs)
python run_tests.py --core --keep-emulator     # Keep emulator running after tests
python run_tests.py --core --keep-app          # Keep test app installed after tests
python run_tests.py --core --keep-emulator --keep-app  # Keep everything running

# 🎯 Specific test files
python run_tests.py test_upload_functionality.py --fast
python run_tests.py test_basic_lasso_selection.py --fast

# 🔍 Debugging and customization
python run_tests.py --core --verbose           # Detailed output
python run_tests.py --core --no-browser        # Don't auto-open report
python run_tests.py --help                     # See all options
```

### **Test Modes Explained**

| Mode | Time | Description | Use Case |
|------|------|-------------|----------|
| `--fast` | ~30 seconds | Skips APK builds, uses existing APK | Rapid UI testing, development |
| Full build | ~10+ minutes | Builds fresh APK with test data | First run, CI/CD, full validation |

### **Test Suite Options**

| Suite | Description | Tests Included |
|-------|-------------|----------------|
| `--core` ⭐ | Essential functionality (recommended) | Activity verification, upload, lasso, basic controls |
| `--mobile` | All mobile tests | Core + legacy + redundant tests |  
| `--legacy` | Legacy tests only | Old test framework compatibility |
| `--integration` | Integration tests | End-to-end workflows |

### **Legacy Manual Approach (Still Available)**

If you prefer the old two-terminal approach or need to debug Appium server issues:

**Terminal 1: Start Appium Server**
```bash
cd testing
source test_venv/bin/activate
npx appium --base-path /wd/hub
```

**Terminal 2: Run Tests**
```bash
cd testing  
source test_venv/bin/activate
python -m pytest -m core --fast
```

## 📋 Complete Setup Guide (First Time Users)

### **Option 1: Full Automatic Setup (Recommended)**

```bash
# 1. Navigate to testing directory
cd testing

# 2. Activate Python environment  
source test_venv/bin/activate

# 3. Install dependencies (first time only)
pip install -r requirements.txt
npm install

# 4. Create an Android Virtual Device (AVD) in Android Studio
# - Open Android Studio > Tools > AVD Manager
# - Create Virtual Device > Choose Pixel 4 > API 29+ > Name it "TestDevice"

# 5. Run tests with automatic everything!
python run_tests.py --core --fast --auto-emulator
```

### **Option 2: Manual Device Management**

```bash
# 1-3. Same as above

# 4. Start your device manually:
# Option A: Android Studio > Tools > AVD Manager > ▶️ button
# Option B: emulator -avd TestDevice -no-audio -gpu swiftshader_indirect -skin 1080x1920 &
# Option C: Connect physical device with USB debugging

# 5. Verify device connection
adb devices

# 6. Run tests
python run_tests.py --core --fast
```

### **Automatic Cleanup for Fresh Runs**

🧹 **The enhanced runner automatically cleans up after each test run:**

- **🔌 Emulator Management**: Auto-started emulators are shut down gracefully
- **📱 App Cleanup**: Test app is uninstalled for fresh installs next time  
- **📁 File Cleanup**: Test files are removed from device storage
- **🛑 Process Cleanup**: Appium server is terminated properly

**🎛️ Control cleanup behavior:**
```bash
# Default: Full automatic cleanup (recommended)
python run_tests.py --core --auto-emulator

# Keep emulator running for faster subsequent tests
python run_tests.py --core --keep-emulator

# Keep test app installed (faster app startup)  
python run_tests.py --core --keep-app

# Keep everything running (manual cleanup)
python run_tests.py --core --keep-emulator --keep-app
```

### **Test Output & Reports**

The enhanced runner automatically provides:
- 📊 **Comprehensive console summary** with test results and configuration
- 📋 **HTML report** at `reports/test_report.html` (auto-opened in browser)
- 🧹 **Fresh environment** ready for next test run

**Note**: The `reports/` directory is automatically created and excluded from git.

## Test Structure

### 🏆 Core Test Suite (Recommended)

**Streamlined essential tests with no redundancy:**

**`test_mobile_with_fixtures.py`** - Rock-solid activity verification:  
- ✅ `test_activity_definitely_visible` - **Rock-solid packaged activity verification** (pixel + viewport + feature detection)

**`test_upload_functionality.py`** - Upload functionality:
- ✅ `test_upload_gpx_file_flow` - Complete upload flow with coordinate-specific verification

**`test_basic_lasso_selection.py`** - Lasso selection:
- ✅ `test_basic_lasso_polygon_selection` - Lasso polygon selection with precision verification

**`test_basic_functionality.py`** - Core UI functionality:
- ✅ `test_map_controls_present` - Map controls presence and visibility
- ✅ `test_zoom_functionality` - Zoom controls functionality
- ✅ `test_extras_panel_opens` - Extras panel functionality

### Legacy Tests (Reference Only)

**Redundant tests marked for exclusion from default runs:**
- App launch tests (redundant - covered in rock-solid test)
- Duplicate activity visibility tests (use rock-solid test instead)
- Other legacy functionality tests

**Session-Scoped Fixtures (`conftest.py`)**:
- `isolated_test_environment` - Creates temporary test env with GPX data
- `test_apk_with_data` - Builds APK with test data (expensive, done once)
- `test_emulator_with_apk` - Installs test APK on emulator
- `mobile_driver` - Provides Appium driver for mobile tests

### Legacy Tests (Still Available)

**`test_basic_functionality.py`** - Basic app functionality:
- ✅ App launches successfully
- ✅ Map controls are present and visible  
- ✅ Zoom functionality works
- ✅ Extras panel opens and closes

**Test Framework (`base_test.py`)** - Common functionality:
- Appium WebDriver setup
- Context switching (Native ↔ WebView)
- Map loading waits

## Writing New Tests

### Option 1: Use New Fixture-Based Approach (Recommended)

Create tests that use session-scoped fixtures for automatic APK building:

```python
import time
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class TestMyNewFeature:
    def test_my_feature_with_test_data(self, mobile_driver):
        """Test using automatically built APK with test data"""
        driver = mobile_driver['driver']
        wait = mobile_driver['wait']
        
        # App already launched with test data
        time.sleep(8)
        
        # Switch to WebView context
        contexts = driver.contexts
        for context in contexts:
            if 'WEBVIEW' in context:
                driver.switch_to.context(context)
                break
        
        # Wait for map and test your feature
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#map")))
        
        # Your test logic here
        button = driver.find_element(By.CSS_SELECTOR, "#my-button")
        button.click()
        # Assert expected behavior
```

### Option 2: Use Legacy BaseTest Approach

```python
from base_test import BaseTest
from selenium.webdriver.common.by import By

class TestNewFeature(BaseTest):
    def test_my_feature(self):
        self.switch_to_webview()
        self.wait_for_map_load()
        
        # Your test logic here
        button = self.driver.find_element(By.ID, "my-button")
        button.click()
        # Assert expected behavior
```

## 🔧 Troubleshooting

### **Enhanced Runner Issues**

#### "No Android devices/emulators connected"
The enhanced runner provides helpful guidance when no devices are found:
```bash
# ✅ SOLUTION 1: Use auto-emulator flag
python run_tests.py --core --fast --auto-emulator

# ✅ SOLUTION 2: Start emulator manually first
emulator -avd TestDevice -no-audio -gpu swiftshader_indirect -skin 1080x1920 &
# Then run tests
python run_tests.py --core --fast

# ✅ SOLUTION 3: Use guided setup script
./setup_emulator.sh
```

#### "APK not found for --fast mode"
```bash
# ✅ SOLUTION: Run full build first (creates APK)
python run_tests.py --core

# Then fast mode will work
python run_tests.py --core --fast
```

#### "AVD 'TestDevice' not found"
```bash
# ✅ SOLUTION 1: Create TestDevice AVD in Android Studio
# Android Studio > Tools > AVD Manager > Create Virtual Device

# ✅ SOLUTION 2: Use existing AVD name
python run_tests.py --core --auto-emulator --emulator-name YourExistingAVD
```

#### "Appium server failed to start"
```bash
# ✅ SOLUTION 1: Install Node dependencies
npm install

# ✅ SOLUTION 2: Check Node.js is installed
node --version  # Should be 14+

# ✅ SOLUTION 3: Use verbose mode for details
python run_tests.py --core --verbose
```

### **Common Device Issues**

#### "Extended Controls buttons not responding" (WSL/Windows)
- **✅ Best solution**: Launch emulator from Android Studio > Tools > AVD Manager (▶️ button)
- **Alternative**: The enhanced runner uses `-skin 1080x1920` automatically for WSL compatibility
- **Root cause**: WSLg compatibility issue with emulator UI controls

#### "Emulator failed to start within timeout"
```bash
# ✅ Check available AVDs
emulator -list-avds

# ✅ Start manually to see errors
emulator -avd TestDevice -verbose

# ✅ Try different AVD or recreate in Android Studio
```

### **Legacy Manual Mode Issues**

#### "Connection refused" / "Appium server not found" 
- **Solution**: The enhanced runner handles this automatically, or start Appium manually: `npx appium --base-path /wd/hub`

#### "No route found for /wd/hub/session" (404 error)
- **Solution**: Use enhanced runner (includes correct base path) or restart Appium with: `npx appium --base-path /wd/hub`

### **App & Test Issues**

#### "App crashes on launch"
- Check device has enough storage/memory
- Try different emulator or device
- Use `--verbose` flag to see detailed logs

#### "Cannot switch to WebView"
- App may still be loading - wait longer  
- Check available contexts in verbose output
- Ensure WebView is enabled in hybrid app

#### "Element not found" / "PMTiles not visible"
- Use the HTML report to analyze test failure details
- Try different zoom levels (zoom 13 works well)
- Ensure test data covers Frederick, MD area
- Verify you're in correct context (Native vs WebView)

### **Getting Help**

```bash
# 📖 See all available options
python run_tests.py --help

# 🔍 Run with detailed output
python run_tests.py --core --verbose

# 📋 Check HTML report for detailed test results
# (automatically opens in browser, or manually open reports/test_report.html)
```

## Advanced Usage

### Custom Device Configuration

Edit `config.py` to modify device capabilities:
```python
ANDROID_CAPABILITIES = {
    'platformName': 'Android',
    'deviceName': 'Your Device Name',
    'udid': 'your-device-udid',  # For specific device
    # ... other capabilities
}
```

### Running Tests in CI/CD

The framework is designed to work in CI environments. See `.github/workflows/android-tests.yml` for GitHub Actions setup.

### Performance Testing

Tests can measure app performance:
```python
def test_map_load_performance(self):
    start_time = time.time()
    self.wait_for_map_load()
    load_time = time.time() - start_time
    self.assertLess(load_time, 5, "Map took too long to load")
```