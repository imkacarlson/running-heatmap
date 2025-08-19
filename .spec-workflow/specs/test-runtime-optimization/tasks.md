# Test Runtime Optimization Implementation Tasks

## Task Overview

This implementation plan reduces test runtime from ~408s to ≤240s through targeted optimizations: deterministic waits, fixture efficiency, lasso optimization, and integration with existing persistent infrastructure. Tasks are organized into atomic, sequential steps that leverage existing codebase patterns.

## Tasks

- [x] 1. Create deterministic wait helpers in base_mobile_test.py
  - File: testing/base_mobile_test.py
  - Add wait_for_webview_ready(), wait_for_map_stable(), wait_for_layers_stable() functions
  - Integrate with existing WebDriverWait patterns and map_load_detector.py logic
  - Purpose: Replace time.sleep() calls with explicit readiness polling
  - _Leverage: testing/map_load_detector.py, existing WebDriverWait usage_
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 2. Replace sleep() calls with deterministic waits in activity visibility test
  - File: testing/test_01_activity_visibility.py
  - Replace time.sleep(5), time.sleep(3), time.sleep(8), time.sleep(4) with appropriate deterministic waits
  - Use wait_for_map_stable() for map loading, wait_for_layers_stable() for activity visibility
  - Purpose: Eliminate fixed delays in core activity visibility testing
  - _Leverage: testing/base_mobile_test.py wait helpers from task 1_
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 3. Replace sleep() calls with deterministic waits in lasso selection test  
  - File: testing/test_basic_lasso_selection.py
  - Replace time.sleep(12), time.sleep(1), time.sleep(0.5), time.sleep(1.0), time.sleep(2.0) with deterministic waits
  - Focus on app startup (12s), tile loading (1s), lasso processing (2s) delays
  - Purpose: Eliminate fixed delays in lasso selection testing workflow
  - _Leverage: testing/base_mobile_test.py wait helpers from task 1_
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 4. Replace sleep() calls with deterministic waits in upload test
  - File: testing/test_upload_functionality.py  
  - Replace major sleep() calls: time.sleep(12), time.sleep(3), time.sleep(2), time.sleep(5)
  - Focus on app startup, file picker readiness, navigation waits
  - Skip WebView pixel-sampling branches where sampling is impossible
  - Purpose: Optimize upload test timing while maintaining native picker simulation
  - _Leverage: testing/base_mobile_test.py wait helpers from task 1_
  - _Requirements: 2.1, 2.2, 5.3_

- [x] 5. Replace sleep() calls with deterministic waits in extras filter test
  - File: testing/test_extras_last_activity_filter.py
  - Replace time.sleep(12) app startup delay with deterministic wait
  - Purpose: Complete deterministic wait coverage across all test files
  - _Leverage: testing/base_mobile_test.py wait helpers from task 1_
  - _Requirements: 2.1, 2.2_

- [x] 6. Optimize lasso polygon from 110 to 40 vertices
  - File: testing/test_basic_lasso_selection.py
  - Change window.__mapTestHelpers.generateCenterPolygon(110) to generateCenterPolygon(40)
  - Verify geometric coverage maintains convex, concave, and edge-crossing test cases
  - Purpose: Reduce pointer events for faster lasso selection while maintaining validation quality
  - _Leverage: existing W3C touch actions, coordinate projection system_
  - _Requirements: 4.1, 4.2, 4.4_

- [x] 7. Convert mobile_driver fixture to module scope
  - File: testing/conftest.py
  - Change @pytest.fixture(scope="function") to @pytest.fixture(scope="module") for mobile_driver
  - Move configure_emulator_stability() call to session or module level to avoid per-test execution
  - Add driver.reset() capability for state cleanup when needed
  - Purpose: Minimize ADB stability tweaks and driver setup overhead
  - _Leverage: existing configure_emulator_stability(), cleanup utilities_
  - _Requirements: 3.1, 3.2_

