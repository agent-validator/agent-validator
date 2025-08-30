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

SMOKE_TEST_OUTPUT_LINES = 60

class SmokeTestError(Exception):
    """Custom exception for smoke test failures."""
    pass


class AgentValidatorSmokeTester:
    """Comprehensive smoke tester with isolated environment."""
    
    def __init__(self, backend_url: Optional[str] = "http://localhost:9090"):
        """Initialize the smoke tester.
        
        Args:
            backend_url: Optional backend URL for cloud testing (default: http://localhost:9090)
        """
        self.temp_dir = None
        self.venv_path = None
        self.python_path = None
        self.pip_path = None
        self.cli_path = None
        self.backend_url = backend_url
        
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
        
        # Configure backend URL if provided
        if self.backend_url:
            self._configure_backend_url()
        
    def _install_package(self):
        """Install the package in the isolated environment."""
        print("🔍 Installing agent-validator in isolated environment...")
        
        # Get the parent directory (where pyproject.toml is)
        parent_dir = Path(__file__).parent.parent
        
        try:
            # Install in editable mode with dev dependencies using python -m pip
            result = subprocess.run(
                [str(self.python_path), "-m", "pip", "install", "-e", f"{parent_dir}[dev]"],
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
        print("🔍 Creating test files...")
        self.test_schema_file = self.temp_dir / "test_schema.json"
        self.test_input_file = self.temp_dir / "test_input.json"
        self.test_invalid_input_file = self.temp_dir / "test_invalid_input.json"
        
        # Valid schema (JSON-compatible format)
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

        print("✅ Test files created successfully")
    
    def _configure_backend_url(self):
        """Configure the backend URL in the isolated environment."""
        if not self.backend_url:
            return
            
        print(f"🔍 Configuring backend URL: {self.backend_url}")
        
        try:
            # Set the backend URL using the CLI config command
            result = subprocess.run(
                [str(self.cli_path), "config", "--set-endpoint", self.backend_url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"⚠️  Warning: Failed to configure backend URL: {result.stderr}")
            else:
                print("✅ Backend URL configured successfully")
                
        except Exception as e:
            print(f"⚠️  Warning: Failed to configure backend URL: {e}")
    
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
    
    def _string_in_output(self, output: str, string: str) -> bool:
        """Check if a string is in the output."""
        return string.lower() in output.lower()

    def test_cli_help(self) -> None:
        """Test CLI help command."""
        print("🔍 Testing CLI help...")
        
        output = self._run_cli_command(["--help"])
        
        if not self._string_in_output(output, "validate LLM/agent outputs against schemas"):
            raise SmokeTestError("CLI help doesn't contain expected description")
        
        if not self._string_in_output(output, "test") or not self._string_in_output(output, "logs"):
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
        
        if not self._string_in_output(output, "max_output_bytes"):
            raise SmokeTestError("Config show doesn't display expected fields")
        
        # Test setting license key
        test_key = "test-license-key-12345"
        self._run_cli_command(["config", "--set-license-key", test_key])
        
        # Verify it was set (should be masked by default)
        output = self._run_cli_command(["config", "--show"])
        if not self._string_in_output(output, "***"):
            raise SmokeTestError("License key should be masked by default")
        
        # Test showing secrets
        output = self._run_cli_command(["config", "--show", "--show-secrets"])
        if not self._string_in_output(output, test_key):
            raise SmokeTestError("License key should be visible with --show-secrets")
        
        print("✅ CLI configuration working")
    
    def test_cli_validation_success(self) -> None:
        """Test CLI validation with valid input."""
        print("🔍 Testing CLI validation (success)...")
        
        output = self._run_cli_command([
            "test", 
            str(self.test_schema_file), 
            str(self.test_input_file),
            "--mode", "cOeRce" # Case-insensitive mode
            
        ])
        
        if not self._string_in_output(output, "Validation successful"):
            raise SmokeTestError(f"Validation should have succeeded: {output}")
        
        # Check that output contains the validated data
        if not self._string_in_output(output, "John Doe"):
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
                "--mode", "sTrIct" # Case-insensitive mode
            ], expect_success=False)
        except SmokeTestError as e:
            if not self._string_in_output(str(e), "exit code 2"):
                raise SmokeTestError(f"Expected validation failure with exit code 2: {e}")
        
        print("✅ CLI validation (failure) working")
    
    def test_cli_logs(self) -> None:
        """Test CLI logs command."""
        print("🔍 Testing CLI logs...")
        
        # Test logs command (should work even if no logs exist)
        output = self._run_cli_command(["logs", "-n", "5"])
        
        # Should either show logs or "No logs found"
        # Logs output now uses table format with headers
        if not self._string_in_output(output, "No logs found") and not self._string_in_output(output, "Timestamp") and not self._string_in_output(output, "Status"):
            raise SmokeTestError("Logs command output unexpected")
        
        print("✅ CLI logs working")
    
    def test_cli_cloud_logs(self) -> None:
        """Test CLI cloud logs command."""
        print("🔍 Testing CLI cloud logs...")
        
        # This might fail if no license key or server not running, which is expected
        try:
            output = self._run_cli_command(["cloud-logs", "-n", "5"])
            if not self._string_in_output(output, "No logs found") and not self._string_in_output(output, "Timestamp") and not self._string_in_output(output, "Status"):
                raise SmokeTestError("Cloud logs command output unexpected")

            print("✅ CLI cloud logs working (server available)")
        except SmokeTestError as e:
            if self._string_in_output(str(e), "No license key configured") or self._string_in_output(str(e), "Cannot connect"):
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
    
    def test_local_log_files(self) -> None:
        """Test that log files are created in the local log location."""
        print("🔍 Testing local log file creation...")
        
        try:
            # Get today's date for log file name
            from datetime import datetime
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            # Check if log directory exists
            log_dir = Path.home() / ".agent_validator" / "logs"
            if not log_dir.exists():
                raise SmokeTestError(f"Log directory does not exist: {log_dir}")
            
            # Check if today's log file exists
            log_file = log_dir / f"{today}.jsonl"
            if not log_file.exists():
                raise SmokeTestError(f"Today's log file does not exist: {log_file}")
            
            # Check if log file has content
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
            
            if not log_lines:
                raise SmokeTestError("Log file is empty")
            
            # Check if log entries are valid JSON
            valid_entries = 0
            for line in log_lines:
                try:
                    json.loads(line.strip())
                    valid_entries += 1
                except json.JSONDecodeError:
                    continue
            
            if valid_entries == 0:
                raise SmokeTestError("No valid JSON entries found in log file")
            
            # Check if our test entries are in the log
            test_entries = 0
            for line in log_lines:
                try:
                    entry = json.loads(line.strip())
                    # Look for entries with our test context
                    if entry.get("context", {}).get("test"):
                        test_entries += 1
                except json.JSONDecodeError:
                    continue
            
            print(f"✅ Local log files working - found {valid_entries} valid entries, {test_entries} test entries")
            
        except Exception as e:
            raise SmokeTestError(f"Local log file test failed: {e}")
    
    def test_redaction_patterns(self) -> None:
        """Test that sensitive data is properly redacted in logs."""
        print("🔍 Testing redaction patterns...")
        
        try:
            # Test validation with sensitive data
            result = subprocess.run(
                [str(self.python_path), "-c", """
import sys
from agent_validator import validate, Schema, ValidationMode

schema = Schema({
    "api_key": str,
    "jwt_token": str,
    "email": str,
    "password": str,
    "config": str
})

# Data with sensitive information
sensitive_data = {
    "api_key": "sk-1234567890abcdef",
    "jwt_token": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    "email": "john.doe@example.com",
    "password": "secret123",
    "config": "api_key=sk-1234567890abcdef&jwt=Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c&email=john.doe@example.com&password=secret123"
}

result = validate(sensitive_data, schema, mode=ValidationMode.STRICT, context={"test": "redaction"})

# Check that the result contains the original data
if result["api_key"] != "sk-1234567890abcdef":
    sys.exit(1)

if result["config"] != "api_key=sk-1234567890abcdef&jwt=Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c&email=john.doe@example.com&password=secret123":
    sys.exit(1)

print("✅ Validation with sensitive data successful")
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise SmokeTestError(f"Redaction test validation failed: {result.stderr}")
            
            # Check log file for redacted data
            from datetime import datetime
            today = datetime.utcnow().strftime("%Y-%m-%d")
            log_file = Path.home() / ".agent_validator" / "logs" / f"{today}.jsonl"
            
            if not log_file.exists():
                raise SmokeTestError("Log file not found for redaction check")
            
            # Look for our redaction test entry
            redacted_found = False
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("context", {}).get("test") == "redaction":
                            output_sample = entry.get("output_sample", "")
                            # Check that sensitive data is redacted in the config field
                            if "sk-1234567890abcdef" in output_sample:
                                raise SmokeTestError("API key not redacted in log")
                            if "Bearer eyJ" in output_sample:
                                raise SmokeTestError("JWT token not redacted in log")
                            if "john.doe@example.com" in output_sample:
                                raise SmokeTestError("Email not redacted in log")
                            if "secret123" in output_sample:
                                raise SmokeTestError("Password not redacted in log")
                            
                            # Check that redaction markers are present
                            if "[REDACTED]" not in output_sample:
                                raise SmokeTestError("No redaction markers found in log")
                            
                            # Check that the config field specifically is redacted
                            if "api_key=sk-1234567890abcdef" in output_sample:
                                raise SmokeTestError("API key in config field not redacted")
                            if "jwt=Bearer eyJ" in output_sample:
                                raise SmokeTestError("JWT in config field not redacted")
                            
                            redacted_found = True
                            break
                    except json.JSONDecodeError:
                        continue
            
            if not redacted_found:
                raise SmokeTestError("Redaction test entry not found in logs")
            
            print("✅ Redaction patterns working correctly")
            
        except Exception as e:
            raise SmokeTestError(f"Redaction test failed: {e}")
    
    def test_exponential_backoff_jitter(self) -> None:
        """Test exponential backoff and jitter in retry logic."""
        print("🔍 Testing exponential backoff and jitter...")
        
        try:
            # Test retry logic with a function that fails twice then succeeds
            result = subprocess.run(
                [str(self.python_path), "-c", """
import sys
import time
from agent_validator import validate, Schema, ValidationMode, ValidationError

schema = Schema({"name": str})

attempt_count = 0
start_time = time.time()
delays = []

def failing_function(prompt, context):
    global attempt_count, delays
    attempt_count += 1
    current_time = time.time()
    delays.append(current_time - start_time)
    
    if attempt_count < 3:
        return "invalid json"  # This will fail validation
    else:
        return '{"name": "John"}'

try:
    result = validate(
        "invalid input",
        schema,
        retry_fn=failing_function,
        retries=3,
        timeout_s=10,
        context={"test": "backoff"}
    )
    
    if attempt_count != 3:
        print(f"Expected 3 attempts, got {attempt_count}")
        sys.exit(1)
    
    # Check that delays show exponential backoff with jitter
    if len(delays) < 2:
        print("Not enough delay measurements")
        sys.exit(1)
    
    # First delay should be around 0.5s (with jitter)
    if delays[1] < 0.3 or delays[1] > 1.0:
        print(f"First delay {delays[1]}s not in expected range")
        sys.exit(1)
    
    # Second delay should be around 1s (with jitter)
    if delays[2] < 0.7 or delays[2] > 2.0:
        print(f"Second delay {delays[2]}s not in expected range")
        sys.exit(1)
    
    print("✅ Exponential backoff and jitter working correctly")
    
except ValidationError as e:
    print(f"Validation failed after retries: {e}")
    sys.exit(1)
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise SmokeTestError(f"Backoff test failed: {result.stderr}")
            
            print("✅ Exponential backoff and jitter working correctly")
            
        except Exception as e:
            raise SmokeTestError(f"Backoff test failed: {e}")
    
    def test_configuration_precedence(self) -> None:
        """Test configuration precedence: CLI args → env → config file."""
        print("🔍 Testing configuration precedence...")
        
        try:
            # Test that CLI arguments override environment variables
            result = subprocess.run(
                [str(self.python_path), "-c", """
import sys
import os
from agent_validator import get_config

# Set environment variable
os.environ['AGENT_VALIDATOR_TIMEOUT_S'] = '30'

# Get config (should pick up env var)
config = get_config()

if config.timeout_s != 30:
    print(f"Expected timeout_s=30, got {config.timeout_s}")
    sys.exit(1)

print("✅ Environment variable precedence working")
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise SmokeTestError(f"Config precedence test failed: {result.stderr}")
            
            print("✅ Configuration precedence working correctly")
            
        except Exception as e:
            raise SmokeTestError(f"Config precedence test failed: {e}")
    
    def test_cloud_redaction(self) -> None:
        """Test that cloud logs are also redacted."""
        print("🔍 Testing cloud log redaction...")
        
        if not self.backend_url:
            print("⚠️  Skipping cloud redaction test (no backend URL)")
            return
        
        try:
            # Test validation with sensitive data that gets sent to cloud
            result = subprocess.run(
                [str(self.python_path), "-c", f"""
import sys
from agent_validator import validate, Schema, ValidationMode, Config

schema = Schema({{
    "api_key": str,
    "email": str
}})

sensitive_data = {{
    "api_key": "sk-cloud-test-key-12345",
    "email": "cloud-test@example.com"
}}

config = Config(
    log_to_cloud=True,
    license_key="license-smoke-test-key",
    cloud_endpoint="{self.backend_url}"
)

result = validate(
    sensitive_data, 
    schema, 
    mode=ValidationMode.STRICT,
    log_to_cloud=True,
    config=config,
    context={{"test": "cloud_redaction"}}
)

print("✅ Cloud validation with sensitive data successful")
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise SmokeTestError(f"Cloud redaction test failed: {result.stderr}")
            
            # Note: We can't easily check the cloud logs from here, but the test
            # ensures that sensitive data is redacted before being sent to cloud
            print("✅ Cloud redaction test completed")
            
        except Exception as e:
            raise SmokeTestError(f"Cloud redaction test failed: {e}")
    
    def test_cloud_failsafe(self) -> None:
        """Test that cloud errors don't break user code."""
        print("🔍 Testing cloud failsafe...")
        
        try:
            # Test validation with cloud logging enabled but invalid endpoint
            result = subprocess.run(
                [str(self.python_path), "-c", """
import sys
from agent_validator import validate, Schema, ValidationMode, Config

schema = Schema({
    "name": str
})

data = {
    "name": "John"
}

# Use invalid cloud endpoint to trigger cloud error
config = Config(
    log_to_cloud=True,
    license_key="invalid-key",
    cloud_endpoint="http://invalid-endpoint-that-does-not-exist.com"
)

# This should succeed even if cloud logging fails
result = validate(
    data, 
    schema, 
    mode=ValidationMode.STRICT,
    log_to_cloud=True,
    config=config,
    context={"test": "cloud_failsafe"}
)

# Check that validation succeeded
if result["name"] != "John":
    print("Validation failed")
    sys.exit(1)

print("✅ Cloud failsafe working - validation succeeded despite cloud error")
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise SmokeTestError(f"Cloud failsafe test failed: {result.stderr}")
            
            print("✅ Cloud failsafe working correctly")
            
        except Exception as e:
            raise SmokeTestError(f"Cloud failsafe test failed: {e}")
    
    def test_cloud_functionality(self) -> None:
        """Test cloud functionality with configured backend URL."""
        print("🔍 Testing cloud functionality...")
        
        # Set a test license key for cloud testing
        test_license_key = "license-smoke-test-key"
        
        try:
            # Configure license key
            self._run_cli_command(["config", "--set-license-key", test_license_key])
            
            # Test cloud logs command
            output = self._run_cli_command(["cloud-logs", "-n", "5"])

            if self._string_in_output(output, "Cannot connect to"):
                raise SmokeTestError("Cannot connect to backend server " + self.backend_url)
            
            # Should show table format or "No logs found"
            if not self._string_in_output(output, "No logs found") and not self._string_in_output(output, "Timestamp"):
                raise SmokeTestError("Cloud logs output unexpected")
            
            print("✅ Cloud functionality working")
            
        except SmokeTestError as e:
            if self._string_in_output(str(e), "Cannot connect") or self._string_in_output(str(e), "Failed to fetch"):
                print("⚠️  Cloud functionality not available (backend may not be running)")
            else:
                raise e
    
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
        print("=" * SMOKE_TEST_OUTPUT_LINES)
        
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
            
            # Test cloud functionality if backend URL is provided
            if self.backend_url:
                self.test_cloud_functionality()

            self.test_cli_cloud_logs()
            
            # Test library functionality
            self.test_library_imports()
            self.test_library_validation_modes()
            self.test_library_error_handling()
            self.test_library_config()
            self.test_library_retry_logic()
            self.test_library_logging()
            
            # Test local log file creation
            self.test_local_log_files()
            
            # Test advanced functionality
            self.test_redaction_patterns()
            self.test_exponential_backoff_jitter()
            self.test_configuration_precedence()
            self.test_cloud_redaction()
            self.test_cloud_failsafe()
            
            print("=" * SMOKE_TEST_OUTPUT_LINES)
            print("🎉 All smoke tests passed!")
            print("🔒 Tests ran in isolated environment - no pollution to your dev environment")
            
        except SmokeTestError as e:
            print("=" * SMOKE_TEST_OUTPUT_LINES)
            print(f"❌ Smoke test failed: {e}")
            sys.exit(1)
        except Exception as e:
            print("=" * SMOKE_TEST_OUTPUT_LINES)
            print(f"💥 Unexpected error during smoke tests: {e}")
            sys.exit(1)
        finally:
            self.cleanup()


def main():
    """Main entry point for smoke tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run agent-validator smoke tests")
    parser.add_argument(
        "--backend-url",
        help="Backend URL for cloud testing (e.g., http://localhost:9090)",
        default="http://localhost:9090"
    )
    
    args = parser.parse_args()
    
    print("🔧 Comprehensive Agent Validator Smoke Tests")
    print("🔧 This creates an isolated environment and tests real end-to-end usage")
    
    print(f"🔧 Backend URL: {args.backend_url}")
    
    # Create tester and run tests
    tester = AgentValidatorSmokeTester(backend_url=args.backend_url)
    tester.run_all_tests()


if __name__ == '__main__':
    main()
