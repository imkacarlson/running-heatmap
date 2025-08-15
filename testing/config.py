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
    
    # Optimization settings
    class OptimizationConfig:
        # Cache settings
        ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        CACHE_TTL_HOURS = int(os.getenv('CACHE_TTL_HOURS', '24'))  # Cache validity in hours
        AUTO_CACHE_CLEANUP = os.getenv('AUTO_CACHE_CLEANUP', 'true').lower() == 'true'
        
        # Build optimization
        SKIP_APK_BUILD_ON_NO_CHANGES = True
        SKIP_DATA_PROCESSING_ON_NO_CHANGES = True
        FORCE_REBUILD_ON_CACHE_CORRUPTION = True
        
        # Parallel execution settings
        ENABLE_PARALLEL_EXECUTION = os.getenv('ENABLE_PARALLEL_EXECUTION', 'true').lower() == 'true'
        MAX_PARALLEL_WORKERS = int(os.getenv('MAX_PARALLEL_WORKERS', '4'))
        PARALLEL_TIMEOUT_MULTIPLIER = float(os.getenv('PARALLEL_TIMEOUT_MULTIPLIER', '1.5'))
        SEQUENTIAL_FALLBACK_ON_FAILURE = True
        
        # Service management timeouts
        EMULATOR_STARTUP_TIMEOUT = int(os.getenv('EMULATOR_STARTUP_TIMEOUT', '180'))  # seconds
        APPIUM_STARTUP_TIMEOUT = int(os.getenv('APPIUM_STARTUP_TIMEOUT', '30'))  # seconds
        SERVICE_HEALTH_CHECK_TIMEOUT = int(os.getenv('SERVICE_HEALTH_CHECK_TIMEOUT', '30'))  # seconds
        SERVICE_RESTART_DELAY = int(os.getenv('SERVICE_RESTART_DELAY', '10'))  # seconds
        MAX_SERVICE_RESTART_ATTEMPTS = int(os.getenv('MAX_SERVICE_RESTART_ATTEMPTS', '3'))
        
        # Performance monitoring
        ENABLE_PERFORMANCE_MONITORING = os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
        PERFORMANCE_REPORT_FORMAT = os.getenv('PERFORMANCE_REPORT_FORMAT', 'json')  # json, csv, both
        DETAILED_TIMING_METRICS = os.getenv('DETAILED_TIMING_METRICS', 'true').lower() == 'true'
        
        # Change detection settings
        CHANGE_DETECTION_ALGORITHM = os.getenv('CHANGE_DETECTION_ALGORITHM', 'mtime')  # mtime, checksum, both
        BASELINE_UPDATE_FREQUENCY = os.getenv('BASELINE_UPDATE_FREQUENCY', 'after_successful_build')
        FORCE_FULL_BUILD_INTERVAL_DAYS = int(os.getenv('FORCE_FULL_BUILD_INTERVAL_DAYS', '7'))
        
        # Cache directories
        CACHE_BASE_DIR = PROJECT_ROOT / "testing" / ".optimization_cache"
        APK_CACHE_DIR = PROJECT_ROOT / "testing" / "cached_test_apk"
        DATA_CACHE_DIR = PROJECT_ROOT / "testing" / "cached_test_data"
        CHANGE_DETECTOR_CACHE_DIR = PROJECT_ROOT / "testing" / ".change_detector_cache"
        SERVICE_STATE_CACHE_DIR = PROJECT_ROOT / "testing" / ".service_cache"
        
        # Persistent infrastructure settings
        PERSISTENT_INFRASTRUCTURE_ENABLED = os.getenv('PERSISTENT_INFRASTRUCTURE_ENABLED', 'false').lower() == 'true'
        AUTO_START_PERSISTENT_SERVICES = os.getenv('AUTO_START_PERSISTENT_SERVICES', 'false').lower() == 'true'
        PERSISTENT_SERVICE_AUTO_RESTART = os.getenv('PERSISTENT_SERVICE_AUTO_RESTART', 'true').lower() == 'true'
        
    # Legacy support - maintain backward compatibility
    OPTIMIZATION = OptimizationConfig()