- [x] 8. Add selective reset mechanism with needs_clean_state marker
  - File: testing/conftest.py (continue from task 7)
  - Implement @pytest.mark.needs_clean_state detection in mobile_driver fixture
  - Add driver.reset() or equivalent cleanup for tests marked as needing clean state
  - Create reset logic that clears app state without full driver recreation
  - Purpose: Maintain test isolation for state-dependent operations with module-scoped driver
  - _Leverage: existing cleanup utilities, pytest marker system_
  - _Requirements: 3.3, 3.4_

- [x] 9. Add pytest markers for test organization
  - File: testing/pytest.ini 
  - Add markers: slow, needs_clean_state for test categorization
  - Update marker descriptions and usage documentation
  - Purpose: Support test organization and selective execution
  - _Leverage: existing pytest.ini marker configuration_
  - _Requirements: 8.1, 8.2_

- [x] 10. Mark tests requiring clean state with needs_clean_state marker
  - Files: testing/test_upload_functionality.py, other state-dependent tests
  - Add @pytest.mark.needs_clean_state to tests that modify app state or require fresh context
  - Identify tests that upload files, modify settings, or change app configuration
  - Purpose: Ensure proper isolation for tests that need clean state with module-scoped driver
  - _Leverage: pytest marker system, existing test patterns_
  - _Requirements: 3.3, 8.2_

- [x] 11. Update map_load_detector.py with stable tile count verification
  - File: testing/map_load_detector.py
  - Enhance existing tile count detection with stability verification (3 consecutive stable checks)
  - Add wait_for_stable_tiles() function that polls tile counts until stable
  - Purpose: Improve map readiness detection for deterministic waits
  - _Leverage: existing tile count detection logic in map_load_detector.py_
  - _Requirements: 2.2, 2.3_

- [x] 12. Skip WebView pixel sampling in upload test
  - File: testing/test_upload_functionality.py
  - Identify and skip pixel-sampling verification branches that are impossible in WebView context
  - Add conditional logic to bypass sampling while maintaining other upload verification
  - Purpose: Remove impossible operations that cause unnecessary delays
  - _Leverage: existing WebView detection, upload verification logic_
  - _Requirements: 5.3_

- [x] 13. Integration testing and performance validation
  - Files: Create testing/performance_validation.py
  - Implement runtime measurement over 5 consecutive runs to validate ≤240s target
  - Add variance tracking and performance regression detection
  - Create before/after comparison reports with timing breakdowns
  - Purpose: Validate optimization effectiveness and detect regressions
  - _Leverage: existing PerformanceMetrics class in run_tests.py_
  - _Requirements: 1.1, 1.2_

- [x] 14. Add network isolation verification
  - Files: testing/test_00_infrastructure_setup.py (enhance existing)
  - Add test to verify zero external network requests during test execution
  - Remove any external connectivity pings or network speed estimation calls
  - Purpose: Eliminate network latency as a variable in test runtime
  - _Leverage: existing infrastructure tests_
  - _Requirements: 6.1, 6.3, 6.4_

- [x] 15. Update documentation with optimization usage
  - File: testing/README.md
  - Document new pytest markers (needs_clean_state) and their usage
  - Add performance optimization section with before/after metrics
  - Include troubleshooting for optimization-related issues
  - Purpose: Provide clear guidance on optimization features and troubleshooting
  - _Leverage: existing testing documentation structure_
  - _Requirements: All_

## Implementation Notes

### Execution Sequence
Tasks 1-5 establish the deterministic wait foundation, tasks 6-8 implement fixture and lasso optimizations, tasks 9-12 add organizational improvements, and tasks 13-15 provide validation and documentation.

### Dependencies
- Tasks 2-5 depend on task 1 (wait helpers)
- Task 8 depends on task 7 (fixture scope change)
- Task 10 depends on task 9 (marker definitions)
- Tasks 13-15 validate the implementation from tasks 1-12

### Risk Mitigation
- Each optimization includes fallback to original behavior on failure
- Module-scoped driver includes state pollution detection and reset capability
- Performance validation ensures optimization effectiveness
- Documentation provides troubleshooting for optimization issues