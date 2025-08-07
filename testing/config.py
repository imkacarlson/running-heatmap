import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class TestConfig:
    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    APK_PATH = PROJECT_ROOT / "mobile/android/app/build/outputs/apk/debug/app-debug.apk"
    TEST_DATA_PATH = PROJECT_ROOT / "testing/test_data"
    
    # Appium settings
    APPIUM_SERVER = os.getenv('APPIUM_SERVER', 'http://localhost:4723/wd/hub')
    
    # Device capabilities using Appium 2.x format
    ANDROID_CAPABILITIES = {
        'platformName': 'Android',
        'appium:automationName': 'UiAutomator2',
        'appium:deviceName': os.getenv('DEVICE_NAME', 'Android Emulator'),
        'appium:app': str(APK_PATH),
        'appium:appPackage': 'com.run.heatmap',
        'appium:appActivity': 'com.run.heatmap.MainActivity',
        'appium:autoGrantPermissions': True,
        'appium:chromedriverAutodownload': False,
        'appium:chromedriverExecutable': str(PROJECT_ROOT / "testing/vetted-drivers/chromedriver-101"),
        'appium:nativeWebScreenshot': True,
        'appium:newCommandTimeout': 300,
        # Important for hybrid apps
        'appium:autoWebview': False,  # We'll switch contexts manually
        'appium:webviewDevtoolsPort': 9222,
    }
    
    # Test settings
    IMPLICIT_WAIT = 10
    EXPLICIT_WAIT = 30
    MAP_LOAD_WAIT = 5
    
    # Test data
    SAMPLE_GPX_PATH = TEST_DATA_PATH / "sample_run.gpx"
    TEST_COORDINATES = {
        'frederick_md': [-77.4144, 39.4143],  # Your location
        'test_run_center': [-77.4244, 39.4243]
    }