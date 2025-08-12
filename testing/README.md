# Mobile App Testing Framework

This directory contains the **enhanced automated testing framework** for the Running Heatmap mobile app using a **dual-tier testing strategy** with both lightweight smoke tests and comprehensive emulator tests.

## 🚀 **NEW: Dual-Tier Testing Strategy**

**Two complementary testing approaches for different development needs:**

### ⚡ **Tier 1: Smoke Tests (< 5 seconds)**
```bash
python smoke_tests.py                    # All smoke tests
python run_tests.py --smoke              # Integrated smoke tests
```

### 🔄 **Tier 2: Comprehensive Tests (30s - 10+ minutes)**
```bash
python run_tests.py --core --fast        # Quick comprehensive tests
```

**Key Features:**
- ⚡ **Lightning Fast Feedback**: Smoke tests validate core functionality in under 5 seconds
- 🎯 **Single Command Testing**: Automatically starts emulator, Appium server, runs tests, generates report, and opens it in your browser
- 🔄 **End-to-End Testing**: GPX → PMTiles → APK → Mobile visualization  
- 🏗️ **Isolated Build Environment**: Never touches production data
- ⚡ **Session-Scoped Fixtures**: Expensive APK builds done once per test session
- 📊 **Feature Detection**: Automated map feature and rendering verification
- 🤖 **Automatic Infrastructure**: No manual Appium server or emulator management needed

---

