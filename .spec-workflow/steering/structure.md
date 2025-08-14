# Structure Steering

## Project Organization

### Directory Structure

```
running-heatmap/
├── data/                          # User GPS data (git-ignored)
│   └── raw/                      # Raw GPS files (FIT/GPX/TCX/ZIP)
├── server/                       # Backend processing and build tools
│   ├── process_data.py          # Main GPS data processing pipeline
│   ├── build_mobile.py          # Mobile app build automation
│   ├── app.py                   # Flask server for mobile uploads
│   ├── requirements.txt         # Python dependencies
│   ├── *.template.*             # Mobile app generation templates
│   ├── runs.geojson            # Processed GeoJSON output
│   ├── runs.pkl                # Spatial index and metadata
│   └── runs.pmtiles            # Vector tiles for mobile rendering
├── mobile/                      # Generated Capacitor Android project
│   ├── android/                # Android-specific build files
│   ├── www/                    # Web app assets
│   ├── capacitor.config.json   # Capacitor configuration
│   └── package.json            # Node.js dependencies
├── testing/                     # Test framework and automation
│   ├── test_*.py              # Automated test suites
│   ├── run_tests.py           # Test runner with options
│   ├── helpers/               # Test utility functions
│   ├── test_data/             # Sample GPS files for testing
│   └── reports/               # Generated test reports
├── .spec-workflow/              # Specification and steering documents
│   ├── steering/              # Project steering documents
│   └── specs/                 # Feature specifications
├── package.json                 # Root project dependencies
├── README.md                    # Main project documentation
└── MOBILE_SETUP.md             # Mobile development setup guide
```

### File Naming Conventions

#### Python Files
- **Snake Case**: `process_data.py`, `build_mobile.py`, `test_upload_functionality.py`
- **Descriptive Names**: Files clearly indicate their primary function or feature
- **Module Organization**: Related functionality grouped in single modules
- **Test Prefix**: All test files start with `test_` for easy identification

#### JavaScript Files
- **Camel Case**: `main.js`, `spatialWorker.js` (for generated/template files)
- **Kebab Case**: `spatial.worker.js` (for source files following web conventions)
- **Purpose-Driven**: Names reflect primary functionality (e.g., `sw.js` for service worker)
- **Version Agnostic**: Avoid version numbers in filenames for easier maintenance

#### Android Resources
- **Lowercase with Underscores**: Following Android conventions
- **Resource Type Prefix**: `ic_` for icons, `activity_` for layouts
- **Density Suffixes**: Standard Android density qualifiers (mdpi, hdpi, etc.)
- **Configuration Qualifiers**: Standard Android configuration naming

#### Configuration Files
- **Standard Names**: `package.json`, `requirements.txt`, `capacitor.config.json`
- **Template Suffix**: `.template.*` for files that generate mobile app configurations
- **Environment Specific**: Configuration variations clearly named
- **Format Extension**: Always include appropriate file extensions

### Module Organization

#### Backend Modules (server/)
- **Single Responsibility**: Each Python file handles one major area of functionality
- **Clear Dependencies**: Import structure reflects architectural layers
- **Configuration Centralization**: Common settings and constants in dedicated modules
- **Utility Separation**: Helper functions organized by domain (GPS, spatial, mobile)

#### Mobile App Organization (mobile/www/)
- **Asset Separation**: Data, JavaScript, and static assets in separate directories
- **Minimal Structure**: Flat organization to minimize complexity
- **Template-Generated**: Most files created by build process, not hand-coded
- **Performance-Optimized**: File organization supports efficient loading and caching

#### Testing Organization (testing/)
- **Feature-Based**: Test files organized by feature area, not technical layer
- **Shared Utilities**: Common test functionality in helpers/ directory
- **Data Isolation**: Test data separate from production data
- **Report Generation**: Automated report generation with consistent formatting

### Configuration Management

#### Environment Configuration
- **Virtual Environments**: Python venv for isolated dependency management
- **Package Management**: pip for Python, npm for Node.js dependencies
- **Version Pinning**: Exact version specifications in requirements files
- **Cross-Platform**: Configuration works on Linux, WSL, and macOS

