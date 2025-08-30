#!/usr/bin/env python3
"""
Comprehensive smoke tests for the agent-validator library and CLI.

These tests create an isolated environment, install the package, and test
real end-to-end usage scenarios including library API and CLI commands.

Usage:
    python smoke_tests.py
"""

import os
import sys
import json
import tempfile
import subprocess
import time
import venv
import shutil
from pathlib import Path
from typing import Dict, Any, Optional


class SmokeTestError(Exception):
    """Custom exception for smoke test failures."""
    pass


class AgentValidatorSmokeTester:
    """Comprehensive smoke tester with isolated environment."""
    
    def __init__(self):
        """Initialize the smoke tester."""
        self.temp_dir = None
        self.venv_path = None
        self.python_path = None
        self.pip_path = None
        self.cli_path = None
        
        # Test files (will be created in temp dir)
        self.test_schema_file = None
        self.test_input_file = None
        self.test_invalid_input_file = None
        
    def setup_isolated_environment(self):
        """Create and setup isolated virtual environment."""
        print("🔍 Creating isolated virtual environment...")
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="agent_validator_smoke_"))
        self.venv_path = self.temp_dir / "venv"
        
        # Create virtual environment
        venv.create(self.venv_path, with_pip=True)
        
        # Get paths
        if sys.platform == "win32":
            self.python_path = self.venv_path / "Scripts" / "python.exe"
            self.pip_path = self.venv_path / "Scripts" / "pip.exe"
            self.cli_path = self.venv_path / "Scripts" / "agent-validator.exe"
        else:
            self.python_path = self.venv_path / "bin" / "python"
            self.pip_path = self.venv_path / "bin" / "pip"
            self.cli_path = self.venv_path / "bin" / "agent-validator"
        
        print(f"✅ Virtual environment created at: {self.venv_path}")
        
        # Install package
        self._install_package()
        
        # Create test files
        self._create_test_files()
        
    def _install_package(self):
        """Install the package in the isolated environment."""
        print("🔍 Installing agent-validator in isolated environment...")
        
        # Get the parent directory (where pyproject.toml is)
        parent_dir = Path(__file__).parent.parent
        
        try:
            # Install in editable mode with dev dependencies
            result = subprocess.run(
                [str(self.pip_path), "install", "-e", f"{parent_dir}[dev]"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                raise SmokeTestError(f"Installation failed: {result.stderr}")
            
            print("✅ Package installed successfully")
            
        except subprocess.TimeoutExpired:
            raise SmokeTestError("Installation timed out")
        except Exception as e:
            raise SmokeTestError(f"Installation error: {e}")
    
    def _create_test_files(self):
        """Create test JSON files for CLI testing."""
        self.test_schema_file = self.temp_dir / "test_schema.json"
        self.test_input_file = self.temp_dir / "test_input.json"
        self.test_invalid_input_file = self.temp_dir / "test_invalid_input.json"
        
        # Valid schema
        schema = {
            "name": "string",
            "age": "integer",
            "email": "string",
            "is_active": "boolean",
            "tags": ["string"],
            "metadata": {
                "source": "string",
                "version": "string"
            }
        }
        
        with open(self.test_schema_file, 'w') as f:
            json.dump(schema, f, indent=2)
        
        # Valid input
        valid_input = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com",
            "is_active": True,
            "tags": ["user", "active"],
            "metadata": {
                "source": "api",
                "version": "1.0.0"
            }
        }
        
        with open(self.test_input_file, 'w') as f:
            json.dump(valid_input, f, indent=2)
        
        # Invalid input (missing required fields)
        invalid_input = {
            "name": "John Doe",
            "age": "thirty",  # Should be int
            "email": "invalid-email",  # Invalid email format
            "is_active": "yes"  # Should be boolean
        }
        
        with open(self.test_invalid_input_file, 'w') as f:
            json.dump(invalid_input, f, indent=2)
        
    def _create_test_files(self):
        """Create test JSON files for CLI testing."""
        # Valid schema
        schema = {
            "name": "string",
            "age": "integer",
            "email": "string",
            "is_active": "boolean",
            "tags": ["string"],
            "metadata": {
                "source": "string",
                "version": "string"
            }
        }
        
        with open(self.test_schema_file, 'w') as f:
            json.dump(schema, f, indent=2)
        
        # Valid input
        valid_input = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com",
            "is_active": True,
            "tags": ["user", "active"],
            "metadata": {
                "source": "api",
                "version": "1.0.0"
            }
        }
        
        with open(self.test_input_file, 'w') as f:
            json.dump(valid_input, f, indent=2)
        
        # Invalid input (missing required fields)
        invalid_input = {
            "name": "John Doe",
            "age": "thirty",  # Should be int
            "email": "invalid-email",  # Invalid email format
            "is_active": "yes"  # Should be boolean
        }
        
        with open(self.test_invalid_input_file, 'w') as f:
            json.dump(invalid_input, f, indent=2)
    
    def _run_cli_command(self, args: list, expect_success: bool = True) -> str:
        """Run a CLI command in isolated environment and return output."""
        try:
            result = subprocess.run(
                [str(self.cli_path)] + args,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if expect_success and result.returncode != 0:
                raise SmokeTestError(
                    f"CLI command failed with exit code {result.returncode}: "
                    f"args={args}, stdout={result.stdout}, stderr={result.stderr}"
                )
            
            if not expect_success and result.returncode == 0:
                raise SmokeTestError(
                    f"CLI command succeeded when it should have failed: "
                    f"args={args}, stdout={result.stdout}"
                )
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise SmokeTestError(f"CLI command timed out: args={args}")
        except FileNotFoundError:
            raise SmokeTestError(f"agent-validator CLI not found at: {self.cli_path}")
    
    def test_cli_help(self) -> None:
        """Test CLI help command."""
        print("🔍 Testing CLI help...")
        
        output = self._run_cli_command(["--help"])
        
        if "validate LLM/agent outputs against schemas" not in output:
            raise SmokeTestError("CLI help doesn't contain expected description")
        
        if "test" not in output or "logs" not in output:
            raise SmokeTestError("CLI help doesn't show expected commands")
        
        print("✅ CLI help working")
    
    def test_cli_id_generation(self) -> None:
        """Test CLI ID generation."""
        print("🔍 Testing CLI ID generation...")
        
        output = self._run_cli_command(["id"])
        
        # Should be a UUID
        if len(output) != 36 or output.count('-') != 4:
            raise SmokeTestError(f"Generated ID doesn't look like UUID: {output}")
        
        print("✅ CLI ID generation working")
    
    def test_cli_config_management(self) -> None:
        """Test CLI configuration management."""
        print("🔍 Testing CLI configuration...")
        
        # Test showing config
        output = self._run_cli_command(["config", "--show"])
        
        if "max_output_bytes" not in output:
            raise SmokeTestError("Config show doesn't display expected fields")
        
        # Test setting license key
        test_key = "test-license-key-12345"
        self._run_cli_command(["config", "--set-license-key", test_key])
        
        # Verify it was set
        output = self._run_cli_command(["config", "--show"])
        if test_key not in output:
            raise SmokeTestError("License key was not set correctly")
        
        print("✅ CLI configuration working")
    
    def test_cli_validation_success(self) -> None:
        """Test CLI validation with valid input."""
        print("🔍 Testing CLI validation (success)...")
        
        output = self._run_cli_command([
            "test", 
            str(self.test_schema_file), 
            str(self.test_input_file),
            "--mode", "COERCE"
        ])
        
        if "Validation successful" not in output:
            raise SmokeTestError(f"Validation should have succeeded: {output}")
        
        # Check that output contains the validated data
        if "John Doe" not in output:
            raise SmokeTestError("Validated output doesn't contain expected data")
        
        print("✅ CLI validation (success) working")
    
    def test_cli_validation_failure(self) -> None:
        """Test CLI validation with invalid input."""
        print("🔍 Testing CLI validation (failure)...")
        
        # This should fail with exit code 2
        try:
            self._run_cli_command([
                "test", 
                str(self.test_schema_file), 
                str(self.test_invalid_input_file),
                "--mode", "STRICT"
            ], expect_success=False)
        except SmokeTestError as e:
            if "exit code 2" not in str(e):
                raise SmokeTestError(f"Expected validation failure with exit code 2: {e}")
        
        print("✅ CLI validation (failure) working")
    
    def test_cli_logs(self) -> None:
        """Test CLI logs command."""
        print("🔍 Testing CLI logs...")
        
        # Test logs command (should work even if no logs exist)
        output = self._run_cli_command(["logs", "-n", "5"])
        
        # Should either show logs or "No logs found"
        if "No logs found" not in output and "correlation_id" not in output:
            raise SmokeTestError("Logs command output unexpected")
        
        print("✅ CLI logs working")
    
    def test_cli_cloud_logs(self) -> None:
        """Test CLI cloud logs command."""
        print("🔍 Testing CLI cloud logs...")
        
        # This might fail if no license key or server not running, which is expected
        try:
            output = self._run_cli_command(["cloud-logs", "-n", "5"])
            print("✅ CLI cloud logs working (server available)")
        except SmokeTestError as e:
            if "No license key configured" in str(e) or "Cannot connect" in str(e):
                print("⚠️  CLI cloud logs not available (expected if no license/server)")
            else:
                raise e
    
    def test_library_imports(self) -> None:
        """Test library imports and basic functionality in isolated environment."""
        print("🔍 Testing library imports in isolated environment...")
        
        try:
            # Test all main imports using the isolated Python
            result = subprocess.run(
                [str(self.python_path), "-c", """
import sys
from agent_validator import validate, Schema, ValidationError, ValidationMode, Config, SchemaError, CloudLogError

# Test basic schema creation
schema = Schema({
    "name": str,
    "age": int,
    "email": str
})

# Test basic validation
test_data = {
    "name": "John",
    "age": 30,
    "email": "john@example.com"
}

result = validate(test_data, schema, mode=ValidationMode.STRICT)

if result["name"] != "John" or result["age"] != 30:
    sys.exit(1)

print("✅ All library functionality working")
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise SmokeTestError(f"Library test failed: {result.stderr}")
            
            print("✅ All library imports and functionality working")
            
        except Exception as e:
            raise SmokeTestError(f"Library functionality failed: {e}")
    
    def test_library_validation_modes(self) -> None:
        """Test different validation modes in isolated environment."""
        print("🔍 Testing validation modes in isolated environment...")
        
        try:
            # Test validation modes using the isolated Python
            result = subprocess.run(
                [str(self.python_path), "-c", """
import sys
from agent_validator import validate, Schema, ValidationMode, ValidationError

schema = Schema({
    "age": int,
    "is_active": bool,
    "score": float
})

# Test strict mode (should fail)
test_data = {
    "age": "30",
    "is_active": "true",
    "score": "42.5"
}

try:
    validate(test_data, schema, mode=ValidationMode.STRICT)
    sys.exit(1)  # Should have failed
except ValidationError:
    pass  # Expected

# Test coerce mode (should succeed)
result = validate(test_data, schema, mode=ValidationMode.COERCE)

if not isinstance(result["age"], int) or result["age"] != 30:
    sys.exit(1)

if not isinstance(result["is_active"], bool) or result["is_active"] is not True:
    sys.exit(1)

if not isinstance(result["score"], float) or result["score"] != 42.5:
    sys.exit(1)

print("✅ Validation modes working")
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise SmokeTestError(f"Validation modes test failed: {result.stderr}")
            
            print("✅ Validation modes working")
            
        except Exception as e:
            raise SmokeTestError(f"Validation modes test failed: {e}")
    
    def test_library_error_handling(self) -> None:
        """Test library error handling in isolated environment."""
        print("🔍 Testing error handling in isolated environment...")
        
        try:
            # Test error handling using the isolated Python
            result = subprocess.run(
                [str(self.python_path), "-c", """
import sys
from agent_validator import validate, Schema, ValidationError, ValidationMode

schema = Schema({
    "name": str,
    "age": int
})

# Test with missing required field
test_data = {"name": "John"}

try:
    validate(test_data, schema, mode=ValidationMode.STRICT)
    sys.exit(1)  # Should have failed
except ValidationError as e:
    if "age" not in str(e):
        sys.exit(1)  # Error message should mention missing field

# Test with wrong type
test_data = {"name": "John", "age": "not_a_number"}

try:
    validate(test_data, schema, mode=ValidationMode.STRICT)
    sys.exit(1)  # Should have failed
except ValidationError:
    pass  # Expected

print("✅ Error handling working")
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise SmokeTestError(f"Error handling test failed: {result.stderr}")
            
            print("✅ Error handling working")
            
        except Exception as e:
            raise SmokeTestError(f"Error handling test failed: {e}")
    
    def test_library_config(self) -> None:
        """Test library configuration in isolated environment."""
        print("🔍 Testing library configuration in isolated environment...")
        
        try:
            # Test configuration using the isolated Python
            result = subprocess.run(
                [str(self.python_path), "-c", """
import sys
from agent_validator import Config

# Test default config
config = Config()

if config.max_output_bytes != 131072:
    sys.exit(1)

if config.max_str_len != 8192:
    sys.exit(1)

# Test custom config
custom_config = Config(
    max_output_bytes=65536,
    max_str_len=4096,
    log_to_cloud=True,
    license_key="test-key"
)

if custom_config.max_output_bytes != 65536:
    sys.exit(1)

if custom_config.license_key != "test-key":
    sys.exit(1)

print("✅ Library configuration working")
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise SmokeTestError(f"Configuration test failed: {result.stderr}")
            
            print("✅ Library configuration working")
            
        except Exception as e:
            raise SmokeTestError(f"Configuration test failed: {e}")
    
    def test_library_retry_logic(self) -> None:
        """Test library retry logic in isolated environment."""
        print("🔍 Testing retry logic in isolated environment...")
        
        try:
            # Test retry logic using the isolated Python
            result = subprocess.run(
                [str(self.python_path), "-c", """
import sys
from agent_validator import validate, Schema, ValidationMode

schema = Schema({"name": str, "age": int})

# Mock retry function that fails first, then succeeds
call_count = 0

def mock_retry_fn(prompt: str, context: dict) -> str:
    global call_count
    call_count += 1
    
    if call_count == 1:
        return '{"name": "John", "age": "invalid"}'  # Invalid
    else:
        return '{"name": "John", "age": 30}'  # Valid

# Test with retries
result = validate(
    '{"name": "John", "age": "invalid"}',
    schema,
    retry_fn=mock_retry_fn,
    retries=2,
    mode=ValidationMode.STRICT
)

if call_count != 2:
    sys.exit(1)

if result["name"] != "John" or result["age"] != 30:
    sys.exit(1)

print("✅ Retry logic working")
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise SmokeTestError(f"Retry logic test failed: {result.stderr}")
            
            print("✅ Retry logic working")
            
        except Exception as e:
            raise SmokeTestError(f"Retry logic test failed: {e}")
    
    def test_library_logging(self) -> None:
        """Test library logging functionality in isolated environment."""
        print("🔍 Testing logging functionality in isolated environment...")
        
        try:
            # Test logging using the isolated Python
            result = subprocess.run(
                [str(self.python_path), "-c", """
import sys
from agent_validator import validate, Schema, ValidationMode
from agent_validator.logging_ import get_recent_logs, clear_logs

schema = Schema({"name": str, "age": int})

# Clear existing logs
clear_logs()

# Perform a validation
result = validate(
    {"name": "John", "age": 30},
    schema,
    mode=ValidationMode.STRICT,
    context={"test": True}
)

# Check that logs were created
logs = get_recent_logs(10)

if not logs:
    sys.exit(1)

# Find our test log
test_log = None
for log in logs:
    if log.get("context", {}).get("test"):
        test_log = log
        break

if not test_log:
    sys.exit(1)

if not test_log.get("valid"):
    sys.exit(1)

if "John" not in test_log.get("output_sample", ""):
    sys.exit(1)

print("✅ Logging functionality working")
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise SmokeTestError(f"Logging test failed: {result.stderr}")
            
            print("✅ Logging functionality working")
            
        except Exception as e:
            raise SmokeTestError(f"Logging test failed: {e}")
    
    def cleanup(self):
        """Clean up temporary environment."""
        if self.temp_dir and self.temp_dir.exists():
            print("🧹 Cleaning up isolated environment...")
            try:
                shutil.rmtree(self.temp_dir)
                print("✅ Cleanup completed")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")
    
    def run_all_tests(self) -> None:
        """Run all smoke tests in isolated environment."""
        print("🚀 Starting comprehensive agent-validator smoke tests")
        print("🔒 Tests will run in isolated environment")
        print("=" * 60)
        
        try:
            # Setup isolated environment
            self.setup_isolated_environment()
            
            # Test CLI functionality
            self.test_cli_help()
            self.test_cli_id_generation()
            self.test_cli_config_management()
            self.test_cli_validation_success()
            self.test_cli_validation_failure()
            self.test_cli_logs()
            self.test_cli_cloud_logs()
            
            # Test library functionality
            self.test_library_imports()
            self.test_library_validation_modes()
            self.test_library_error_handling()
            self.test_library_config()
            self.test_library_retry_logic()
            self.test_library_logging()
            
            print("=" * 60)
            print("🎉 All smoke tests passed!")
            print("🔒 Tests ran in isolated environment - no pollution to your dev environment")
            
        except SmokeTestError as e:
            print("=" * 60)
            print(f"❌ Smoke test failed: {e}")
            sys.exit(1)
        except Exception as e:
            print("=" * 60)
            print(f"💥 Unexpected error during smoke tests: {e}")
            sys.exit(1)
        finally:
            self.cleanup()


def main():
    """Main entry point for smoke tests."""
    print("🔧 Comprehensive Agent Validator Smoke Tests")
    print("🔧 This creates an isolated environment and tests real end-to-end usage")
    
    # Create tester and run tests
    tester = AgentValidatorSmokeTester()
    tester.run_all_tests()


if __name__ == '__main__':
    main()