## 📚 Table of Contents
- [⚡ Dual-Tier Testing Strategy](#-dual-tier-testing-strategy-explained) - When to use smoke vs comprehensive tests
- [🚀 Quick Start](#-complete-setup-guide-first-time-users) - Get running in 5 minutes
- [🎯 Running Tests](#-running-tests---enhanced-single-command-approach) - All command options
- [🔧 Troubleshooting](#-troubleshooting) - Solutions to common issues
- [📋 Test Structure](#test-structure) - Understanding the test suites
- [✍️ Writing Tests](#writing-new-tests) - Adding new test cases

---

## ⚡ **Dual-Tier Testing Strategy Explained**

### **When to Use Each Testing Tier**

| Scenario | Recommended Approach | Command | Time |
|----------|---------------------|---------|------|
| 🔄 **Active Development** | Smoke tests for immediate feedback | `python smoke_tests.py` | < 5s |
| 🐛 **Bug Fixes** | Smoke tests first, then targeted comprehensive | `python smoke_tests.py` → `python run_tests.py --core --fast` | 5s + 30s |
| 🚀 **Pre-commit** | Smoke tests for quick validation | `python smoke_tests.py` | < 5s |
| 📦 **Pre-release** | Full comprehensive test suite | `python run_tests.py --core` | 10+ min |
| 🔧 **CI/CD Pipeline** | Smoke tests → Comprehensive tests | Both tiers | 5s + 10+ min |
| 🎯 **Feature Development** | Smoke tests during development, comprehensive for validation | `python smoke_tests.py` → `python run_tests.py --core --fast` | 5s + 30s |

### **Decision Matrix: Smoke vs Comprehensive Tests**

```
┌─────────────────────────────────────────────────────────────┐
│                    DECISION MATRIX                          │
├─────────────────────────────────────────────────────────────┤
│  SMOKE TESTS (< 5 seconds)                                 │
│  ✅ Server starts and responds                             │
│  ✅ API endpoints return expected data                     │
│  ✅ Mobile web interface loads without errors              │
│  ✅ Core data pipeline processes sample data               │
│  ✅ Build artifacts are generated correctly                │
│                                                             │
│  USE WHEN:                                                  │
│  • Making frequent code changes                            │
│  • Need immediate feedback                                  │
│  • Validating basic functionality                          │
│  • Running in pre-commit hooks                             │
│  • First-level CI/CD validation                            │
├─────────────────────────────────────────────────────────────┤
│  COMPREHENSIVE TESTS (30s - 10+ minutes)                   │
│  ✅ Full mobile app installation and testing               │
│  ✅ End-to-end user workflows                              │
│  ✅ UI interaction validation                              │
│  ✅ Cross-device compatibility                             │
│  ✅ Performance and memory testing                         │
│                                                             │
│  USE WHEN:                                                  │
│  • Preparing for release                                   │
│  • Validating complex features                             │
│  • Testing UI/UX changes                                   │
│  • Final CI/CD validation                                  │
│  • Debugging mobile-specific issues                        │
└─────────────────────────────────────────────────────────────┘
```

### **Smoke Test Examples**

#### **Quick Development Workflow**
```bash
# 1. Make code changes
# 2. Run smoke tests for immediate feedback
python smoke_tests.py

# 3. If smoke tests pass, continue development
# 4. If smoke tests fail, fix issues immediately
```

#### **Pre-commit Validation**
```bash
# Before committing changes
python smoke_tests.py
# Only commit if smoke tests pass
```

#### **Granular Smoke Testing**
```bash
# Test specific components
python run_tests.py --smoke --server     # Server startup only
python run_tests.py --smoke --api        # API endpoints only  
python run_tests.py --smoke --web        # Web interface only
python run_tests.py --smoke --mobile     # Mobile build validation
```

#### **Development + Validation Workflow**
```bash
# 1. Development phase - use smoke tests
python smoke_tests.py

# 2. Feature complete - validate with comprehensive tests
python run_tests.py --core --fast

# 3. Pre-release - full validation
python run_tests.py --core
```

### **Smoke Test Troubleshooting Guide**

#### **Server Startup Failures**
```bash
# Error: "Server failed to start within timeout"
# Solutions:
1. Check if port 5000 is already in use: netstat -an | grep 5000
2. Verify Python dependencies: pip install -r requirements.txt
3. Check for missing data files: ls -la data/
4. Run with verbose output: python smoke_tests.py --verbose
```

#### **API Response Failures**
```bash
# Error: "API endpoint returned unexpected response"
# Solutions:
1. Verify server is running: curl http://localhost:5000/
2. Check API endpoint directly: curl http://localhost:5000/api/last_activity
3. Validate test data exists: ls -la testing/test_data/
4. Check server logs for errors
```

#### **Web Interface Failures**
```bash
# Error: "JavaScript errors detected in mobile web interface"
# Solutions:
1. Check browser console for specific errors
2. Verify external libraries load: Check MapLibre, PMTiles availability
3. Test in different browser: Chrome vs Firefox
4. Validate mobile viewport rendering
```

#### **Mobile Build Failures**
```bash
# Error: "Mobile build artifacts missing or invalid"
# Solutions:
1. Run full build: python server/build_mobile.py
2. Check build dependencies: npm install (in server directory)
3. Verify PMTiles generation: ls -la server/*.pmtiles
4. Validate mobile template files exist
```

---

## ⚡ **Most Important Commands**

### **Smoke Tests (< 5 seconds) - Use During Development**
```bash
# ⚡ FASTEST: All smoke tests
python smoke_tests.py

# 🎯 GRANULAR: Specific component smoke tests
python run_tests.py --smoke --server     # Server startup only
python run_tests.py --smoke --api        # API endpoints only
python run_tests.py --smoke --web        # Web interface only
python run_tests.py --smoke --mobile     # Mobile build validation

# 🔍 DEBUGGING: Verbose smoke test output
python smoke_tests.py --verbose
```

### **Comprehensive Tests - Use for Validation**
```bash
# 🏆 COMPLETE AUTOMATION: Tests + automatic cleanup 
python run_tests.py --core --fast --auto-emulator

# 🚀 DEVELOPMENT: Fast iteration for UI changes  
python run_tests.py --core --fast

# 🧪 MANUAL TESTING: Interactive testing session
python manual_test.py --fast

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

## 🧪 **NEW: Manual Testing Mode**

**Interactive testing with automatic setup and cleanup!**

```bash
# 🎯 Start manual testing session
python manual_test.py --fast

# 🚀 With automatic emulator startup  
python manual_test.py --fast --auto-emulator

# 🔄 Keep environment running when done
python manual_test.py --fast --keep-emulator --keep-app
```

**What it does:**
1. **🚀 Sets up everything**: Emulator, APK installation, test data, Appium server
2. **📱 Launches the app**: Ready for you to test manually
3. **⏳ Waits for you**: Test at your own pace, no time limits
4. **🧹 Cleans up**: When you press Enter/Ctrl+C, automatically does all cleanup

**Perfect for:**
- 🎨 UI/UX testing and design validation  
- 🐛 Bug reproduction and debugging
- 🔍 Exploratory testing of new features
- 📊 Performance and usability testing
- 🎮 Interactive feature demonstrations

The manual testing script uses the same robust infrastructure as `run_tests.py` but gives you complete control over the testing session.

### **All Available Commands**

#### **Smoke Tests (Tier 1)**
```bash
# ⚡ All smoke tests (< 5 seconds)
python smoke_tests.py                          # Standalone smoke test runner
python run_tests.py --smoke                    # Integrated smoke tests

# 🎯 Granular smoke tests
python run_tests.py --smoke --server           # Server startup validation
python run_tests.py --smoke --api              # API endpoint validation
python run_tests.py --smoke --web              # Web interface validation
python run_tests.py --smoke --mobile           # Mobile build validation

# 🔍 Smoke test debugging
python smoke_tests.py --verbose                # Detailed smoke test output
python smoke_tests.py --help                   # Smoke test options
```

#### **Comprehensive Tests (Tier 2)**
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

## 🔄 **Developer Workflow Integration**

### **Recommended Development Workflows**

#### **Daily Development Workflow**
```bash
# 1. Start development session
git checkout -b feature/my-new-feature

# 2. Make code changes
# ... edit files ...

# 3. Quick validation with smoke tests (< 5 seconds)
python smoke_tests.py

# 4. Continue development if smoke tests pass
# 5. Repeat steps 2-4 as needed

# 6. Before committing - run smoke tests again
python smoke_tests.py

# 7. Commit changes if smoke tests pass
git add .
git commit -m "Add new feature"

# 8. Before pushing - validate with comprehensive tests
python run_tests.py --core --fast

# 9. Push if comprehensive tests pass
git push origin feature/my-new-feature
```

#### **Feature Development Workflow**
```bash
# Phase 1: Rapid Development (use smoke tests)
while developing:
    # Make changes
    python smoke_tests.py  # < 5 seconds feedback
    # Fix issues immediately if smoke tests fail

# Phase 2: Feature Validation (use comprehensive tests)  
python run_tests.py --core --fast  # 30 seconds validation

# Phase 3: Pre-release Validation (full test suite)
python run_tests.py --core  # 10+ minutes thorough testing
```

#### **Bug Fix Workflow**
```bash
# 1. Reproduce issue
python manual_test.py --fast  # Interactive testing

# 2. Identify root cause
python smoke_tests.py --verbose  # Quick component validation

# 3. Fix issue
# ... make changes ...

# 4. Validate fix
python smoke_tests.py  # Quick validation
python run_tests.py --core --fast  # Comprehensive validation

# 5. Commit fix
git commit -m "Fix: issue description"
```

### **Pre-commit Hook Integration**

#### **Option 1: Simple Pre-commit Hook (Recommended)**

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Simple pre-commit hook using smoke tests

echo "Running smoke tests before commit..."
cd testing
python smoke_tests.py

if [ $? -ne 0 ]; then
    echo "❌ Smoke tests failed! Commit aborted."
    echo "Fix the issues and try again."
    exit 1
fi

echo "✅ Smoke tests passed! Proceeding with commit."
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

#### **Option 2: Advanced Pre-commit Hook with Granular Testing**

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Advanced pre-commit hook with component-specific testing

echo "🔍 Analyzing changed files..."
cd testing

# Check which components were modified
CHANGED_FILES=$(git diff --cached --name-only)
SERVER_CHANGED=$(echo "$CHANGED_FILES" | grep -E "(server/|app\.py)" | wc -l)
WEB_CHANGED=$(echo "$CHANGED_FILES" | grep -E "(web/|\.html|\.js)" | wc -l)
API_CHANGED=$(echo "$CHANGED_FILES" | grep -E "(api|routes)" | wc -l)

# Run targeted smoke tests based on changes
if [ $SERVER_CHANGED -gt 0 ]; then
    echo "🖥️  Server changes detected - running server smoke tests..."
    python run_tests.py --smoke --server
    [ $? -ne 0 ] && echo "❌ Server smoke tests failed!" && exit 1
fi

if [ $API_CHANGED -gt 0 ]; then
    echo "🔌 API changes detected - running API smoke tests..."
    python run_tests.py --smoke --api
    [ $? -ne 0 ] && echo "❌ API smoke tests failed!" && exit 1
fi

if [ $WEB_CHANGED -gt 0 ]; then
    echo "🌐 Web changes detected - running web smoke tests..."
    python run_tests.py --smoke --web
    [ $? -ne 0 ] && echo "❌ Web smoke tests failed!" && exit 1
fi

# Always run full smoke tests as final check
echo "⚡ Running full smoke test suite..."
python smoke_tests.py

if [ $? -ne 0 ]; then
    echo "❌ Smoke tests failed! Commit aborted."
    echo "Run 'python smoke_tests.py --verbose' for detailed error information."
    exit 1
fi

echo "✅ All smoke tests passed! Proceeding with commit."
exit 0
```

#### **Option 3: Using pre-commit Framework**

Install pre-commit:
```bash
pip install pre-commit
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: smoke-tests
        name: Run smoke tests
        entry: python testing/smoke_tests.py
        language: system
        pass_filenames: false
        always_run: true
        stages: [commit]
```

Install the hook:
```bash
pre-commit install
```

### **CI/CD Integration Patterns**

#### **GitHub Actions Integration**

Create `.github/workflows/testing.yml`:
```yaml
name: Testing Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  smoke-tests:
    runs-on: ubuntu-latest
    name: Smoke Tests (< 5s)
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd testing
        pip install -r requirements.txt
    
    - name: Run smoke tests
      run: |
        cd testing
        python smoke_tests.py --verbose
    
    - name: Upload smoke test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: smoke-test-results
        path: testing/reports/

  comprehensive-tests:
    runs-on: ubuntu-latest
    needs: smoke-tests
    name: Comprehensive Tests (30s+)
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Set up Android SDK
      uses: android-actions/setup-android@v2
    
    - name: Install dependencies
      run: |
        cd testing
        pip install -r requirements.txt
        npm install
    
    - name: Run comprehensive tests
      run: |
        cd testing
        python run_tests.py --core --fast --auto-emulator
    
    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: comprehensive-test-results
        path: testing/reports/
```

#### **GitLab CI Integration**

Create `.gitlab-ci.yml`:
```yaml
stages:
  - smoke-tests
  - comprehensive-tests

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip/
    - testing/node_modules/

smoke-tests:
  stage: smoke-tests
  image: python:3.9
  script:
    - cd testing
    - pip install -r requirements.txt
    - python smoke_tests.py --verbose
  artifacts:
    when: always
    reports:
      junit: testing/reports/smoke-test-results.xml
    paths:
      - testing/reports/
  only:
    - merge_requests
    - main
    - develop

comprehensive-tests:
  stage: comprehensive-tests
  image: python:3.9
  needs: ["smoke-tests"]
  before_script:
    - apt-get update -qq && apt-get install -y -qq git curl unzip
    # Install Android SDK (simplified for CI)
    - export ANDROID_HOME=/opt/android-sdk
    - mkdir -p $ANDROID_HOME
  script:
    - cd testing
    - pip install -r requirements.txt
    - npm install
    - python run_tests.py --core --fast
  artifacts:
    when: always
    reports:
      junit: testing/reports/test-results.xml
    paths:
      - testing/reports/
  only:
    - main
    - develop
```

#### **Jenkins Pipeline Integration**

Create `Jenkinsfile`:
```groovy
pipeline {
    agent any
    
    stages {
        stage('Smoke Tests') {
            steps {
                dir('testing') {
                    sh 'pip install -r requirements.txt'
                    sh 'python smoke_tests.py --verbose'
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'testing/reports/**', allowEmptyArchive: true
                }
            }
        }
        
        stage('Comprehensive Tests') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                dir('testing') {
                    sh 'npm install'
                    sh 'python run_tests.py --core --fast --auto-emulator'
                }
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'testing/reports',
                        reportFiles: 'test_report.html',
                        reportName: 'Test Report'
                    ])
                }
            }
        }
    }
}
```

### **IDE Integration Examples**

#### **VS Code Integration**

Create `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Smoke Tests",
            "type": "shell",
            "command": "python",
            "args": ["smoke_tests.py"],
            "options": {
                "cwd": "${workspaceFolder}/testing"
            },
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "problemMatcher": []
        },
        {
            "label": "Run Comprehensive Tests",
            "type": "shell",
            "command": "python",
            "args": ["run_tests.py", "--core", "--fast"],
            "options": {
                "cwd": "${workspaceFolder}/testing"
            },
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "problemMatcher": []
        }
    ]
}
```

Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Smoke Tests",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/testing/smoke_tests.py",
            "args": ["--verbose"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}/testing"
        }
    ]
}
```

#### **PyCharm Integration**

1. **Run Configuration for Smoke Tests**:
   - Go to Run → Edit Configurations
   - Add new Python configuration
   - Script path: `testing/smoke_tests.py`
   - Parameters: `--verbose`
   - Working directory: `testing/`

2. **External Tool for Quick Testing**:
   - Go to File → Settings → Tools → External Tools
   - Add new tool:
     - Name: "Quick Smoke Tests"
     - Program: `python`
     - Arguments: `smoke_tests.py`
     - Working directory: `$ProjectFileDir$/testing`

### **Team Development Guidelines**

#### **Code Review Checklist**
- [ ] Smoke tests pass locally before creating PR
- [ ] PR includes relevant test updates if needed
- [ ] CI/CD pipeline shows green smoke tests
- [ ] Comprehensive tests pass for main/develop branches

#### **Release Process Integration**
```bash
# 1. Feature freeze - run full test suite
python run_tests.py --core

# 2. Release candidate - validate with smoke tests
python smoke_tests.py

# 3. Production deployment - final smoke test validation
python smoke_tests.py --verbose
```

#### **Debugging Workflow**
```bash
# 1. Issue reported - quick component validation
python run_tests.py --smoke --server --api --web --mobile

# 2. Identify failing component - detailed investigation
python smoke_tests.py --verbose

# 3. Fix and validate
python smoke_tests.py

# 4. Comprehensive validation before deployment
python run_tests.py --core --fast
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

The framework is designed to work in CI environments with the dual-tier approach:

1. **Smoke Tests**: Run on every commit/PR for immediate feedback
2. **Comprehensive Tests**: Run on main branches and releases

See the CI/CD integration examples above for specific platform configurations.

### Performance Testing

Tests can measure app performance:
```python
def test_map_load_performance(self):
    start_time = time.time()
    self.wait_for_map_load()
    load_time = time.time() - start_time
    self.assertLess(load_time, 5, "Map took too long to load")
```