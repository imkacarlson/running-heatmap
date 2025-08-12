# Design Document

## Overview

This design implements a dual-tier testing strategy for the Running Heatmap mobile app, introducing lightweight smoke tests alongside the existing comprehensive emulator tests. The smoke tests will validate core system functionality in under 5 seconds, while the emulator tests continue to provide thorough end-to-end validation.

## Architecture

### Two-Tier Testing Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    Testing Framework                        │
├─────────────────────────────────────────────────────────────┤
│  Tier 1: Smoke Tests (< 5 seconds)                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Server Tests  │  │  API Tests      │  │Mobile Web   │ │
│  │   - Startup     │  │  - Endpoints    │  │Interface    │ │
│  │   - Data Load   │  │  - Responses    │  │- Loading    │ │
│  │   - Build Ready │  │  - Mobile APIs  │  │- Mobile UI  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Tier 2: Comprehensive Tests (30s - 10+ min)              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Existing Emulator Tests                    │ │
│  │  - Mobile app testing with Appium                      │ │
│  │  - End-to-end workflows                                │ │
│  │  - UI interaction validation                           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Integration with Existing Infrastructure

The smoke tests will integrate with the existing `run_tests.py` infrastructure:

```
run_tests.py
├── --smoke (new)           # Run smoke tests only
├── --core (existing)       # Run comprehensive core tests  
├── --mobile (existing)     # Run all mobile tests
└── --fast (existing)       # Skip expensive operations
```

## Components and Interfaces

### 1. Smoke Test Runner (`smoke_tests.py`)

**Purpose**: Standalone smoke test execution with minimal dependencies

**Interface**:
```python
class SmokeTestRunner:
    def run_all_smoke_tests() -> SmokeTestResult
    def run_server_tests() -> TestResult
    def run_api_tests() -> TestResult  
    def run_web_tests() -> TestResult
```

**Dependencies**: 
- `requests` for HTTP testing
- `selenium` (headless) for basic web validation
- Standard library only (no Appium, no emulator)

### 2. Server Smoke Tests (`test_smoke_server.py`)

**Purpose**: Validate Flask server startup and data loading

**Test Cases**:
- Server startup within timeout
- Sample data loading (small test dataset)
- Basic route accessibility
- Database/pickle file integrity

**Sample Test Structure**:
```python
@pytest.mark.smoke
class TestServerSmoke:
    def test_server_starts_successfully(self):
        # Start server, verify it responds within 3 seconds
        
    def test_sample_data_loads(self):
        # Verify runs.pkl can be loaded and contains valid data
        
    def test_spatial_index_builds(self):
        # Verify rtree index builds without errors
```

### 3. API Smoke Tests (`test_smoke_api.py`)

**Purpose**: Validate key API endpoints return expected responses

**Test Cases**:
- `/` returns HTML content
- `/api/last_activity` returns JSON
- `/api/runs_in_area` accepts POST and returns valid structure
- `/runs.pmtiles` serves file (if exists)

**Sample Test Structure**:
```python
@pytest.mark.smoke  
class TestAPISmoke:
    def test_root_endpoint_serves_html(self):
        # GET / returns 200 with HTML content
        
    def test_api_endpoints_respond(self):
        # Test key API endpoints return expected status codes
        
    def test_api_data_structure(self):
        # Verify API responses have expected JSON structure
```

### 4. Mobile Web Interface Smoke Tests (`test_smoke_web.py`)

**Purpose**: Validate mobile web interface loads without critical errors and renders properly for mobile app packaging

**Test Cases**:
- HTML page loads successfully in mobile viewport
- JavaScript executes without console errors
- Map container element exists and is properly sized
- Required external libraries load (MapLibre, PMTiles)
- Mobile-specific UI elements are present and functional
- Touch/gesture event handlers are properly attached
- Responsive design works for mobile screen sizes

**Sample Test Structure**:
```python
@pytest.mark.smoke
class TestWebSmoke:
    def test_mobile_page_loads_without_errors(self):
        # Load page in headless browser with mobile viewport, check for JS errors
        
    def test_mobile_map_container_exists(self):
        # Verify #map element is present and properly sized for mobile
        
    def test_mobile_ui_elements_present(self):
        # Verify mobile-specific controls and interface elements
        
    def test_external_libraries_load(self):
        # Verify MapLibre and PMTiles are available for mobile packaging
```

