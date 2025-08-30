# Smoke Tests for Agent Validator

This directory contains comprehensive smoke tests for the agent-validator library and CLI.

## Overview

Smoke tests verify the complete user experience from installation to usage, testing both the library API and CLI commands in various environments.

## Test Types

### 1. **Comprehensive Smoke Tests** (`smoke_tests.py`)

- **Purpose**: Complete end-to-end testing in isolated environment
- **Benefits**: Tests real installation and usage scenarios
- **Use Case**: CI/CD, production testing, development validation

### 2. **Shell Script** (`run_smoke_tests.sh`)

- **Purpose**: Bash-based isolated testing
- **Benefits**: Works in any shell environment
- **Use Case**: Unix/Linux environments, shell-based workflows

## Running Tests

### From Root Directory (Recommended)

```bash
# Run comprehensive smoke tests
python run_smoke_tests.py
```

### From This Directory

```bash
# Run comprehensive smoke tests
python smoke_tests.py

# Run shell-based tests
./run_smoke_tests.sh
```

## What Gets Tested

### CLI Functionality

- ✅ Help command and documentation
- ✅ ID generation
- ✅ Configuration management
- ✅ Validation (success and failure cases)
- ✅ Log viewing (local and cloud)
- ✅ Dashboard access

### Library Functionality

- ✅ All imports and basic functionality
- ✅ Validation modes (strict and coerce)
- ✅ Error handling and exceptions
- ✅ Configuration system
- ✅ Retry logic
- ✅ Logging functionality

### Integration Testing

- ✅ Package installation
- ✅ CLI command availability
- ✅ Cross-platform compatibility
- ✅ Environment isolation

## Environment Isolation

The isolated tests create a temporary virtual environment that:

1. **Creates** a new virtual environment in a temporary directory
2. **Installs** the package in editable mode with all dependencies
3. **Runs** comprehensive tests
4. **Cleans up** the temporary environment completely

This ensures:

- ✅ No pollution to your development environment
- ✅ Clean testing environment every time
- ✅ Tests the actual installation process
- ✅ Validates package dependencies

## Test Files

- `smoke_tests.py` - Comprehensive test suite with isolated environment
- `run_smoke_tests.sh` - Shell-based testing
- `README.md` - This documentation

## Troubleshooting

### Common Issues

1. **Permission Denied**

   ```bash
   chmod +x run_smoke_tests.sh
   ```

2. **Virtual Environment Creation Fails**

   - Ensure Python 3.9+ is installed
   - Check that `venv` module is available

3. **Package Installation Fails**

   - Ensure you're in the root directory (where `pyproject.toml` is)
   - Check that all dependencies are available

4. **CLI Not Found**
   - The isolated environment should handle this automatically
   - If running manually, ensure the package is installed

### Debug Mode

For debugging, you can run tests with verbose output:

```bash
# Run with Python debug output
python -v run_smoke_tests.py

# Run shell script with debug
bash -x smoke_tests/run_smoke_tests.sh
```

## Integration with CI/CD

These smoke tests are designed to work in CI/CD environments:

```yaml
# Example GitHub Actions workflow
- name: Run Smoke Tests
  run: |
    python run_smoke_tests.py --isolated
```

The isolated tests are particularly useful for CI/CD as they:

- Don't require pre-installed dependencies
- Test the actual installation process
- Clean up after themselves
- Provide reliable results across environments
