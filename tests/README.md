# GMFT CLI Test Suite

Comprehensive test suite for the GMFT CLI based on gmft's test structure and notebook examples.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_discovery.py        # Component discovery tests
├── test_extract.py          # Extract command tests
├── test_bulk_extract.py     # Bulk-extract command tests
├── test_detect.py           # Detect command tests
├── test_list_components.py  # List-components command tests
├── test_integration.py      # Integration tests based on notebooks
├── test_pdf_handler.py      # PDF backend handling tests
├── test_gmft_integration.py # Tests using GMFT's actual test data
├── test_gmft_validation.py  # Validation against GMFT's expected results
└── download_gmft_data.py    # Script to download GMFT test data
```

## Running Tests

### Basic Test Run
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_extract.py

# Run specific test
pytest tests/test_extract.py::TestExtractCommand::test_extract_json_format
```

### Coverage
```bash
# Run with coverage report
pytest --cov=gmft_cli --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=gmft_cli --cov-report=html
```

### Test Categories
```bash
# Run only unit tests (exclude integration tests)
pytest -m "not integration"

# Run only integration tests
pytest -m integration

# Run tests that don't require GMFT
pytest -m "not requires_gmft"

# Run GMFT data tests (requires GMFT test data)
pytest -m gmft_data

# Run validation tests
pytest -m validation
```

### GMFT Test Data

To run tests that use GMFT's actual test PDFs and reference data:

```bash
# Download GMFT test data
python tests/download_gmft_data.py

# Check if data is available
python tests/download_gmft_data.py --check

# Run GMFT data tests
pytest tests/test_gmft_integration.py -v
pytest tests/test_gmft_validation.py -v
```

These tests ensure our CLI produces results consistent with GMFT's expected outputs.

### Using the Test Runner Script
```bash
# Basic run
python run_tests.py

# With coverage
python run_tests.py --coverage

# Include integration tests
python run_tests.py --integration

# Specific tests
python run_tests.py tests/test_extract.py
```

## Test Fixtures

### CLI Testing
- `cli_runner`: Click test runner for invoking CLI commands
- `temp_dir`: Temporary directory for test outputs

### Sample Data
- `sample_image`: Creates a simple table image
- `sample_pdf`: Creates a PDF with tables
- `multiple_pdfs`: Creates multiple PDFs for bulk testing

### Mocking
- `mock_gmft_components`: Mocks GMFT components for testing without installation

## Test Categories

### Unit Tests
- **Component Discovery**: Tests dynamic discovery of detectors and formatters
- **Command Tests**: Tests each CLI command with various options
- **Error Handling**: Tests error cases and edge conditions

### Integration Tests
- **Notebook Examples**: Reproduces workflows from GMFT notebooks
- **Real-world Scenarios**: Tests common usage patterns
- **Multi-format Output**: Tests all supported output formats

## Writing New Tests

### Adding a New Command Test
```python
def test_new_feature(cli_runner, sample_pdf, temp_dir):
    """Test description."""
    output_dir = temp_dir / "output"
    result = cli_runner.invoke(cli, [
        'command-name',
        str(sample_pdf),
        '-o', str(output_dir),
        '--option', 'value'
    ])
    
    assert result.exit_code == 0
    assert "expected output" in result.output
    assert output_dir.exists()
```

### Adding Integration Tests
```python
@pytest.mark.integration
def test_workflow(cli_runner, sample_pdf, temp_dir):
    """Test complete workflow."""
    # Test detection
    result = cli_runner.invoke(cli, ['detect', str(sample_pdf)])
    assert result.exit_code == 0
    
    # Test extraction
    result = cli_runner.invoke(cli, [
        'extract', str(sample_pdf),
        '--visualize', '--captions'
    ])
    assert result.exit_code == 0
```

## Continuous Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Multiple OS: Ubuntu, macOS, Windows
- Python versions: 3.9, 3.10, 3.11, 3.12

## Test Data

The test suite creates synthetic test data rather than relying on external files:
- Simple table images with grid patterns
- PDFs with basic table structures
- Multi-page documents
- Documents with/without keywords for filtering

This approach ensures tests are:
- Self-contained
- Reproducible
- Fast
- Don't require external dependencies