# Technical Steering

## Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raw GPS Data  │───▶│  Data Processing │───▶│  Mobile App     │
│   (FIT/GPX/TCX) │    │  (Python Server) │    │  (Capacitor)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        │
                       ┌──────────────────┐             │
                       │   Processed Data │◄────────────┘
                       │ (PMTiles/Pickle) │
                       └──────────────────┘
```

### Technology Stack Choices

#### Backend Processing (Python)
- **Python 3.10+**: Core language for GPS data processing and build automation
- **Libraries**: 
  - `gpxpy`, `fitparse` for GPS file parsing
  - `shapely`, `rtree` for spatial operations and indexing
  - `tippecanoe` (via subprocess) for PMTiles generation
  - `flask` for upload API server

#### Mobile Application (Capacitor/Android)
- **Capacitor 7.4+**: Web-to-native bridge for Android app generation
- **Vanilla JavaScript**: Core app logic without framework dependencies
- **MapLibre GL JS**: Map rendering engine with PMTiles support
- **RBush**: Client-side spatial indexing for fast queries
- **Web Workers**: Background processing for spatial operations

#### Data Storage & Formats
- **PMTiles**: Vector tile format for efficient offline map rendering
- **Pickle (Python)**: Serialized spatial index and metadata storage
- **GeoJSON**: Intermediate format for geometry processing
- **SQLite**: Future consideration for complex metadata queries

### Integration Patterns

#### Data Flow Pattern
1. **Import Stage**: Raw GPS files → Parsed coordinates → Simplified geometry
2. **Index Stage**: Geometry → Spatial index (R-tree) → Serialized storage
3. **Tile Stage**: GeoJSON → PMTiles with multiple zoom levels
4. **Mobile Stage**: PMTiles + Index → Bundled Android APK

#### Offline-First Architecture
- **Self-Contained APK**: All data and dependencies bundled at build time
- **No Runtime Dependencies**: Zero network requests after installation
- **Local Storage**: Web storage APIs for user-uploaded activities
- **Progressive Loading**: Lazy loading of map tiles based on viewport

#### Build Pipeline Integration
- **Template System**: Dynamic Android manifest and configuration generation
- **Asset Pipeline**: Automated copying of processed data to mobile assets
- **Gradle Integration**: Native Android build process with custom plugins
- **Version Management**: Coordinated versioning across Python and Android components

## Development Standards

### Coding Conventions

#### Python Code Standards
- **PEP 8 Compliance**: Standard Python formatting and naming conventions
- **Type Hints**: Full type annotation for all public functions and class methods
- **Docstring Format**: Google-style docstrings for all modules, classes, and functions
- **Import Organization**: Standard library, third-party, local imports in separate groups

#### JavaScript Code Standards
- **ES6+ Features**: Modern JavaScript with const/let, arrow functions, async/await
- **No Framework Dependencies**: Vanilla JS for maximum compatibility and performance
- **Consistent Naming**: camelCase for variables/functions, PascalCase for constructors
- **Module Pattern**: IIFE or module-based organization for namespace management

#### Android/Java Code Standards
- **Standard Android Conventions**: Follow Android Studio default formatting
- **Minimal Custom Code**: Prefer Capacitor plugins over custom Java implementation
- **Resource Organization**: Logical grouping of drawables, layouts, and values
- **Manifest Clarity**: Well-documented permissions and component declarations

### Testing Requirements

#### Python Testing Standards
- **pytest Framework**: Comprehensive test suite for all data processing functions
- **Test Coverage**: Minimum 80% coverage for core processing modules
- **Integration Tests**: End-to-end testing of full GPS processing pipeline
- **Data Validation**: Automated testing with sample GPS files from each supported format

#### Mobile Testing Standards
- **Automated UI Testing**: Selenium-based tests for core app functionality
- **Device Testing**: Validation across multiple Android versions and screen sizes
- **Performance Testing**: Memory usage and rendering performance benchmarks
- **User Journey Testing**: Complete workflows from app launch to feature usage

#### Build Process Testing
- **APK Generation**: Automated verification of successful APK builds
- **Asset Validation**: Confirmation of all required files in final package
- **Installation Testing**: Automated APK installation and basic functionality checks
- **Regression Testing**: Automated detection of breaking changes in build pipeline

### Security Guidelines

#### Data Privacy Standards
- **Local-Only Processing**: All GPS data processing happens on user's machine
- **No Network Transmission**: Zero data sent to external services during normal operation
- **Secure Storage**: Local data stored using platform-standard security mechanisms
- **Audit Trail**: Clear logging of all data processing operations for transparency

#### Mobile Security Standards
- **Android Permissions**: Minimal required permissions (storage access only)
- **Network Security**: Explicit network security config preventing accidental data transmission
- **File Access**: Scoped storage access following Android best practices
- **APK Security**: Standard Android signing and verification processes

#### Build Security Standards
- **Dependency Management**: Regular updates and vulnerability scanning of all dependencies
- **Code Review**: All changes require review before merging to main branch
- **Secret Management**: No hardcoded credentials or API keys in codebase
- **Secure Defaults**: All configurations default to most secure reasonable settings

### Performance Standards

#### Processing Performance
- **GPS Import Speed**: Process 1000+ activities in under 5 minutes on standard hardware
- **Memory Efficiency**: Peak memory usage under 2GB during large dataset processing
- **Incremental Processing**: Support for adding new activities without full reprocessing
- **Parallel Processing**: Multi-threaded operations where applicable for large datasets

#### Mobile Performance
- **App Launch Time**: Under 3 seconds on mid-range Android devices
- **Map Rendering**: 60fps scrolling and zooming with 5000+ activity dataset
- **Query Response Time**: Lasso selection results in under 500ms for typical queries
- **Memory Footprint**: Stable operation under 200MB RAM usage on device

#### Build Performance
- **Initial Build Time**: Complete APK generation in under 10 minutes
- **Incremental Build**: Template-only changes rebuild in under 2 minutes
- **Asset Optimization**: Automatic compression and optimization of all bundled assets
- **CI/CD Integration**: All tests and builds complete within 15-minute CI timeout

## Technology Choices

### Programming Languages and Versions
- **Python 3.10+**: Required for modern type hinting and performance improvements
- **JavaScript ES6+**: Modern browser features for optimal mobile web experience
- **Java 8+**: Android development compatibility requirements
- **Gradle 7+**: Current Android build system requirements

### Frameworks and Libraries

#### Core Dependencies
- **Capacitor 7.4+**: Proven web-to-native bridge with active development
- **MapLibre GL JS**: Open-source map rendering with PMTiles support
- **Flask 2+**: Lightweight web server for upload functionality
- **RBush**: High-performance spatial indexing library

#### Development Dependencies
- **pytest**: Comprehensive Python testing framework
- **selenium**: Mobile UI automation testing
- **black**: Python code formatting automation
- **eslint**: JavaScript code quality and consistency

### Development Tools
- **IDE Support**: VS Code with Python, JavaScript, and Android extensions
- **Version Control**: Git with conventional commit messages and branch protection
- **CI/CD**: GitHub Actions for automated testing and build verification
- **Documentation**: Markdown-based documentation with automated generation

### Deployment Infrastructure
- **Local Development**: WSL/Linux environment for cross-platform compatibility
- **Android SDK**: Standard Android development toolchain
- **Build Automation**: Python scripts for coordinated build process
- **Distribution**: Direct APK distribution (no app store dependencies)

## Patterns & Best Practices

### Recommended Code Patterns

#### Data Processing Patterns
- **ETL Pipeline**: Clear extract, transform, load stages for GPS data processing
- **Strategy Pattern**: Pluggable parsers for different GPS file formats
- **Builder Pattern**: Complex object construction for mobile app configuration
- **Observer Pattern**: Progress reporting during long-running processing operations

#### Mobile Development Patterns
- **Module Pattern**: JavaScript modules for feature organization and namespace management
- **Event-Driven Architecture**: DOM events and custom events for user interaction handling
- **Lazy Loading**: On-demand loading of map tiles and activity data
- **Progressive Enhancement**: Core functionality first, enhanced features as performance allows

#### Error Handling Approaches
- **Graceful Degradation**: App continues functioning with partial data when possible
- **User Feedback**: Clear error messages with actionable resolution steps
- **Logging Strategy**: Comprehensive logging for debugging without compromising privacy
- **Retry Logic**: Automatic retry with exponential backoff for transient failures

### Logging and Monitoring

#### Development Logging
- **Structured Logging**: JSON-formatted logs with consistent field naming
- **Log Levels**: DEBUG for development, INFO for production, ERROR for failures
- **Performance Metrics**: Processing time and memory usage logging for optimization
- **Privacy Compliance**: No logging of actual GPS coordinates or personal data

#### Production Monitoring
- **Application Metrics**: App launch success, feature usage, and crash reporting
- **Performance Monitoring**: Memory usage, rendering performance, and query response times
- **Build Monitoring**: Automated build success/failure notifications
- **User Feedback**: In-app feedback mechanisms for issue reporting

### Documentation Standards

#### Code Documentation
- **Inline Comments**: Complex algorithms and business logic explanation
- **API Documentation**: All public functions with parameters, return values, and examples
- **Architecture Decision Records**: Document major technical decisions with rationale
- **Setup Instructions**: Comprehensive environment setup and troubleshooting guides

#### User Documentation
- **README Structure**: Quick start, detailed setup, usage examples, troubleshooting
- **Mobile Guide**: Step-by-step mobile app usage with screenshots
- **Developer Guide**: Contribution guidelines and development workflow
- **FAQ Documentation**: Common issues and solutions based on user feedback