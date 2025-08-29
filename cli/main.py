"""Command-line interface for agent_validator."""

import json
import sys
import uuid
from pathlib import Path
from typing import Optional

import typer

from agent_validator import Schema, ValidationMode, validate
from agent_validator.logging_ import get_recent_logs, clear_logs
from agent_validator.config import get_config, save_config, create_default_config


app = typer.Typer(
    name="agent-validator",
    help="Validate LLM/agent outputs against schemas",
    add_completion=False,
)


@app.command()
def logs(
    n: int = typer.Option(20, "--number", "-n", help="Number of log entries to show"),
    clear: bool = typer.Option(False, "--clear", help="Clear all logs"),
) -> None:
    """Show recent validation logs."""
    if clear:
        clear_logs()
        typer.echo("All logs cleared.")
        return
    
    entries = get_recent_logs(n)
    if not entries:
        typer.echo("No logs found.")
        return
    
    for entry in entries:
        ts = entry.get("ts", "unknown")
        correlation_id = entry.get("correlation_id", "unknown")
        valid = "✓" if entry.get("valid") else "✗"
        mode = entry.get("mode", "unknown")
        attempts = entry.get("attempts", 0)
        duration_ms = entry.get("duration_ms", 0)
        
        typer.echo(
            f"{ts} {valid} {correlation_id} {mode} "
            f"(attempts: {attempts}, duration: {duration_ms}ms)"
        )


@app.command()
def test(
    schema_path: str = typer.Argument(..., help="Path to schema JSON file"),
    input_path: str = typer.Argument(..., help="Path to input JSON file"),
    mode: ValidationMode = typer.Option(
        ValidationMode.STRICT, "--mode", "-m", help="Validation mode"
    ),
) -> None:
    """Test validation with schema and input files."""
    try:
        # Load schema
        with open(schema_path, "r") as f:
            schema_data = json.load(f)
        schema = Schema.from_dict(schema_data)
        
        # Load input
        with open(input_path, "r") as f:
            input_data = json.load(f)
        
        # Validate
        result = validate(input_data, schema, mode=mode)
        
        typer.echo("✓ Validation successful")
        typer.echo(json.dumps(result, indent=2))
        sys.exit(0)
        
    except Exception as e:
        typer.echo(f"✗ Validation failed: {e}", err=True)
        sys.exit(2)


@app.command()
def id() -> None:
    """Generate a new correlation ID."""
    correlation_id = str(uuid.uuid4())
    typer.echo(correlation_id)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    set_api_key: Optional[str] = typer.Option(None, "--set-api-key", help="Set API key"),
    set_endpoint: Optional[str] = typer.Option(
        None, "--set-endpoint", help="Set cloud endpoint"
    ),
    set_log_to_cloud: Optional[bool] = typer.Option(
        None, "--set-log-to-cloud", help="Enable/disable cloud logging"
    ),
) -> None:
    """Manage configuration."""
    config = get_config()
    
    if show:
        typer.echo("Current configuration:")
        typer.echo(f"  max_output_bytes: {config.max_output_bytes}")
        typer.echo(f"  max_str_len: {config.max_str_len}")
        typer.echo(f"  max_list_len: {config.max_list_len}")
        typer.echo(f"  max_dict_keys: {config.max_dict_keys}")
        typer.echo(f"  log_to_cloud: {config.log_to_cloud}")
        typer.echo(f"  cloud_endpoint: {config.cloud_endpoint}")
        typer.echo(f"  timeout_s: {config.timeout_s}")
        typer.echo(f"  retries: {config.retries}")
        typer.echo(f"  api_key: {'***' if config.api_key else 'not set'}")
        typer.echo(f"  webhook_secret: {'***' if config.webhook_secret else 'not set'}")
        return
    
    if set_api_key is not None:
        config.api_key = set_api_key
        typer.echo("API key updated.")
    
    if set_endpoint is not None:
        config.cloud_endpoint = set_endpoint
        typer.echo("Cloud endpoint updated.")
    
    if set_log_to_cloud is not None:
        config.log_to_cloud = set_log_to_cloud
        typer.echo(f"Cloud logging {'enabled' if set_log_to_cloud else 'disabled'}.")
    
    # Save configuration
    save_config(config)


def main() -> None:
    """Main entry point."""
    # Create default config on first run
    create_default_config()
    
    app()


if __name__ == "__main__":
    main()
