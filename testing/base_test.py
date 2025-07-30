import time
import unittest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from appium.webdriver.common.touch_action import TouchAction
from config import TestConfig

class BaseTest(unittest.TestCase):
    driver = None
    wait = None
    
    @classmethod
    def setUpClass(cls):
        """Set up Appium driver once for all tests in the class"""
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.device_name = TestConfig.ANDROID_CAPABILITIES.get('appium:deviceName', 'Android Emulator')
        options.app = TestConfig.ANDROID_CAPABILITIES['appium:app']
        options.app_package = TestConfig.ANDROID_CAPABILITIES['appium:appPackage']
        options.app_activity = TestConfig.ANDROID_CAPABILITIES['appium:appActivity']
        options.auto_grant_permissions = TestConfig.ANDROID_CAPABILITIES['appium:autoGrantPermissions']
        options.chromedriver_autodownload = TestConfig.ANDROID_CAPABILITIES['appium:chromedriverAutodownload']
        options.chromedriver_executable = TestConfig.ANDROID_CAPABILITIES['appium:chromedriverExecutable']
        options.native_web_screenshot = TestConfig.ANDROID_CAPABILITIES['appium:nativeWebScreenshot']
        options.new_command_timeout = TestConfig.ANDROID_CAPABILITIES['appium:newCommandTimeout']
        options.auto_webview = TestConfig.ANDROID_CAPABILITIES['appium:autoWebview']
        
        cls.driver = webdriver.Remote(TestConfig.APPIUM_SERVER, options=options)
        cls.driver.implicitly_wait(TestConfig.IMPLICIT_WAIT)
        cls.wait = WebDriverWait(cls.driver, TestConfig.EXPLICIT_WAIT)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        if cls.driver:
            cls.driver.quit()
            
    def setUp(self):
        """Reset app state before each test"""
        # Note: reset() is deprecated in Appium 2.x
        # Instead, we'll terminate and relaunch the app if needed
        time.sleep(2)  # Give app time to initialize
        
    def switch_to_webview(self):
        """Switch to WebView context for hybrid app testing"""
        time.sleep(2)  # Wait for WebView to load
        contexts = self.driver.contexts
        print(f"Available contexts: {contexts}")
        
        for context in contexts:
            if 'WEBVIEW' in context:
                self.driver.switch_to.context(context)
                print(f"Switched to context: {context}")
                return True
        return False
        
    def switch_to_native(self):
        """Switch back to native context"""
        self.driver.switch_to.context('NATIVE_APP')
        
    def wait_for_map_load(self):
        """Wait for map to fully load"""
        self.switch_to_webview()
        # Wait for map container to be present (using CSS selector)
        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#map"))
        )
        time.sleep(TestConfig.MAP_LOAD_WAIT)
        
    def take_screenshot(self, name):
        """Take a screenshot for debugging"""
        TestConfig.SCREENSHOTS_PATH.mkdir(exist_ok=True)
        path = TestConfig.SCREENSHOTS_PATH / f"{name}.png"
        self.driver.save_screenshot(str(path))
        return path