# Document Grouper Tests

## Overview

Comprehensive test suite for the Document Grouper functionality using pytest.

## Test Structure

```
tests/
├── __init__.py                  # Package initialization
├── conftest.py                  # Pytest configuration and fixtures
├── test_pattern_matching.py    # Pattern matching tests
├── test_classification.py      # Classification and tagging tests
├── test_integration.py          # Integration tests
└── README.md                    # This file
```

## Running Tests

### Install Test Dependencies

```bash
cd backend
pip install -r requirements-test.txt
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_pattern_matching.py

# Run specific test
pytest tests/test_pattern_matching.py::TestPatternMatching::test_contract_detection
```

### Run Tests by Category

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Coverage

### Pattern Matching Tests (test_pattern_matching.py)

- ✅ Contract detection
- ✅ Report detection
- ✅ Meeting notes detection
- ✅ Confidential detection
- ✅ Anonymous detection
- ✅ Time period extraction

### Classification Tests (test_classification.py)

- ✅ Multi-label classification
- ✅ Confidence scores validation
- ✅ Suggested groups format
- ✅ Tag structure validation
- ✅ No duplicate tags

### Integration Tests (test_integration.py)

- ✅ Ingestion pipeline integration
- ✅ Document grouper integration

## Expected Results

```bash
$ pytest

======================== test session starts =========================
collected 13 items

tests/test_pattern_matching.py ......                          [ 46%]
tests/test_classification.py .....                             [ 84%]
tests/test_integration.py ..                                   [100%]

========================= 13 passed in 0.5s ==========================
```

## Writing New Tests

### Test File Template

```python
"""Test description."""
import pytest
from app.document_grouper import document_grouper


class TestFeatureName:
    """Test feature description."""
    
    def test_specific_functionality(self):
        """Test specific functionality description."""
        # Arrange
        content = "test content"
        
        # Act
        result = document_grouper.analyze_document(
            content=content,
            filename="test.pdf",
            mime_type="application/pdf",
        )
        
        # Assert
        assert result is not None
        assert 'tags' in result
```

### Best Practices

1. **Use descriptive test names** - `test_contract_detection` not `test_1`
2. **Follow AAA pattern** - Arrange, Act, Assert
3. **One assertion per test** - Keep tests focused
4. **Use fixtures** - For common setup/teardown
5. **Mark tests appropriately** - Use `@pytest.mark.unit` etc.

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    cd backend
    pip install -r requirements-test.txt
    pytest --cov=app --cov-report=xml
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running pytest from the backend directory:

```bash
cd backend
pytest
```

### Missing Dependencies

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

### Skipped Tests

Some integration tests may be skipped if external dependencies (Qdrant, Gemini) are not configured. This is expected.

## Performance

- Pattern matching tests: < 100ms each
- Classification tests: < 50ms each
- Integration tests: < 500ms each (if dependencies available)
- Total test suite: < 1 second

## Coverage Goals

- Pattern matching: 100%
- Classification: 100%
- Integration: 80% (some paths require external services)
- Overall: 90%+
