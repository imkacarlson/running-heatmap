# Requirements Document

## Introduction

This specification outlines a comprehensive project cleanup to transform the running heatmap application from a dual web/mobile codebase into a streamlined mobile-only solution. The cleanup involves removing all web-related infrastructure, consolidating data processing scripts, simplifying the testing framework, and optimizing the overall project structure while maintaining full mobile app functionality.

## Alignment with Product Vision

This cleanup aligns with the project's evolution toward mobile-first development, removing legacy web components that are no longer needed and creating a more maintainable, focused codebase for Android app development.

## Requirements

### Requirement 1: Web Infrastructure Removal

**User Story:** As a developer, I want all web-related components removed so that the codebase focuses exclusively on mobile app development.

#### Acceptance Criteria

1. WHEN examining the project structure THEN the `web/` directory SHALL be completely removed
2. WHEN running the application THEN no Flask web server components SHALL remain active
3. WHEN examining `server/app.py` THEN all web-serving endpoints and static file serving SHALL be removed
4. WHEN building the mobile app THEN the build process SHALL not depend on any web assets
5. WHEN reviewing imports and dependencies THEN all web-only packages SHALL be removed from requirements
6. WHEN checking project documentation THEN all references to web functionality SHALL be updated or removed

### Requirement 2: Data Processing Script Consolidation

**User Story:** As a developer, I want a single unified data processing script so that data import and PMTiles generation are handled in one streamlined workflow.

#### Acceptance Criteria

1. WHEN processing GPS data THEN a single script SHALL handle both import and PMTiles generation
2. WHEN running the consolidated script THEN it SHALL import runs from raw data AND generate PMTiles output
3. WHEN the script completes THEN both `runs.pkl` and `runs.pmtiles` files SHALL be generated
4. WHEN examining the server directory THEN `import_runs.py` and `make_pmtiles.py` SHALL be replaced by the consolidated script
5. WHEN the mobile build process runs THEN it SHALL use the consolidated script for data preparation
6. WHEN errors occur THEN comprehensive error handling SHALL provide clear feedback for both import and PMTiles stages

### Requirement 3: Testing Framework Simplification

**User Story:** As a developer, I want a simplified testing framework with only essential flags so that testing remains powerful but manageable.

#### Acceptance Criteria

1. WHEN running tests THEN only `manual_test.sh` and `test.sh` scripts SHALL be available
2. WHEN using test flags THEN only `--fast` and `--one-test` options SHALL be supported
3. WHEN examining test configuration THEN complex unused flags SHALL be removed
4. WHEN tests execute THEN all existing mobile functionality SHALL remain fully testable
5. WHEN test failures occur THEN clear error reporting SHALL be maintained
6. WHEN new tests are added THEN the simplified framework SHALL support extension

### Requirement 4: Mobile App Functionality Preservation

**User Story:** As a user, I want all mobile app features to work identically after cleanup so that no functionality is lost during the reorganization.

#### Acceptance Criteria

1. WHEN using the mobile app THEN all GPS tracking features SHALL function identically
2. WHEN drawing lasso selections THEN area selection and run filtering SHALL work as before
3. WHEN uploading GPX files THEN file processing and map display SHALL remain unchanged
4. WHEN viewing run details THEN all metadata and statistics SHALL display correctly
5. WHEN building the mobile app THEN the APK generation SHALL complete successfully
6. WHEN testing the mobile app THEN all existing test cases SHALL pass

### Requirement 5: Project Structure Optimization

**User Story:** As a developer, I want an optimized project structure so that the codebase is easier to navigate and maintain.

#### Acceptance Criteria

1. WHEN examining the project root THEN only mobile-relevant directories SHALL remain
2. WHEN building the app THEN the build process SHALL be more efficient without web dependencies
3. WHEN adding new features THEN the simplified structure SHALL provide clear organization
4. WHEN reviewing dependencies THEN package.json files SHALL contain only necessary mobile packages
5. WHEN onboarding new developers THEN the project structure SHALL be self-explanatory
6. WHEN maintaining the codebase THEN file organization SHALL follow clear mobile-app conventions

## Non-Functional Requirements

### Code Architecture and Modularity
- **Single Responsibility Principle**: Consolidated scripts shall have clearly separated concerns for data import vs PMTiles generation
- **Modular Design**: Mobile templates and build scripts shall remain isolated and reusable  
- **Dependency Management**: Remove all web-specific dependencies while preserving mobile requirements
- **Clear Interfaces**: Maintain clean separation between data processing, mobile app, and testing layers

### Performance
- Consolidated data processing shall complete in similar or better time than separate scripts
- Mobile app startup and operation shall maintain current performance levels
- Testing execution shall be faster due to simplified flag processing

### Maintainability  
- Reduced codebase complexity shall improve long-term maintainability
- Simplified testing framework shall reduce maintenance overhead
- Clear mobile-only focus shall prevent feature drift back to web components

### Reliability
- All existing mobile functionality shall remain fully operational
- Data processing reliability shall be maintained or improved
- Testing coverage shall remain comprehensive despite framework simplification