#### Build Configuration
- **Template System**: Dynamic configuration generation based on processed data
- **Environment Detection**: Automatic detection of development vs. production builds
- **Dependency Validation**: Pre-build checks for all required tools and libraries
- **Asset Management**: Automatic copying and optimization of all required assets

## Development Workflow

### Git Branching Strategy

#### Branch Types
- **main**: Production-ready code, always deployable
- **feature/***: New feature development branches
- **bugfix/***: Bug fix branches for non-critical issues
- **hotfix/***: Critical bug fixes that need immediate attention
- **experiment/***: Experimental features or architectural changes

#### Branch Naming
- **Descriptive Names**: `feature/lasso-selection-improvements`, `bugfix/mobile-memory-leak`
- **Issue References**: Include issue numbers when applicable
- **Scope Indication**: Clear indication of what area of code is affected
- **Kebab Case**: Consistent lowercase with hyphens

#### Merge Strategy
- **Feature Branches**: Merge to main with squash for clean history
- **Pull Request Required**: All changes require PR with review
- **Automated Testing**: All tests must pass before merge
- **Clean History**: Squash commits for features, preserve commits for bug fixes

### Code Review Process

#### Review Requirements
- **All Changes**: Every change requires at least one review
- **Architecture Changes**: Technical steering changes require multiple reviews
- **Test Coverage**: New features require corresponding tests
- **Documentation**: Changes affecting user workflow require documentation updates

#### Review Guidelines
- **Functionality**: Code does what it's supposed to do
- **Performance**: Changes don't negatively impact performance
- **Security**: No security vulnerabilities introduced
- **Maintainability**: Code is readable and well-organized
- **Testing**: Adequate test coverage for changes

#### Review Process
1. **Create PR**: Clear description of changes and testing performed
2. **Automated Checks**: CI/CD pipeline runs all tests and checks
3. **Human Review**: Code review focusing on logic, design, and maintainability
4. **Address Feedback**: Make requested changes or discuss alternatives
5. **Final Approval**: Reviewer approves and changes can be merged

### Testing Workflow

#### Test Categories
- **Unit Tests**: Individual function and class testing
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Full workflow testing with real data
- **Performance Tests**: Memory usage and processing speed validation

#### Test Execution
- **Local Development**: Run tests before committing changes
- **Pull Request**: Automated test execution on PR creation
- **Pre-Merge**: All tests must pass before merge approval
- **Post-Merge**: Additional regression testing on main branch

#### Test Data Management
- **Sample Data**: Curated GPS files representing common use cases
- **Generated Data**: Programmatically created test data for edge cases
- **Data Isolation**: Test data separate from user data directories
- **Cleanup Automation**: Test runs clean up temporary files and data

### Deployment Process

#### Build Pipeline
1. **Data Processing**: Run GPS processing with current dataset
2. **Mobile Build**: Generate Capacitor project with processed data
3. **Android Build**: Compile APK with all assets bundled
4. **Testing**: Run automated test suite against built APK
5. **Packaging**: Create distributable APK with version information

#### Release Management
- **Semantic Versioning**: MAJOR.MINOR.PATCH version numbering
- **Release Notes**: Comprehensive changelog for each release
- **APK Distribution**: Direct distribution without app store dependencies
- **Rollback Plan**: Ability to revert to previous working build

## Documentation Structure

### Where to Find What

#### User Documentation
- **README.md**: Quick start guide and project overview
- **MOBILE_SETUP.md**: Detailed mobile development environment setup
- **testing/README.md**: Test framework usage and guidelines
- **.spec-workflow/steering/**: Project steering documents (this structure)

#### Developer Documentation
- **Inline Comments**: Complex algorithms and business logic explanation
- **Docstrings**: All public functions with usage examples
- **Architecture Decisions**: Major design decisions documented in steering docs
- **API Documentation**: Flask server endpoints and mobile app interfaces

#### Process Documentation
- **Setup Guides**: Environment configuration and dependency installation
- **Workflow Guides**: Development, testing, and deployment procedures
- **Troubleshooting**: Common issues and their solutions
- **Contributing**: Guidelines for external contributions

### How to Update Documentation

#### Documentation Maintenance
- **Feature Changes**: Update relevant documentation when adding features
- **Process Changes**: Update workflow documentation when changing processes
- **Regular Review**: Quarterly review of documentation accuracy and completeness
- **User Feedback**: Incorporate user feedback to improve clarity and completeness

#### Documentation Standards
- **Markdown Format**: All documentation in GitHub-flavored Markdown
- **Clear Structure**: Consistent heading structure and table of contents
- **Code Examples**: Working code examples with expected output
- **Screenshot Updates**: Keep mobile app screenshots current with UI changes

### Spec Organization

#### Specification Structure
- **Feature Specs**: Located in `.spec-workflow/specs/{feature-name}/`
- **Three-Document Pattern**: requirements.md, design.md, tasks.md for each spec
- **Cross-References**: Clear links between related specs and steering documents
- **Status Tracking**: Current implementation status of each specification

#### Specification Workflow
1. **Requirements**: Define user needs and acceptance criteria
2. **Design**: Technical approach and implementation details
3. **Tasks**: Specific implementation steps with status tracking
4. **Implementation**: Code changes following the documented design
5. **Validation**: Testing and verification of implemented features

### Bug Tracking Process

#### Bug Reporting
- **GitHub Issues**: Primary bug tracking system
- **Template Usage**: Consistent bug report templates
- **Reproduction Steps**: Clear steps to reproduce the issue
- **Environment Info**: Device, Android version, dataset size, etc.

#### Bug Prioritization
- **Critical**: App crashes or data loss
- **High**: Major feature not working correctly
- **Medium**: Minor feature issues or usability problems
- **Low**: Cosmetic issues or nice-to-have improvements

#### Bug Resolution Workflow
1. **Triage**: Assess severity and assign priority
2. **Investigation**: Reproduce issue and identify root cause
3. **Planning**: Determine fix approach and effort estimate
4. **Implementation**: Develop and test fix
5. **Verification**: Confirm fix resolves issue without new problems
6. **Release**: Include fix in next appropriate release

## Team Conventions

### Communication Guidelines

#### Primary Channels
- **GitHub**: All development communication through issues and PRs
- **Documentation**: Written decisions and architectural choices in steering docs
- **Code Comments**: Technical implementation details and rationale
- **Commit Messages**: Clear, descriptive commit messages following conventional format

#### Communication Standards
- **Async-First**: Documentation and written communication preferred over meetings
- **Decision Records**: Important decisions documented with reasoning
- **Status Updates**: Regular progress updates on significant features or changes
- **Knowledge Sharing**: Technical discoveries and solutions shared with team

### Meeting Structures

#### Development Reviews
- **Weekly**: Progress review and upcoming work planning
- **Feature Kick-offs**: Design review before starting significant features
- **Retrospectives**: Regular process improvement discussions
- **Architecture Reviews**: Technical decision discussions for major changes

### Decision-Making Process

#### Technical Decisions
- **Research Phase**: Gather information and evaluate alternatives
- **Proposal Phase**: Document proposed approach with trade-offs
- **Review Phase**: Team review and feedback on proposal
- **Decision Phase**: Final decision with rationale documented
- **Implementation Phase**: Execute decided approach with monitoring

#### Process Decisions
- **Workflow Changes**: Team discussion and consensus building
- **Tool Changes**: Evaluation period with feedback collection
- **Standard Updates**: Gradual adoption with clear migration path
- **Documentation**: All process changes documented in steering docs

### Knowledge Sharing

#### Code Knowledge
- **Code Reviews**: Knowledge transfer through review process
- **Documentation**: Comprehensive inline and external documentation
- **Pair Programming**: Occasional pairing for complex features
- **Architecture Sessions**: Regular discussion of system design and patterns

#### Domain Knowledge
- **GPS Processing**: Understanding of GPS file formats and spatial operations
- **Mobile Development**: Android app development and Capacitor framework
- **Testing**: Test framework usage and effective testing strategies
- **Performance**: Optimization techniques and performance monitoring