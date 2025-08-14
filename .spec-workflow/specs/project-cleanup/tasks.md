# Implementation Plan

## Task Overview

This implementation plan focuses purely on consolidation: removing web infrastructure, combining data processing scripts, and simplifying testing flags. The goal is streamlining without adding new features or improvements beyond the core cleanup objectives.

## Tasks

- [x] 1. Phase 1: Preparation and Analysis
  - Analyze current project structure and identify web-specific components
  - Document dependencies to be removed vs preserved
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1_

- [x] 1.1 Analyze project dependencies and web components
  - Document all files in `web/` directory and their purposes
  - Identify web-specific imports in `server/app.py`
  - List web-only packages in requirements.txt and package.json files
  - _Requirements: 1.1, 1.6_

- [x] 2. Phase 2: Web Infrastructure Removal
  - Remove all web-related directories and files
  - Strip web-serving functionality from Flask app
  - Update project documentation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 2.1 Remove web directory and static assets
  - Files: `web/` directory (remove entirely)
  - Delete `web/index.html`, `web/main.js`, and all web assets
  - Verify no references to web assets remain in other files
  - Update any relative path references that pointed to web directory
  - _Requirements: 1.1_
  - _Leverage: Current web/ directory structure_

- [x] 2.2 Strip web-serving code from server/app.py
  - File: `server/app.py`
  - Remove Flask static_folder and static_url_path configuration
  - Remove `@app.route('/')` root endpoint and `send_from_directory` calls
  - Remove `/runs.pmtiles` endpoint since it serves web assets
  - Keep only mobile-relevant API endpoints: `/api/runs_in_area`, `/api/upload`, `/api/last_activity`, `/update_runs`
  - _Requirements: 1.2, 1.3_
  - _Leverage: Existing API endpoints_

- [x] 2.3 Update package dependencies
  - Files: `requirements.txt`, `package.json`
  - Remove Flask static file serving dependencies if any
  - Remove any web-specific JavaScript packages from package.json
  - Keep only mobile and data processing dependencies
  - _Requirements: 1.5_
  - _Leverage: Current dependency management_

- [x] 2.4 Update project documentation
  - Files: `README.md`, `CLAUDE.md`, `MOBILE_SETUP.md`
  - Remove all references to web functionality and Flask web server
  - Update build instructions to focus only on mobile app
  - Update feature descriptions to be mobile-only
  - _Requirements: 1.6_
  - _Leverage: Existing documentation structure_

- [x] 3. Phase 3: Data Processing Consolidation
  - Create unified data processing script
  - Update mobile build process
  - Remove old separate scripts
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 3.1 Create consolidated process_data.py script
  - File: `server/process_data.py`
  - Combine import logic from `import_runs.py` and PMTiles logic from `make_pmtiles.py`
  - Implement unified command-line interface with progress reporting
  - Use existing error handling from both scripts without enhancement
  - Support all existing GPS file formats (GPX, FIT, TCX)
  - _Requirements: 2.1, 2.2, 2.6_
  - _Leverage: `server/import_runs.py`, `server/make_pmtiles.py`_

- [x] 3.2 Update mobile build process to use consolidated script
  - File: `server/build_mobile.py`
  - Replace separate calls to `import_runs.py` and `make_pmtiles.py`
  - Update to call single `process_data.py` script
  - Ensure error handling works with consolidated script
  - _Requirements: 2.2, 2.3_
  - _Leverage: Existing `server/build_mobile.py`_

- [x] 3.3 Remove old separate processing scripts
  - Files: `server/import_runs.py`, `server/make_pmtiles.py`
  - Delete the old individual scripts after confirming consolidated script works
  - Update any remaining references to old script names
  - _Requirements: 2.4_

- [x] 4. Phase 4: Testing Framework Simplification
  - Simplify test runner flag processing only
  - Remove complex unused flags
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4.1 Simplify test runner flag processing
  - File: `testing/run_tests.py`
  - Modify argument parser to support only `--fast` and `--one-test` flags
  - Remove all other complex flags and their processing logic
  - Simplify flag validation and help text
  - _Requirements: 3.2, 3.3_
  - _Leverage: Existing `testing/run_tests.py`_

- [x] 5. Phase 5: Final Cleanup and Documentation
  - Clean up project structure
  - Comprehensive documentation rewrite
  - Remove temporary files
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 5.1 Clean up project root structure
  - Files: Project root directory
  - Remove any remaining web-related files or references
  - Remove `AGENTS.md` file (will be recreated later)
  - Remove any temporary analysis files created during cleanup
  - Verify mobile-focused directory structure is clean and logical
  - _Requirements: 5.1, 5.2, 5.5_

- [x] 5.2 Comprehensive README rewrite
  - File: `README.md`
  - Complete rewrite from scratch based on current mobile-only codebase
  - Focus on mobile app functionality, build process, and testing
  - Remove outdated or inconsistent information from previous iterations
  - Create clear, accurate documentation that matches the cleaned-up codebase
  - _Requirements: 5.3, 5.5_
  - _Leverage: Understanding of cleaned-up project structure_

- [x] 5.3 Update remaining project documentation
  - Files: `CLAUDE.md`, `MOBILE_SETUP.md`
  - Ensure all documentation reflects mobile-only focus
  - Update build instructions and feature descriptions
  - Verify no broken references to removed web components
  - _Requirements: 5.3, 5.5_
  - _Leverage: Updated documentation from previous phases_

- [x] 5.4 Final project validation
  - Files: Entire project
  - Run existing test suite to ensure mobile functionality works
  - Build mobile app from clean state to verify build process
  - Verify no web components remain anywhere in codebase
  - Confirm project structure is optimized and maintainable
  - _Requirements: 4.6, 5.6_
  - _Leverage: All existing testing and validation procedures_