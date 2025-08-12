# Implementation Plan

- [x] 1. Set up smoke test infrastructure and core framework
  - Create smoke test directory structure and base classes focused on mobile testing
  - Implement SmokeTestRunner class with mobile-focused test discovery and execution
  - Create pytest markers and configuration for mobile smoke tests
  - _Requirements: 1.1, 2.1, 5.1_

- [x] 2. Implement mobile data pipeline smoke tests
  - [x] 2.1 Create test_smoke_data_pipeline.py with data processing validation
    - Write test for runs.pkl loading and validation within 2-second timeout
    - Implement PMTiles generation verification from sample data
    - Create spatial index building validation test
    - _Requirements: 4.1, 1.1_

  - [x] 2.2 Add mobile build artifact validation tests
    - Test mobile data directory structure and required files exist
    - Validate PMTiles file integrity and basic metadata
    - Implement graceful failure handling for missing or corrupt data files
    - _Requirements: 4.1, 1.3_

- [x] 3. Implement mobile build process smoke tests
  - [x] 3.1 Create test_smoke_build.py with build validation
    - Write tests for build_mobile.py script execution without errors
    - Implement mobile directory structure validation after build
    - Test that required mobile assets (HTML, JS, PMTiles) are generated
    - _Requirements: 4.3, 1.2_

  - [x] 3.2 Add mobile configuration validation
    - Validate Capacitor configuration files are properly generated
    - Test mobile template processing and asset copying
    - Implement build artifact size and integrity checks
    - _Requirements: 4.3, 1.3_

- [ ] 4. Implement API and web interface smoke tests
  - [ ] 4.1 Create test_smoke_api.py with API endpoint validation
    - Write tests for key API endpoints (/api/last_activity, /api/runs_in_area)
    - Implement API response format validation
    - Test API error handling and timeout behavior
    - _Requirements: 4.2, 1.1_

  - [ ] 4.2 Create test_smoke_web.py with web interface validation
    - Write tests for web page loading without JavaScript errors
    - Implement DOM structure validation (map container, required elements)
    - Test external library loading (MapLibre, PMTiles)
    - _Requirements: 4.4, 1.1_

- [ ] 5. Implement mobile app smoke tests
  - [ ] 5.1 Create test_smoke_mobile.py with APK validation
    - Write test to verify cached test APK exists and is valid
    - Implement APK installation verification without full emulator startup
    - Test mobile build artifacts and dependencies are present
    - _Requirements: 4.4, 1.1_

  - [ ] 5.2 Add mobile data pipeline validation
    - Test PMTiles generation from sample data completes successfully
    - Validate mobile app bundle contains required test data
    - Implement mobile-specific configuration validation
    - _Requirements: 4.4, 1.3_

- [x] 6. Integrate smoke tests with existing test runner
  - [x] 6.1 Modify run_tests.py to support --smoke flag
    - Add smoke test command-line argument parsing
    - Implement smoke test discovery and execution logic
    - Create smoke test reporting integration with existing HTML reports
    - _Requirements: 5.1, 5.2_

  - [x] 6.2 Add granular smoke test execution options
    - Implement --smoke --server, --smoke --api, --smoke --mobile flags
    - Create help text and documentation for new commands
    - Add smoke test timing and performance reporting
    - _Requirements: 2.1, 5.3_

- [ ] 7. Create mobile test data and configuration management
  - [ ] 7.1 Set up minimal mobile test dataset for smoke tests
    - Create lightweight sample GPX files for mobile testing
    - Generate minimal runs.pkl file for mobile app data pipeline
    - Implement mobile test data validation and integrity checks
    - _Requirements: 4.2, 1.1_

  - [ ] 7.2 Implement mobile smoke test configuration system
    - Create SmokeTestConfig class with mobile-specific timeout and path settings
    - Add mobile build environment configuration overrides
    - Implement mobile APK and data validation error handling
    - _Requirements: 2.1, 1.3_

- [ ] 8. Add error handling and reporting enhancements
  - [ ] 8.1 Implement comprehensive error categorization
    - Create TestFailure dataclass with detailed error information
    - Add component-specific error messages and suggestions
    - Implement graceful degradation for missing dependencies
    - _Requirements: 1.3, 5.4_

  - [ ] 8.2 Enhance reporting and debugging capabilities
    - Add detailed timing information for each test category
    - Create actionable error messages with troubleshooting steps
    - Implement verbose mode for smoke test debugging
    - _Requirements: 5.4, 1.3_

- [x] 9. Create standalone smoke test runner
  - [x] 9.1 Implement smoke_tests.py as independent script
    - Create standalone script that runs without run_tests.py
    - Add command-line interface with argparse
    - Implement basic reporting and exit codes for CI/CD
    - _Requirements: 2.1, 2.2_

  - [ ] 9.2 Add performance monitoring and optimization
    - Implement execution time tracking for each test phase
    - Add memory usage monitoring during test execution
    - Create performance regression detection
    - _Requirements: 1.1, 2.1_

- [ ] 10. Update documentation and integration
  - [ ] 10.1 Update testing framework documentation
    - Modify testing/README.md with dual-tier testing explanation
    - Add decision matrix for when to use smoke vs comprehensive tests
    - Create troubleshooting guide for smoke test failures
    - _Requirements: 6.1, 6.2_

  - [ ] 10.2 Create developer workflow integration
    - Add smoke test examples to development workflow
    - Create pre-commit hook integration guidance
    - Document CI/CD integration patterns
    - _Requirements: 6.3, 6.4_

- [ ] 11. Testing and validation of smoke test framework
  - [ ] 11.1 Write tests for the smoke test framework itself
    - Create unit tests for SmokeTestRunner class
    - Test error handling and edge cases
    - Validate performance targets are met consistently
    - _Requirements: 1.1, 1.4_

  - [ ] 11.2 Integration testing with existing framework
    - Test smoke tests work alongside existing emulator tests
    - Validate reporting integration doesn't break existing functionality
    - Test command-line interface compatibility
    - _Requirements: 3.3, 5.1_