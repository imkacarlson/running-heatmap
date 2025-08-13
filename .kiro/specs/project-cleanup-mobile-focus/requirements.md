# Requirements Document

## Introduction

This project has grown significantly and needs a comprehensive cleanup to focus exclusively on mobile app development. The current codebase contains both web and mobile components, with the web components being legacy code that is no longer needed. The project should be streamlined to support only mobile app development while maintaining all existing mobile functionality and testing capabilities.

## Requirements

### Requirement 1

**User Story:** As a developer, I want to remove all web-related components from the project, so that the codebase is focused only on mobile development.

#### Acceptance Criteria

1. WHEN the cleanup is complete THEN the web directory SHALL be completely removed
2. WHEN the cleanup is complete THEN the Flask web server routes SHALL be removed from server/app.py
3. WHEN the cleanup is complete THEN all web-specific dependencies SHALL be removed from requirements files
4. WHEN the cleanup is complete THEN the README SHALL be updated to reflect mobile-only focus
5. WHEN the cleanup is complete THEN no references to web functionality SHALL remain in documentation

### Requirement 2

**User Story:** As a developer, I want the server scripts to be consolidated and streamlined, so that the build process is more efficient and maintainable.

#### Acceptance Criteria

1. WHEN the consolidation is complete THEN import_runs.py and make_pmtiles.py SHALL be combined into a single script
2. WHEN the consolidation is complete THEN the combined script SHALL maintain all existing functionality
3. WHEN the consolidation is complete THEN the mobile build process SHALL use the consolidated script
4. WHEN the consolidation is complete THEN the consolidated script SHALL have clear command-line options for different operations

### Requirement 3

**User Story:** As a developer, I want the testing framework to be simplified, so that I can focus on the essential testing capabilities without unnecessary complexity.

#### Acceptance Criteria

1. WHEN the testing cleanup is complete THEN only manual_test.sh and test.sh SHALL be supported as entry points
2. WHEN the testing cleanup is complete THEN only --fast and --one-test flags SHALL be supported
3. WHEN the testing cleanup is complete THEN all unused command-line flags SHALL be removed from run_tests.py
4. WHEN the testing cleanup is complete THEN the testing framework SHALL continue to work with the mobile app
5. WHEN the testing cleanup is complete THEN all existing mobile tests SHALL continue to pass

### Requirement 4

**User Story:** As a developer, I want the project structure to be reorganized for better maintainability, so that related files are grouped logically.

#### Acceptance Criteria

1. WHEN the reorganization is complete THEN the project structure SHALL be logical and intuitive
2. WHEN the reorganization is complete THEN all mobile functionality SHALL continue to work
3. WHEN the reorganization is complete THEN the testing framework SHALL be updated to work with the new structure
4. WHEN the reorganization is complete THEN build scripts SHALL be updated to work with the new structure

### Requirement 5

**User Story:** As a developer, I want the documentation to be updated to reflect the mobile-only focus, so that new developers understand the project's current scope.

#### Acceptance Criteria

1. WHEN the documentation update is complete THEN the README SHALL focus exclusively on mobile development
2. WHEN the documentation update is complete THEN all web-related instructions SHALL be removed
3. WHEN the documentation update is complete THEN the mobile setup and build process SHALL be clearly documented
4. WHEN the documentation update is complete THEN the testing process SHALL be clearly documented
5. WHEN the documentation update is complete THEN MOBILE_SETUP.md SHALL be integrated or referenced appropriately