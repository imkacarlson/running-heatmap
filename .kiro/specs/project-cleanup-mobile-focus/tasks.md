# Implementation Plan

- [x] 1. Extract mobile API endpoints to mobile/api.py
  - Create mobile/api.py with mobile API endpoints extracted from server/app.py
  - Ensure mobile/api.py contains all necessary mobile functionality
  - _Requirements: 1.1, 1.2_

- [x] 2. Consolidate data processing scripts
  - Create mobile/data_processor.py combining server/import_runs.py and server/make_pmtiles.py functionality
  - Implement unified command-line interface with --import-only, --pmtiles-only, and --all options
  - Add proper error handling and progress reporting to consolidated script
  - Test consolidated script functionality against existing data
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 3. Move and update mobile build script
  - Move server/build_mobile.py to mobile/build.py (completed - build script created in mobile/)
  - Update all file paths in mobile/build.py to work with new structure
  - Update mobile/build.py to use new consolidated data_processor.py
  - _Requirements: 4.1, 4.2, 4.4_

- [x] 4. Simplify testing framework
  - Remove unused command-line flags from testing/run_tests.py (keep only --fast and --one-test)
  - Remove flags: --mobile, --legacy, --integration, --manual-emulator, --emulator-name, --keep-emulator, --keep-app, --browser, --report-file, --verbose
  - Simplify argument parsing logic in run_tests.py
  - Update test paths and references to work with mobile/ directory structure
  - Verify all existing mobile tests continue to pass with simplified framework
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.3_

- [x] 5. Update mobile/api.py to use mobile/ paths
  - Update file paths in mobile/api.py to reference mobile/runs.pkl and mobile/runs.pmtiles
  - Update subprocess call in update_runs endpoint to use mobile/data_processor.py
  - _Requirements: 4.2, 4.4_

- [x] 6. Create mobile requirements file and update dependencies
  - Create mobile/requirements.txt based on server/requirements.txt
  - Keep only mobile-focused dependencies in mobile/requirements.txt
  - Update package.json if needed to remove web-specific dependencies
  - Test that mobile build process works with updated dependencies
  - _Requirements: 1.3_

- [x] 7. Update documentation for mobile-only focus
  - Rewrite README.md to focus exclusively on mobile development
  - Remove all web-related instructions and examples from README.md
  - Integrate relevant content from MOBILE_SETUP.md into main README.md (MOBILE_SETUP.md not found - content already integrated)
  - Update all file paths in documentation to reflect mobile/ directory structure
  - Document the new consolidated data processing workflow
  - Document the simplified testing process with only supported flags
  - _Requirements: 1.4, 1.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 8. Clean up and remove obsolete server files
  - Remove server/import_runs.py and server/make_pmtiles.py (replaced by mobile/data_processor.py)
  - Remove server/app.py (replaced by mobile/api.py)
  - Remove server/requirements.txt (replaced by mobile/requirements.txt)
  - Move server/runs.pkl to mobile/runs.pkl if it exists
  - Move any other necessary server files to mobile/ directory
  - Remove the entire server/ directory once all files are migrated
  - _Requirements: 1.1, 2.1, 4.1_

- [x] 9. Verify mobile functionality end-to-end

  - Test mobile app build process with new mobile/build.py script
  - Verify data processing works with new mobile/data_processor.py script
  - Test mobile API endpoints work correctly with updated mobile/api.py
  - Run simplified test suite to ensure all mobile functionality works
  - Test that mobile app can be built, installed, and functions correctly
  - _Requirements: 2.2, 3.5, 4.2_