### 5. Enhanced Test Runner Integration

**Modified `run_tests.py`**:
- Add `--smoke` flag for smoke tests only
- Add smoke test discovery and execution
- Maintain existing emulator test functionality
- Provide clear command help and documentation

**Command Structure**:
```bash
# New smoke test commands
python run_tests.py --smoke                    # Run all smoke tests (< 5s)
python run_tests.py --smoke --server           # Server tests only
python run_tests.py --smoke --api              # API tests only  
python run_tests.py --smoke --web              # Web tests only

# Existing commands remain unchanged
python run_tests.py --core --fast              # Existing emulator tests
python run_tests.py --mobile                   # Full mobile test suite
```

## Data Models

### Test Result Models

```python
@dataclass
class SmokeTestResult:
    total_tests: int
    passed: int
    failed: int
    execution_time: float
    failures: List[TestFailure]
    
@dataclass  
class TestFailure:
    test_name: str
    error_message: str
    component: str  # 'server', 'api', 'web'
```

### Test Configuration

```python
@dataclass
class SmokeTestConfig:
    server_timeout: int = 3  # seconds
    api_timeout: int = 2     # seconds  
    web_timeout: int = 3     # seconds
    test_data_path: str = "testing/test_data"
    headless_browser: bool = True
```

## Error Handling

### Failure Categories and Responses

1. **Server Startup Failures**:
   - Clear error message indicating server component failure
   - Suggestion to check dependencies and port availability
   - Exit code 1 for CI/CD integration

2. **API Response Failures**:
   - Specific endpoint and expected vs actual response
   - HTTP status code and response body details
   - Suggestion to run full server tests

3. **Web Interface Failures**:
   - JavaScript console errors with line numbers
   - Missing DOM elements with selectors
   - External library loading failures with network details

4. **Data Loading Failures**:
   - File path and permission issues
   - Data format validation errors
   - Suggestion to run data pipeline tests

### Graceful Degradation

- If server fails to start, skip API and web tests
- If sample data missing, create minimal test dataset
- If external dependencies unavailable, skip related tests
- Always provide actionable error messages

## Testing Strategy

### Smoke Test Execution Flow

```
1. Environment Check (0.5s)
   ├── Python dependencies available
   ├── Test data present
   └── Port availability

2. Server Tests (2s)
   ├── Start Flask server
   ├── Load sample data  
   ├── Build spatial index
   └── Verify basic routes

3. API Tests (1.5s)
   ├── Test key mobile API endpoints
   ├── Validate response formats for mobile consumption
   └── Check error handling for mobile scenarios

4. Mobile Web Interface Tests (1s)
   ├── Load page in headless browser with mobile viewport
   ├── Check for JS errors that would affect mobile app
   ├── Verify mobile-optimized DOM structure
   ├── Test external library loading for mobile packaging
   └── Validate responsive design for mobile screens

5. Cleanup (< 0.5s)
   ├── Stop test server
   ├── Close browser
   └── Generate report
```

### Integration with Existing Tests

- Smoke tests run independently of emulator tests
- Shared test data and utilities where appropriate
- Same reporting format and CI/CD integration
- Clear documentation on when to use each tier

### Performance Targets

- **Total smoke test execution**: < 5 seconds
- **Individual test categories**: < 2 seconds each
- **Memory usage**: < 100MB (vs 1GB+ for emulator tests)
- **No external dependencies**: No Android SDK, emulator, or Appium required

## Implementation Phases

### Phase 1: Core Infrastructure
- Create smoke test runner framework
- Implement server startup tests
- Basic API endpoint validation
- Integration with existing test runner

### Phase 2: Web Interface Testing  
- Headless browser setup
- JavaScript error detection
- DOM structure validation
- External library loading tests

### Phase 3: Enhanced Integration
- Command-line interface improvements
- Reporting and documentation
- CI/CD integration
- Performance optimization

### Phase 4: Documentation and Training
- Update testing documentation
- Create decision matrix for test selection
- Team training on dual-tier approach
- Monitoring and metrics collection