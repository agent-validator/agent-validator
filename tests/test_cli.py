"""Tests for CLI functionality."""

import json
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cli.main import app


@pytest.fixture
def runner():
    # Use mix_stderr=False for Python 3.9, default for newer versions
    if sys.version_info < (3, 10):
        return CliRunner(mix_stderr=False)
    else:
        return CliRunner()


@pytest.fixture
def temp_schema_file():
    schema = {"schema": {"name": "string", "age": "integer"}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        f.flush()  # Ensure data is written to disk
        f.close()  # Close the file
        yield f.name

    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_input_file():
    data = {"name": "John Doe", "age": 30}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()  # Ensure data is written to disk
        f.close()  # Close the file
        yield f.name

    Path(f.name).unlink(missing_ok=True)


def test_id_command(runner):
    """Test the id command generates a UUID."""
    result = runner.invoke(app, ["id"])

    assert result.exit_code == 0
    # Verify it's a valid UUID
    uuid.UUID(result.stdout.strip())


def test_test_command_success(runner, temp_schema_file, temp_input_file):
    """Test the test command with valid input."""
    result = runner.invoke(app, ["test", temp_schema_file, temp_input_file])

    assert result.exit_code == 0
    assert "✓ Validation successful" in result.stdout


def test_test_command_failure(runner, temp_schema_file):
    """Test the test command with invalid input."""
    # Create invalid input file
    invalid_data = {"name": "John Doe"}  # Missing age

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(invalid_data, f)
        f.flush()
        f.close()
        invalid_input_file = f.name

    try:
        result = runner.invoke(app, ["test", temp_schema_file, invalid_input_file])

        assert result.exit_code == 2
        assert "✗ Validation failed" in result.stdout
    finally:
        Path(invalid_input_file).unlink(missing_ok=True)


def test_test_command_strict_mode(runner, temp_schema_file):
    """Test the test command with strict mode."""
    # Create input with string age (should fail in strict mode)
    data = {"name": "John Doe", "age": "30"}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        f.close()
        input_file = f.name

    try:
        result = runner.invoke(
            app, ["test", temp_schema_file, input_file, "--mode", "STRICT"]
        )

        assert result.exit_code == 2
        assert "✗ Validation failed" in result.stderr
    finally:
        Path(input_file).unlink(missing_ok=True)


def test_test_command_coerce_mode(runner, temp_schema_file):
    """Test the test command with coerce mode."""
    # Create input with string age (should succeed in coerce mode)
    data = {"name": "John Doe", "age": "30"}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        f.close()
        input_file = f.name

    try:
        result = runner.invoke(
            app, ["test", temp_schema_file, input_file, "--mode", "COERCE"]
        )

        assert result.exit_code == 0
        assert "✓ Validation successful" in result.stdout
    finally:
        Path(input_file).unlink(missing_ok=True)


@patch("cli.main.get_recent_logs")
def test_logs_command_no_logs(mock_get_logs, runner):
    """Test the logs command when no logs exist."""
    mock_get_logs.return_value = []

    result = runner.invoke(app, ["logs"])

    assert result.exit_code == 0
    assert "No logs found." in result.stdout


@patch("cli.main.get_recent_logs")
def test_logs_command_with_logs(mock_get_logs, runner):
    """Test the logs command with existing logs."""
    mock_logs = [
        {
            "ts": "2023-01-01T12:00:00Z",
            "correlation_id": "test-123",
            "valid": True,
            "mode": "STRICT",
            "attempts": 1,
            "duration_ms": 100,
        }
    ]
    mock_get_logs.return_value = mock_logs

    result = runner.invoke(app, ["logs"])

    assert result.exit_code == 0
    assert "2023-01-01 12:00:00" in result.stdout
    assert "test-123" in result.stdout
    assert "✓" in result.stdout  # Success indicator


@patch("cli.main.get_recent_logs")
def test_logs_command_with_number(mock_get_logs, runner):
    """Test the logs command with custom number."""
    mock_get_logs.return_value = []

    result = runner.invoke(app, ["logs", "--number", "10"])

    assert result.exit_code == 0
    mock_get_logs.assert_called_once_with(10)


@patch("cli.main.clear_logs")
def test_logs_command_clear(mock_clear_logs, runner):
    """Test the logs command with clear flag."""
    result = runner.invoke(app, ["logs", "--clear"])

    assert result.exit_code == 0
    assert "All logs cleared." in result.stdout
    mock_clear_logs.assert_called_once()


@patch("cli.main.get_config")
@patch("cli.main.save_config")
def test_config_command_show(mock_save_config, mock_get_config, runner):
    """Test the config command with show flag."""
    from agent_validator.typing_ import Config

    config = Config()
    mock_get_config.return_value = config

    result = runner.invoke(app, ["config", "--show"])

    assert result.exit_code == 0
    assert "Current configuration:" in result.stdout
    assert "max_output_bytes" in result.stdout
    assert "log_to_cloud" in result.stdout


@patch("cli.main.get_config")
@patch("cli.main.save_config")
def test_config_command_set_license_key(mock_save_config, mock_get_config, runner):
    """Test the config command setting license key."""
    from agent_validator.typing_ import Config

    config = Config()
    mock_get_config.return_value = config

    result = runner.invoke(app, ["config", "--set-license-key", "test-key"])

    assert result.exit_code == 0
    assert "License key updated." in result.stdout
    assert config.license_key == "test-key"
    mock_save_config.assert_called_once_with(config)


@patch("cli.main.get_config")
@patch("cli.main.save_config")
def test_config_command_set_endpoint(mock_save_config, mock_get_config, runner):
    """Test the config command setting endpoint."""
    from agent_validator.typing_ import Config

    config = Config()
    mock_get_config.return_value = config

    result = runner.invoke(
        app, ["config", "--set-endpoint", "https://test.example.com"]
    )

    assert result.exit_code == 0
    assert "Cloud endpoint updated." in result.stdout
    assert config.cloud_endpoint == "https://test.example.com"
    mock_save_config.assert_called_once_with(config)


@patch("cli.main.get_config")
@patch("cli.main.save_config")
def test_config_command_set_log_to_cloud(mock_save_config, mock_get_config, runner):
    """Test the config command setting log_to_cloud."""
    from agent_validator.typing_ import Config

    config = Config()
    mock_get_config.return_value = config

    result = runner.invoke(app, ["config", "--set-log-to-cloud"])

    assert result.exit_code == 0
    assert "Cloud logging enabled." in result.stdout
    assert config.log_to_cloud is True
    mock_save_config.assert_called_once_with(config)


def test_help_command(runner):
    """Test the help command."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Validate LLM/agent outputs against schemas" in result.stdout
    assert "id" in result.stdout
    assert "test" in result.stdout
    assert "logs" in result.stdout
    assert "config" in result.stdout
