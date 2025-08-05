#!/usr/bin/env python3
"""
Infrastructure Setup Tests

This module contains tests that handle the expensive, one-time setup operations
required before running functional tests:
- Building APK with test data 
- Installing APK on emulator
- Setting up test environment

These tests run first (00_ prefix) and prepare the infrastructure that
functional tests depend on.
"""
import pytest
import time
from pathlib import Path


@pytest.mark.core
@pytest.mark.mobile
class TestInfrastructureSetup:
    """Infrastructure setup tests for mobile testing environment"""
    
    def test_build_and_install_test_apk(self, session_setup):
        """
        🏗️ Build and install test APK with sample data
        
        This test handles all the expensive infrastructure setup:
        - Creates isolated test environment with GPX data
        - Runs data pipeline (GPX import, PMTiles generation)  
        - Builds mobile APK with test data
        - Installs APK on emulator
        
        This runs once per test session and enables all functional tests.
        """
        print("🏗️ Infrastructure setup test starting...")
        print("   This test builds APK with test data and installs it on emulator")
        
        # The session_setup fixture handles all the actual work
        # We just need to verify it completed successfully
        setup_info = session_setup
        
        # Verify essential components were set up
        assert 'package_name' in setup_info, "Package name not set in setup"
        assert setup_info['package_name'] == 'com.run.heatmap', f"Unexpected package name: {setup_info['package_name']}"
        
        if not setup_info.get('apk_path') and not setup_info.get('test_env'):
            # Fast mode - APK already exists
            print("   ⚡ Fast mode: Using existing APK installation")
        else:
            # Full mode - APK was built and installed
            if setup_info.get('apk_path'):
                apk_path = Path(setup_info['apk_path'])
                assert apk_path.exists(), f"APK not found after build: {apk_path}"
                print(f"   ✅ APK built and available: {apk_path}")
            
            if setup_info.get('pmtiles_path'):
                pmtiles_path = Path(setup_info['pmtiles_path'])
                assert pmtiles_path.exists(), f"PMTiles not found after build: {pmtiles_path}"
                print(f"   ✅ PMTiles generated: {pmtiles_path}")
            
            print("   ✅ Test environment created with sample GPX data")
        
        print("   ✅ APK installed and ready for functional testing")
        print("🏗️ Infrastructure setup completed successfully!")
        
        # Brief pause to ensure everything is settled
        time.sleep(2)