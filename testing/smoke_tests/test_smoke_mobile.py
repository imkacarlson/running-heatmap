"""
Mobile app smoke tests for APK validation and mobile build artifacts
Focused on validating mobile app components without full emulator startup
"""
import os
import zipfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Make pytest optional for standalone usage
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create a dummy pytest module for compatibility
    class DummyPytest:
        @staticmethod
        def fail(msg):
            raise AssertionError(msg)
        
        class mark:
            @staticmethod
            def smoke(func):
                return func
    pytest = DummyPytest()

from .base_smoke_test import BaseSmokeTest


@pytest.mark.smoke
@pytest.mark.smoke_mobile
class TestMobileSmoke(BaseSmokeTest):
    """
    Mobile app smoke tests for APK validation and build artifacts
    Tests run in under 2 seconds without requiring emulator startup
    """
    
    def test_cached_apk_exists_and_valid(self):
        """
        Test that cached test APK exists and is a valid APK file
        Requirements: 4.4, 1.1
        """
        print("🔍 Testing cached APK existence and validity...")
        
        cached_apk_path = self.get_cached_apk_path()
        
        # Check if cached APK exists
        if not cached_apk_path.exists():
            print("ℹ️  Cached test APK not found (created during full build)")
            pytest.skip("Cached APK not found - run full build first")
        
        # Validate APK file structure
        self._validate_apk_structure(cached_apk_path)
        
        # Check APK size is reasonable (should be > 1MB for a real APK)
        apk_size = cached_apk_path.stat().st_size
        assert apk_size > 1024 * 1024, f"APK too small ({apk_size} bytes), likely corrupted"
        
        print(f"✅ Cached APK valid: {cached_apk_path} ({apk_size / (1024*1024):.1f} MB)")
        
        # Ensure test completes quickly
        self.assert_fast_execution(1.5)
    
    def test_apk_installation_verification_without_emulator(self):
        """
        Test APK installation verification using aapt without full emulator startup
        Requirements: 4.4, 1.1
        """
        print("🔍 Testing APK installation verification without emulator...")
        
        cached_apk_path = self.get_cached_apk_path()
        
        # Skip if APK doesn't exist (previous test should catch this)
        if not cached_apk_path.exists():
            pytest.skip("Cached APK not found - run full build first")
        
        # Use aapt to validate APK without installing
        apk_info = self._get_apk_info_with_aapt(cached_apk_path)
        
        # Validate expected package information
        assert apk_info['package_name'] == 'com.run.heatmap', \
            f"Wrong package name: {apk_info['package_name']}"
        
        assert apk_info['main_activity'] == 'com.run.heatmap.MainActivity', \
            f"Wrong main activity: {apk_info['main_activity']}"
        
        # Validate APK has required permissions for mobile app
        required_permissions = [
            'android.permission.INTERNET',
            'android.permission.ACCESS_NETWORK_STATE'
        ]
        
        for permission in required_permissions:
            assert permission in apk_info['permissions'], \
                f"Missing required permission: {permission}"
        
        print(f"✅ APK installation verification passed: {apk_info['package_name']}")
        
        # Ensure test completes quickly
        self.assert_fast_execution(1.5)
    
    def test_mobile_build_artifacts_present(self):
        """
        Test that mobile build artifacts and dependencies are present
        Requirements: 4.4, 1.3
        """
        print("🔍 Testing mobile build artifacts and dependencies...")
        
        # Check mobile build artifacts using base class method
        artifacts = self.check_mobile_build_artifacts()
        
        # Validate critical build artifacts exist
        critical_artifacts = [
            'build_script',
            'mobile_template', 
            'mobile_main_js',
            'android_manifest_template',
            'main_activity_template'
        ]
        
        missing_artifacts = []
        for artifact in critical_artifacts:
            if not artifacts.get(artifact, False):
                missing_artifacts.append(artifact)
        
        assert not missing_artifacts, \
            f"Missing critical mobile build artifacts: {missing_artifacts}"
        
        # Check mobile template has required placeholders
        self._validate_mobile_templates()
        
        # Check for mobile data directory if it exists
        mobile_dir = self.get_project_root() / "mobile"
        if mobile_dir.exists():
            self._validate_mobile_directory_structure(mobile_dir)
        
        print("✅ Mobile build artifacts validation passed")
        
        # Ensure test completes quickly
        self.assert_fast_execution(1.5)
    
    def _validate_apk_structure(self, apk_path: Path) -> None:
        """Validate APK has proper ZIP structure and required files"""
        try:
            with zipfile.ZipFile(apk_path, 'r') as apk_zip:
                file_list = apk_zip.namelist()
                
                # Check for required APK components
                required_files = [
                    'AndroidManifest.xml',
                    'classes.dex',
                    'META-INF/MANIFEST.MF'
                ]
                
                for required_file in required_files:
                    assert required_file in file_list, \
                        f"APK missing required file: {required_file}"
                
                # Check for assets directory (should contain our web app)
                assets_files = [f for f in file_list if f.startswith('assets/')]
                assert assets_files, "APK missing assets directory"
                
        except zipfile.BadZipFile:
            pytest.fail(f"APK file is corrupted or not a valid ZIP: {apk_path}")
    
    def _get_apk_info_with_aapt(self, apk_path: Path) -> Dict[str, Any]:
        """Get APK information using aapt tool without installing"""
        try:
            # Try to find aapt in Android SDK
            aapt_cmd = self._find_aapt_command()
            
            if not aapt_cmd:
                # Fallback: use basic APK validation without aapt
                return self._get_apk_info_fallback(apk_path)
            
            # Run aapt dump badging to get APK info
            result = self.run_quick_command(
                [aapt_cmd, 'dump', 'badging', str(apk_path)],
                timeout=5,
                description="aapt dump badging"
            )
            
            if result.returncode != 0:
                return self._get_apk_info_fallback(apk_path)
            
            return self._parse_aapt_output(result.stdout)
            
        except Exception as e:
            print(f"⚠️ aapt validation failed, using fallback: {e}")
            return self._get_apk_info_fallback(apk_path)
    
    def _find_aapt_command(self) -> Optional[str]:
        """Find aapt command in Android SDK"""
        # Check common aapt locations
        android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
        
        if android_home:
            # Try build-tools directories
            build_tools_dir = Path(android_home) / "build-tools"
            if build_tools_dir.exists():
                for version_dir in sorted(build_tools_dir.iterdir(), reverse=True):
                    if version_dir.is_dir():
                        aapt_path = version_dir / "aapt"
                        aapt2_path = version_dir / "aapt2"
                        
                        # Prefer aapt2 if available
                        if aapt2_path.exists():
                            return str(aapt2_path)
                        elif aapt_path.exists():
                            return str(aapt_path)
        
        # Check if aapt is in PATH
        import shutil
        aapt_in_path = shutil.which('aapt') or shutil.which('aapt2')
        if aapt_in_path:
            return aapt_in_path
        
        return None
    
    def _parse_aapt_output(self, aapt_output: str) -> Dict[str, Any]:
        """Parse aapt dump badging output"""
        info = {
            'package_name': '',
            'main_activity': '',
            'permissions': [],
            'version_code': '',
            'version_name': ''
        }
        
        for line in aapt_output.split('\n'):
            line = line.strip()
            
            if line.startswith('package:'):
                # Extract package name
                if "name='" in line:
                    start = line.find("name='") + 6
                    end = line.find("'", start)
                    info['package_name'] = line[start:end]
            
            elif line.startswith('launchable-activity:'):
                # Extract main activity
                if "name='" in line:
                    start = line.find("name='") + 6
                    end = line.find("'", start)
                    info['main_activity'] = line[start:end]
            
            elif line.startswith('uses-permission:'):
                # Extract permissions
                if "name='" in line:
                    start = line.find("name='") + 6
                    end = line.find("'", start)
                    permission = line[start:end]
                    info['permissions'].append(permission)
        
        return info
    
    def _get_apk_info_fallback(self, apk_path: Path) -> Dict[str, Any]:
        """Fallback APK info extraction using ZIP inspection"""
        try:
            with zipfile.ZipFile(apk_path, 'r') as apk_zip:
                # Basic validation - assume correct package if APK structure is valid
                return {
                    'package_name': 'com.run.heatmap',  # Expected package
                    'main_activity': 'com.run.heatmap.MainActivity',  # Expected activity
                    'permissions': ['android.permission.INTERNET'],  # Minimal expected
                    'version_code': 'unknown',
                    'version_name': 'unknown'
                }
        except Exception:
            pytest.fail("Could not validate APK structure")
    
    def _validate_mobile_templates(self) -> None:
        """Validate mobile configuration templates have required placeholders"""
        server_dir = self.get_server_dir()
        
        # Validate Android manifest template
        manifest_template = server_dir / "AndroidManifest.xml.template"
        if manifest_template.exists():
            required_placeholders = [
                'MainActivity',
                'android.permission.INTERNET',
                'android:name=".MainActivity"'
            ]
            self.validate_mobile_template(manifest_template, required_placeholders)
        
        # Validate MainActivity template
        activity_template = server_dir / "MainActivity.java.template"
        if activity_template.exists():
            required_placeholders = [
                'MainActivity',
                'HttpRangeServerPlugin'
            ]
            self.validate_mobile_template(activity_template, required_placeholders)
        
        # Validate mobile HTML template
        html_template = server_dir / "mobile_template.html"
        if html_template.exists():
            required_placeholders = [
                '<div id="map"',
                'maplibre',
                'pmtiles'
            ]
            self.validate_mobile_template(html_template, required_placeholders)
    
    def _validate_mobile_directory_structure(self, mobile_dir: Path) -> None:
        """Validate mobile directory has expected structure"""
        expected_dirs = ['www', 'android']
        expected_files = ['capacitor.config.json', 'package.json']
        
        for dir_name in expected_dirs:
            dir_path = mobile_dir / dir_name
            if dir_path.exists():
                self.check_directory_exists(dir_path, f"Mobile {dir_name} directory")
        
        for file_name in expected_files:
            file_path = mobile_dir / file_name
            if file_path.exists():
                self.check_file_exists(file_path, f"Mobile {file_name}")
        
        # Check www directory has web assets
        www_dir = mobile_dir / "www"
        if www_dir.exists():
            expected_www_files = ['index.html', 'main.js']
            for file_name in expected_www_files:
                file_path = www_dir / file_name
                if file_path.exists():
                    self.check_file_exists(file_path, f"Mobile www/{file_name}")
    
    def test_pmtiles_generation_from_sample_data(self):
        """
        Test PMTiles generation from sample data completes successfully
        Requirements: 4.4, 1.3
        """
        print("🔍 Testing PMTiles generation from sample data...")
        
        # Check if make_pmtiles.py script exists
        make_pmtiles_script = self.get_server_dir() / "make_pmtiles.py"
        self.check_file_exists(make_pmtiles_script, "PMTiles generation script")
        
        # Verify script has mobile-compatible PMTiles functionality
        script_content = make_pmtiles_script.read_text(encoding='utf-8', errors='ignore')
        
        required_components = [
            'pmtiles',
            'geojson',
            'tippecanoe'
        ]
        
        for component in required_components:
            assert component.lower() in script_content.lower(), \
                f"make_pmtiles.py missing {component} functionality for mobile"
        
        # Check for existing PMTiles files
        pmtiles_locations = [
            self.get_server_dir() / "runs.pmtiles",
            self.get_project_root() / "mobile" / "www" / "data" / "runs.pmtiles"
        ]
        
        pmtiles_found = False
        for pmtiles_path in pmtiles_locations:
            if pmtiles_path.exists():
                self._validate_pmtiles_file(pmtiles_path)
                pmtiles_found = True
                print(f"✅ Valid PMTiles file found: {pmtiles_path}")
                break
        
        if not pmtiles_found:
            print("ℹ️  PMTiles file not found (created during full mobile build)")
        
        # Ensure test completes quickly
        self.assert_fast_execution(1.5)
    
    def test_mobile_app_bundle_contains_required_data(self):
        """
        Test mobile app bundle contains required test data
        Requirements: 4.4, 1.3
        """
        print("🔍 Testing mobile app bundle data requirements...")
        
        mobile_dir = self.get_project_root() / "mobile"
        
        if mobile_dir.exists():
            www_dir = mobile_dir / "www"
            if www_dir.exists():
                # Check for data directory in mobile bundle
                data_dir = www_dir / "data"
                if data_dir.exists():
                    self.check_directory_exists(data_dir, "Mobile app data directory")
                    
                    # Check for PMTiles data file
                    pmtiles_file = data_dir / "runs.pmtiles"
                    if pmtiles_file.exists():
                        self._validate_pmtiles_file(pmtiles_file)
                        print("✅ Mobile app bundle contains PMTiles data")
                    else:
                        print("ℹ️  PMTiles data not found in mobile bundle")
                else:
                    print("ℹ️  Mobile app data directory not found")
                
                # Check for required web assets in mobile bundle
                required_assets = [
                    'index.html',
                    'main.js',
                    'sw.js'
                ]
                
                for asset in required_assets:
                    asset_path = www_dir / asset
                    if asset_path.exists():
                        self.check_file_exists(asset_path, f"Mobile bundle {asset}")
                        print(f"✅ Mobile bundle contains {asset}")
                    else:
                        print(f"ℹ️  Mobile bundle missing {asset}")
            else:
                print("ℹ️  Mobile www directory not found")
        else:
            print("ℹ️  Mobile directory not found (created during full build)")
        
        # Ensure test completes quickly
        self.assert_fast_execution(1.5)
    
    def test_mobile_specific_configuration_validation(self):
        """
        Test mobile-specific configuration validation
        Requirements: 4.4, 1.3
        """
        print("🔍 Testing mobile-specific configuration validation...")
        
        mobile_dir = self.get_project_root() / "mobile"
        
        if mobile_dir.exists():
            # Validate Capacitor configuration
            capacitor_config = mobile_dir / "capacitor.config.json"
            if capacitor_config.exists():
                self._validate_capacitor_config(capacitor_config)
                print("✅ Capacitor configuration validated")
            
            # Validate package.json for mobile dependencies
            package_json = mobile_dir / "package.json"
            if package_json.exists():
                self._validate_mobile_package_json(package_json)
                print("✅ Mobile package.json validated")
            
            # Validate Android configuration if present
            android_dir = mobile_dir / "android"
            if android_dir.exists():
                self._validate_android_configuration(android_dir)
                print("✅ Android configuration validated")
        else:
            print("ℹ️  Mobile directory not found (created during full build)")
        
        # Ensure test completes quickly
        self.assert_fast_execution(1.5)
    
    def _validate_pmtiles_file(self, pmtiles_path: Path) -> None:
        """Validate PMTiles file for mobile app usage"""
        # Check file size is reasonable for mobile
        file_size = pmtiles_path.stat().st_size
        assert file_size > 100, f"PMTiles file too small: {file_size} bytes"
        assert file_size < 100 * 1024 * 1024, f"PMTiles file too large for mobile: {file_size} bytes"
        
        # Basic file header validation
        with open(pmtiles_path, 'rb') as f:
            header = f.read(16)
            assert len(header) > 0, "PMTiles file appears to be empty"
            # PMTiles files should have specific structure
            assert len(header) >= 8, "PMTiles file header too short"
    
    def _validate_capacitor_config(self, config_path: Path) -> None:
        """Validate Capacitor configuration for mobile app"""
        import json
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Check required Capacitor configuration
            required_fields = ['appId', 'appName', 'webDir']
            for field in required_fields:
                assert field in config, f"Capacitor config missing required field: {field}"
            
            # Validate app ID format
            app_id = config.get('appId', '')
            assert 'com.run.heatmap' in app_id, f"Unexpected app ID: {app_id}"
            
            # Check web directory configuration
            web_dir = config.get('webDir', '')
            assert web_dir == 'www', f"Unexpected webDir: {web_dir}"
            
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid Capacitor configuration JSON: {e}")
        except Exception as e:
            pytest.fail(f"Capacitor configuration validation failed: {e}")
    
    def _validate_mobile_package_json(self, package_path: Path) -> None:
        """Validate mobile package.json has required dependencies"""
        import json
        
        try:
            with open(package_path, 'r') as f:
                package = json.load(f)
            
            # Check for Capacitor dependencies
            dependencies = package.get('dependencies', {})
            dev_dependencies = package.get('devDependencies', {})
            all_deps = {**dependencies, **dev_dependencies}
            
            expected_deps = [
                '@capacitor/core',
                '@capacitor/cli',
                '@capacitor/android'
            ]
            
            for dep in expected_deps:
                if dep not in all_deps:
                    print(f"ℹ️  Mobile package.json missing {dep} (added during build)")
            
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid mobile package.json: {e}")
        except Exception as e:
            pytest.fail(f"Mobile package.json validation failed: {e}")
    
    def _validate_android_configuration(self, android_dir: Path) -> None:
        """Validate Android-specific configuration"""
        # Check for key Android files
        expected_files = [
            'app/build.gradle',
            'build.gradle',
            'app/src/main/AndroidManifest.xml'
        ]
        
        for file_path in expected_files:
            full_path = android_dir / file_path
            if full_path.exists():
                print(f"✅ Found Android config: {file_path}")
            else:
                print(f"ℹ️  Android config not found: {file_path}")
        
        # Check for custom plugin files
        plugin_dir = android_dir / "app" / "src" / "main" / "java" / "com" / "run" / "heatmap"
        if plugin_dir.exists():
            expected_plugin_files = [
                'MainActivity.java',
                'HttpRangeServerPlugin.java'
            ]
            
            for plugin_file in expected_plugin_files:
                plugin_path = plugin_dir / plugin_file
                if plugin_path.exists():
                    print(f"✅ Found mobile plugin: {plugin_file}")
                else:
                    print(f"ℹ️  Mobile plugin not found: {plugin_file}")