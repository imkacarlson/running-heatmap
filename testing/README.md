# Mobile App Testing Framework

This directory contains the automated testing framework for the Running Heatmap mobile app using Appium and Python.

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

### 3. Build the APK

Before running tests, ensure the APK is built:
```bash
cd ../server
python build_mobile.py
```

This creates: `mobile/android/app/build/outputs/apk/debug/app-debug.apk`

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

### Quick Test Run

```bash
./test.sh
```

### Manual Test Run

```bash
# Activate virtual environment
source test_venv/bin/activate

# Run all tests
python run_tests.py

# Run specific test
python -m pytest test_basic_functionality.py::TestBasicFunctionality::test_app_launches_successfully -v
```

### Test Output

- Console output shows test progress
- Screenshots saved to `screenshots/` directory (auto-created)
- HTML report generated at `reports/test_report.html` (auto-created)

**Note**: The `screenshots/` and `reports/` directories are automatically created when tests run and are excluded from git.

## Test Structure

### Basic Functionality Tests (`test_basic_functionality.py`)

Tests existing app features:
- ✅ App launches successfully
- ✅ Map controls are present and visible
- ✅ Zoom functionality works
- ✅ Extras panel opens and closes

### Test Framework (`base_test.py`)

Provides common functionality:
- Appium WebDriver setup
- Context switching (Native ↔ WebView)
- Screenshot capture
- Map loading waits

## Writing New Tests

1. Inherit from `BaseTest`
2. Use `self.switch_to_webview()` to interact with map
3. Use `self.wait_for_map_load()` before map interactions
4. Take screenshots with `self.take_screenshot("description")`

Example:
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

### "No devices found"
- Start Android emulator or connect physical device
- Run `adb devices` to verify connection

### "App crashes on launch"
- Check if APK is built correctly
- Verify device has enough storage/memory
- Check Appium logs for detailed error

### "Cannot switch to WebView"
- App may still be loading
- Try increasing wait times in `base_test.py`
- Check if hybrid app WebView is enabled

### "Element not found"
- Take screenshot to see current app state
- Check if you're in correct context (Native vs WebView)
- Wait for elements to load before interacting

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