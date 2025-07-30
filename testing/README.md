# Mobile App Testing Framework

This directory contains the automated testing framework for the Running Heatmap mobile app using Appium and Python.

**Key Features:**
- 🔄 **End-to-End Testing**: GPX → PMTiles → APK → Mobile visualization
- 🏗️ **Isolated Build Environment**: Never touches production data
- ⚡ **Session-Scoped Fixtures**: Expensive APK builds done once per test session
- 📸 **Visual Verification**: Screenshot capture and automated feature detection

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

# Start an emulator (replace with your AVD name)
emulator -avd Pixel_4_API_30 &
```

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

## Running Tests

### The Two-Terminal Approach

**Terminal 1: Start Appium Server**
```bash
cd testing
source test_venv/bin/activate
npx appium --base-path /wd/hub
```
Keep this running - you'll see Appium server logs here.

**Important:** The `--base-path /wd/hub` flag is required! Without it, you'll get "No route found" errors because the tests expect the server at `http://localhost:4723/wd/hub/session`.

**Terminal 2: Run Tests**
```bash
cd testing  
source test_venv/bin/activate

# Run the complete end-to-end test suite
python -m pytest test_mobile_with_fixtures.py -v -s

# Run specific test
python -m pytest test_mobile_with_fixtures.py::TestMobileAppWithTestData::test_test_activity_visualization -v -s

# Run all mobile tests
python -m pytest test_mobile_with_fixtures.py test_end_to_end_gpx_mobile.py -v -s
```

### Legacy Test Run (Old Framework)

```bash
# Run old basic functionality tests (still works)
python -m pytest test_basic_functionality.py -v -s
```

### Test Output

- Console output shows test progress
- Screenshots saved to `screenshots/` directory (auto-created)
- HTML report generated at `reports/test_report.html` (auto-created)

**Note**: The `screenshots/` and `reports/` directories are automatically created when tests run and are excluded from git.

## Test Structure

### New Fixture-Based Tests (Recommended)

**`test_mobile_with_fixtures.py`** - Uses session-scoped fixtures:
- ✅ App launches with isolated test data
- ✅ Test activity visualization on map
- ✅ Automatic APK building with test data only
- ✅ Screenshots and visual verification

**`test_end_to_end_gpx_mobile.py`** - End-to-end pipeline tests:
- ✅ Data pipeline validation (GPX → runs.pkl → PMTiles)
- ✅ APK build validation
- ✅ Complete integration testing

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
- Screenshot capture
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
        screenshots_dir = Path(__file__).parent / "screenshots"
        
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
        
        driver.save_screenshot(str(screenshots_dir / "my_feature_test.png"))
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
        
        self.take_screenshot("after_click")
        # Assert expected behavior
```

## Troubleshooting

### "Connection refused" / "Appium server not found"
- **Solution**: Start Appium server first in Terminal 1: `npx appium --base-path /wd/hub`
- Make sure Appium server is running on `http://localhost:4723`

### "No route found for /wd/hub/session" (404 error)
- **Solution**: You started Appium without the base path flag
- Restart Appium with: `npx appium --base-path /wd/hub`
- Tests require the `/wd/hub` path to work correctly

### "No devices found" 
- Start Android emulator or connect physical device
- Run `adb devices` to verify connection
- For emulator: `emulator -avd YourAVDName &`

### "APK build failed" (Session-scoped fixtures)
- Check that main project `.venv` has required packages (shapely, etc.)
- Verify Android SDK and Node.js are properly installed
- Check build output in test logs for specific error

### "App crashes on launch"
- Verify device has enough storage/memory
- Check Appium logs in Terminal 1 for detailed error
- Try with a fresh emulator or different device

### "Cannot switch to WebView" 
- App may still be loading - wait longer
- Check available contexts: `driver.contexts`
- Ensure hybrid app WebView is enabled

### "Element not found"
- Take screenshot to see current app state
- Check if you're in correct context (Native vs WebView)
- Wait for elements to load before interacting

### "PMTiles not visible" / "Features not found"
- Try different zoom levels (zoom 13 works well, zoom 16+ may be too detailed)
- Check screenshots to verify map is loaded
- Ensure test data is in the expected location (Frederick, MD area)

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