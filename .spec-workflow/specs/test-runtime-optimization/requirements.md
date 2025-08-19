# Test Runtime Optimization Requirements

## Introduction

This specification defines requirements for reducing end-to-end test runtime by ~40% (from 408s to ≤240s) for Android/WebView (Appium) mobile app tests while maintaining complete functional coverage. The optimization focuses on eliminating waste in the existing test suite without adding complexity - specifically targeting deterministic waits, fixture efficiency, and leveraging existing persistent infrastructure.

## Alignment with Product Vision

This optimization aligns with the project's technical excellence values by improving development velocity through efficient testing while maintaining the reliability standards essential for offline GPS visualization functionality. The approach prioritizes optimization over additional features to address codebase growth concerns.

## Requirements

### Requirement 1: Runtime Performance Target

**User Story:** As a developer, I want test execution time reduced from ~408s to ≤240s, so that development cycles are more efficient while maintaining complete coverage.

#### Acceptance Criteria

1. WHEN full test suite executes THEN total runtime SHALL be ≤240s on reference environment (WSL2, Android emulator, 4 cores, 8GB RAM)
2. WHEN measuring runtime performance THEN median execution time over 5 consecutive runs SHALL be ≤240s  
3. WHEN persistence mode is used (existing persist_tests.sh) THEN cold emulator/Appium startup costs SHALL be excluded from runtime measurement
4. WHEN runtime target is not met THEN system SHALL provide detailed timing breakdown identifying bottlenecks

### Requirement 2: Deterministic Wait Strategy

**User Story:** As a developer, I want all fixed sleep statements replaced with deterministic readiness signals, so that tests are both faster and more reliable.

#### Acceptance Criteria

1. WHEN WebView context is needed THEN system SHALL wait for explicit WebView attachment signal instead of fixed delays
2. WHEN map loading is required THEN system SHALL poll for map.loaded() === true and stable tile counts
3. WHEN activity visibility is checked THEN system SHALL verify layer counts reach expected thresholds and remain stable
4. WHEN deterministic waits are implemented THEN zero unconditional sleep(N) statements SHALL remain except in justified helper functions

### Requirement 3: Test Fixture Optimization

**User Story:** As a developer, I want test fixtures re-scoped to avoid redundant ADB stability tweaks, so that setup overhead is minimized while maintaining test isolation.

#### Acceptance Criteria

1. WHEN mobile_driver fixture is used THEN it SHALL be module-scoped instead of function-scoped
2. WHEN ADB stability tweaks are needed THEN they SHALL be applied once per session, not per test
3. WHEN tests require clean state THEN only tests marked @pytest.mark.needs_clean_state SHALL trigger driver.reset()
4. WHEN fixture optimization is active THEN tests SHALL maintain proper isolation for state-dependent operations

### Requirement 4: Lasso Selection Efficiency

**User Story:** As a developer, I want lasso selection tests to use fewer pointer events while maintaining geometric coverage, so that selection tests execute faster without losing validation quality.

#### Acceptance Criteria

1. WHEN lasso selection is tested THEN default polygon SHALL use ~40 vertices instead of 110 vertices
2. WHEN geometric coverage is validated THEN polygon SHALL still include convex, concave, and edge-crossing test cases
3. WHEN comprehensive testing is required THEN a separate @pytest.mark.slow test SHALL maintain 110-vertex polygon for nightly/full runs
4. WHEN pointer event reduction is applied THEN selection logic validation SHALL remain identical to current coverage

### Requirement 5: Upload Test Optimization

**User Story:** As a developer, I want upload tests optimized while maintaining realistic user behavior simulation, so that upload validation remains authentic but more efficient.

#### Acceptance Criteria

1. WHEN upload functionality is tested THEN existing manual picker workflow SHALL be maintained for realistic user simulation
2. WHEN pixel-sampling verification occurs THEN WebView branches that cannot be sampled SHALL be skipped to avoid unnecessary delays
3. WHEN upload test executes THEN any deterministic wait opportunities SHALL be identified and optimized without changing user flow
4. WHEN upload flow completes THEN post-upload activity verification SHALL remain identical to current validation

### Requirement 6: Network Isolation

**User Story:** As a developer, I want all external network dependencies removed from tests, so that network latency doesn't affect test runtime.

#### Acceptance Criteria

1. WHEN tests execute THEN zero external network requests SHALL be made during normal operation
2. WHEN network speed estimation is needed THEN system SHALL use hardcoded local profile values with PMTiles data
3. WHEN external connectivity pings exist THEN they SHALL be removed and replaced with local alternatives
4. WHEN network isolation is enforced THEN all tests SHALL complete successfully in airplane mode environment

### Requirement 7: Persistent Infrastructure Integration

**User Story:** As a developer, I want optimized tests to work seamlessly with existing persist_tests.sh infrastructure, so that persistence benefits are maintained without duplication.

#### Acceptance Criteria

1. WHEN existing persist_tests.sh is active THEN optimized tests SHALL automatically detect and use persistent services
2. WHEN persistence mode is available THEN infrastructure startup time (~70s emulator + ~16s Appium) SHALL be excluded from optimization measurements
3. WHEN persistent infrastructure fails THEN tests SHALL fallback gracefully to isolated mode
4. WHEN using persistence mode THEN no duplicate service management code SHALL be added to test framework

### Requirement 8: Test Marker Organization

**User Story:** As a developer, I want tests organized with appropriate markers for slow vs standard execution, so that comprehensive validation can be balanced with fast feedback.

#### Acceptance Criteria

1. WHEN tests are slow by design THEN they SHALL be marked with @pytest.mark.slow
2. WHEN tests require clean state THEN they SHALL be marked with @pytest.mark.needs_clean_state  
3. WHEN running standard test suite THEN slow tests SHALL be excluded by default
4. WHEN comprehensive validation is needed THEN slow tests SHALL be included in full test runs

## Non-Functional Requirements

### Code Architecture and Modularity
- **Minimal Code Addition**: Optimizations must reuse existing infrastructure and avoid adding significant new complexity
- **Backward Compatibility**: All existing test execution modes must continue to work without modification
- **Graceful Degradation**: When optimizations fail, system must fallback to current behavior automatically

### Performance
- **Deterministic Timing**: All wait operations must have defined maximum timeouts with failure logging
- **Resource Efficiency**: Memory usage during optimized test runs must not exceed baseline measurements
- **Measurement Precision**: Performance timing must be accurate to 100ms resolution for reliable comparison

### Security
- **Test Isolation**: Optimization changes must not compromise test isolation or introduce state leakage between tests
- **Data Privacy**: All optimizations must maintain existing local-only data processing requirements

### Reliability
- **Flake Rate**: No increase in test flakiness rate compared to current baseline measurements
- **Coverage Parity**: Functional coverage must remain identical with detailed mapping documentation provided
- **Error Recovery**: System must handle optimization failures gracefully with clear error reporting