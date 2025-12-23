# Testing Guide

## Coverage Requirements

**Minimum coverage: 95%** for all active code.

## Multi-Epoch Coverage Strategy

This project uses a phased development approach (Epochs). To maintain accurate coverage metrics:

### `.coveragerc` Configuration

Placeholder apps for future epochs are **excluded** from coverage until implemented:

```ini
[run]
omit =
    # Epoch 2+ placeholder apps (remove as each epoch is implemented)
    apps/appointments/*
    apps/pets/*
    apps/store/*
    # ... etc
```

### When Starting a New Epoch

1. **Remove** the app from the `omit` list in `.coveragerc`
2. **Write tests** as you implement features (TDD)
3. **Maintain 95%+** coverage for the new app

Example: Starting Epoch 2 (Appointments + Pets)

```diff
[run]
omit =
-   apps/appointments/*
-   apps/pets/*
    apps/store/*
    apps/pharmacy/*
    # ...
```

## Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=apps --cov-report=term-missing

# Run with coverage and fail if below threshold
python -m pytest --cov=apps --cov-fail-under=95
```

## Coverage Report

Generate HTML coverage report:

```bash
python -m pytest --cov=apps --cov-report=html
open htmlcov/index.html
```

## Test Categories

### Markers

```python
@pytest.mark.slow          # Long-running tests
@pytest.mark.integration   # Integration tests
```

Skip slow tests:
```bash
python -m pytest -m "not slow"
```

## Mocking External Services

### AI/OpenRouter Client

Mock the OpenRouter API client for consistent tests:

```python
@patch('apps.ai_assistant.clients.OpenRouterClient.chat')
def test_ai_response(mock_chat):
    mock_chat.return_value = {"content": "Test response"}
    # ... test code
```

### License Validation

The license check in `apps/core/apps.py` can be bypassed in tests by setting:

```python
# In test settings or conftest.py
os.environ['SCC_LICENSE_TYPE'] = 'test'
```

## Test Database

Tests use SQLite by default (configured in `config/settings/test.py`) for speed.

## Epoch Coverage Tracking

| Epoch | Apps | Status |
|-------|------|--------|
| 1 | core, accounts, multilingual, ai_assistant, knowledge | Active - 95% required |
| 2 | appointments, pets | Excluded until implementation |
| 3 | store, pharmacy | Excluded until implementation |
| 4 | communications | Excluded until implementation |
| 5 | crm | Excluded until implementation |
| 6 | practice | Excluded until implementation |
