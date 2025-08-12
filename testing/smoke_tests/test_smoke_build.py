"""
Smoke tests for mobile build process
Fast validation of build infrastructure without full build execution
"""
import pytest
from .base_smoke_test import BaseSmokeTest


@pytest.mark.smoke
@pytest.mark.smoke_build
class TestMobileBuildSmoke(BaseSmokeTest):
    """Smoke tests for mobile build infrastructure"""
    
    def test_build_scripts_exist(self):
        """Verify mobile build scripts exist"""
        server_dir = self.get_server_dir()
        
        build_files = [
            ("build_mobile.py", "Main mobile build script"),
            ("mobile_template.html", "Mobile HTML template"),
            ("mobile_main.js", "Mobile JavaScript main file")
        ]
        
        for file_name, description in build_files:
            file_path = server_dir / file_name
            self.check_file_exists(file_path, description)
    
    def test_mobile_configuration_templates(self):
        """Verify mobile configuration templates exist and are valid"""
        server_dir = self.get_server_dir()
        
        # Android configuration templates
        android_templates = [
            ("AndroidManifest.xml.template", ["{{PACKAGE_NAME}}", "{{APP_NAME}}"]),
            ("MainActivity.java.template", ["{{PACKAGE_NAME}}", "{{APP_NAME}}"]),
            ("HttpRangeServerPlugin.java.template", ["{{PACKAGE_NAME}}"])
        ]
        
        for template_name, required_placeholders in android_templates:
            template_path = server_dir / template_name
            self.check_file_exists(template_path, f"Android template: {template_name}")
            self.validate_mobile_template(template_path, required_placeholders)
    
    def test_mobile_build_dependencies(self):
        """Verify mobile build dependencies and tools"""
        # Check Python dependencies for build process
        self.check_python_import('os', 'OS operations for build')
        self.check_python_import('shutil', 'File operations for build')
        self.check_python_import('subprocess', 'Process execution for build')
        
        # Check build script structure
        build_script = self.get_server_dir() / "build_mobile.py"
        if build_script.exists():
            content = build_script.read_text(encoding='utf-8', errors='ignore')
            
            # Check for key build functionality
            build_indicators = [
                "capacitor",  # Capacitor framework
                "android",    # Android platform
                "build",      # Build process
                "mobile"      # Mobile-specific code
            ]
            
            found_indicators = []
            for indicator in build_indicators:
                if indicator.lower() in content.lower():
                    found_indicators.append(indicator)
            
            assert len(found_indicators) >= 2, \
                f"Build script missing key functionality. Found: {found_indicators}"
    
    def test_cached_build_artifacts(self):
        """Check for cached build artifacts (optional for fast mode)"""
        # Check for cached APK
        cached_apk_path = self.get_cached_apk_path()
        
        if cached_apk_path.exists():
            print(f"✅ Found cached APK: {cached_apk_path}")
            
            # Basic APK validation
            apk_size = cached_apk_path.stat().st_size
            assert apk_size > 1024 * 1024, f"APK file too small: {apk_size} bytes"  # At least 1MB
            
            # Check APK file signature
            with open(cached_apk_path, 'rb') as f:
                header = f.read(4)
                assert header == b'PK\x03\x04', "APK file has invalid ZIP signature"
            
            print(f"   APK size: {apk_size / (1024*1024):.1f} MB")
        else:
            print("ℹ️  No cached APK found (will be built during full test run)")
        
        # Check for cached PMTiles data
        cached_data_dir = self.get_project_root() / "testing" / "cached_test_data"
        if cached_data_dir.exists():
            pmtiles_files = list(cached_data_dir.glob("*.pmtiles"))
            if pmtiles_files:
                print(f"✅ Found {len(pmtiles_files)} cached PMTiles files")
                
                # Basic PMTiles validation
                for pmtiles_file in pmtiles_files:
                    size = pmtiles_file.stat().st_size
                    assert size > 1024, f"PMTiles file too small: {pmtiles_file}"
                    print(f"   {pmtiles_file.name}: {size / 1024:.1f} KB")
            else:
                print("ℹ️  No cached PMTiles files found")
        else:
            print("ℹ️  No cached data directory found")
    
    def test_mobile_build_artifacts_structure(self):
        """Verify mobile build artifacts have expected structure"""
        artifacts = self.check_mobile_build_artifacts()
        
        # Core build files should exist
        required_artifacts = [
            'build_script',
            'mobile_template', 
            'mobile_main_js'
        ]
        
        missing_artifacts = []
        for artifact in required_artifacts:
            if not artifacts.get(artifact, False):
                missing_artifacts.append(artifact)
        
        assert not missing_artifacts, \
            f"Missing required build artifacts: {missing_artifacts}"
        
        # Android-specific templates should exist
        android_artifacts = [
            'android_manifest_template',
            'main_activity_template',
            'http_plugin_template'
        ]
        
        android_count = sum(1 for artifact in android_artifacts if artifacts.get(artifact, False))
        assert android_count >= 2, \
            f"Missing Android templates. Found {android_count}/{len(android_artifacts)}"
        
        print(f"✅ Build artifacts check: {sum(artifacts.values())}/{len(artifacts)} found")
    
    def test_mobile_template_content(self):
        """Verify mobile template files have expected content"""
        server_dir = self.get_server_dir()
        
        # Check mobile HTML template
        html_template = server_dir / "mobile_template.html"
        if html_template.exists():
            self.check_file_contains(html_template, "<html", "HTML structure")
            self.check_file_contains(html_template, "{{", "Template placeholders")
            
            # Check for mobile-specific content
            content = html_template.read_text(encoding='utf-8', errors='ignore')
            mobile_indicators = ["viewport", "mobile", "map", "script"]
            
            found_indicators = sum(1 for indicator in mobile_indicators 
                                 if indicator.lower() in content.lower())
            assert found_indicators >= 2, \
                f"Mobile template missing key indicators. Found {found_indicators}/{len(mobile_indicators)}"
        
        # Check mobile JavaScript
        js_main = server_dir / "mobile_main.js"
        if js_main.exists():
            content = js_main.read_text(encoding='utf-8', errors='ignore')
            
            # Basic JavaScript validation
            assert len(content.strip()) > 100, "Mobile JavaScript file too small"
            
            # Check for mobile/map functionality
            js_indicators = ["map", "mobile", "function", "document"]
            found_indicators = sum(1 for indicator in js_indicators 
                                 if indicator.lower() in content.lower())
            assert found_indicators >= 2, \
                f"Mobile JavaScript missing key functionality. Found {found_indicators}/{len(js_indicators)}"
    
    def test_build_environment_check(self):
        """Verify build environment is ready"""
        import os
        import sys
        
        # Check Python environment
        assert sys.version_info >= (3, 7), f"Python 3.7+ required for build"
        
        # Check for common build tools (without requiring them)
        build_tools = ['node', 'npm', 'npx']
        available_tools = []
        
        for tool in build_tools:
            try:
                result = self.run_quick_command([tool, '--version'], timeout=2)
                if result.returncode == 0:
                    available_tools.append(tool)
                    print(f"✅ {tool} available")
            except:
                print(f"ℹ️  {tool} not available")
        
        # We don't require build tools for smoke tests, just report status
        if available_tools:
            print(f"✅ Build tools available: {', '.join(available_tools)}")
        else:
            print("ℹ️  No build tools detected (required for full mobile build)")
    
    def test_network_security_config(self):
        """Verify network security configuration template"""
        server_dir = self.get_server_dir()
        network_config = server_dir / "network_security_config.xml.template"
        
        if network_config.exists():
            print("✅ Found network security config template")
            
            # Basic XML structure validation
            content = network_config.read_text(encoding='utf-8', errors='ignore')
            assert '<?xml' in content, "Network config missing XML header"
            assert 'network-security-config' in content, "Network config missing root element"
            
            # Check for localhost/development configuration
            if 'localhost' in content.lower() or '127.0.0.1' in content:
                print("   Contains localhost configuration for development")
        else:
            print("ℹ️  Network security config template not found (optional)")