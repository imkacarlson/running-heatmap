# Vetted ChromeDriver Directory

This directory contains manually verified ChromeDriver binaries for WebView automation.

## Setup Instructions

To set up ChromeDriver for your Android WebView version:

1. **Check your WebView version:**
   ```bash
   adb shell dumpsys package com.android.webview | grep versionName
   ```

2. **Download matching ChromeDriver:**
   ```bash
   VER=101.0.4951.41  # Replace with your version
   curl -O https://chromedriver.storage.googleapis.com/$VER/chromedriver_linux64.zip
   unzip chromedriver_linux64.zip
   chmod +x chromedriver
   mv chromedriver vetted-drivers/chromedriver-101  # Rename appropriately
   ```

3. **Update config.py:**
   The `config.py` file should point to your ChromeDriver:
   ```python
   'appium:chromedriverExecutable': str(PROJECT_ROOT / "testing/vetted-drivers/chromedriver-101")
   ```

## Current Setup

- **WebView Version**: 101.0.4951.61
- **ChromeDriver**: chromedriver-101 (version 101.0.4951.41)
- **Compatibility**: ✅ Working

## Security Note

ChromeDriver binaries are manually downloaded and verified rather than using auto-download for better security and deterministic builds.