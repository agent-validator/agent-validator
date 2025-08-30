"""Command-line interface for agent_validator."""

import json
import sys
import uuid
from pathlib import Path
from typing import Optional, Any

import typer

from agent_validator import Schema, ValidationMode, validate
from agent_validator.logging_ import get_recent_logs, clear_logs
from agent_validator.config import get_config, save_config, create_default_config


def parse_validation_mode(value: str) -> ValidationMode:
    """Parse validation mode with case-insensitive support."""
    value_lower = value.lower()
    if value_lower == "strict":
        return ValidationMode.STRICT
    elif value_lower == "coerce":
        return ValidationMode.COERCE
    else:
        raise ValueError(f"Invalid validation mode: {value}. Must be 'strict' or 'coerce'")


def convert_string_schema_to_types(schema_data: Any) -> Any:
    """Convert string-based schema to Python types."""
    if isinstance(schema_data, dict):
        converted = {}
        for key, value in schema_data.items():
            converted[key] = convert_string_schema_to_types(value)
        return converted
    elif isinstance(schema_data, list):
        if len(schema_data) == 1:
            # List schema: ["string"] -> [str]
            return [convert_string_schema_to_types(schema_data[0])]
        else:
            return [convert_string_schema_to_types(item) for item in schema_data]
    elif isinstance(schema_data, str):
        # Convert string type names to Python types
        type_map = {
            "string": str,
            "integer": int,
            "int": int,
            "float": float,
            "number": float,
            "boolean": bool,
            "bool": bool,
            "list": list,
            "array": list,
            "dict": dict,
            "object": dict,
        }
        return type_map.get(schema_data.lower(), schema_data)
    else:
        return schema_data


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
    
    # Print table header
    typer.echo("┌─────────────────────────────────────┬────────┬─────────────┬─────────┬──────────┬─────────────┐")
    typer.echo("│ Timestamp                           │ Status │ Correlation │ Mode    │ Attempts │ Duration    │")
    typer.echo("├─────────────────────────────────────┼────────┼─────────────┼─────────┼──────────┼─────────────┤")
    
    for entry in entries:
        ts = entry.get("ts", "unknown")
        correlation_id = entry.get("correlation_id")
        valid = "✓" if entry.get("valid") else "✗"
        mode = entry.get("mode", "unknown")
        attempts = entry.get("attempts", 0)
        duration_ms = entry.get("duration_ms", 0)
        
        # Format correlation ID - show "none" if missing, truncate if too long
        if correlation_id:
            # Truncate long correlation IDs for readability
            display_id = correlation_id[:8] + "..." if len(correlation_id) > 12 else correlation_id
        else:
            display_id = "none"
        
        # Format timestamp for better readability
        if ts != "unknown":
            try:
                # Parse ISO timestamp and format it nicely
                from datetime import datetime
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                formatted_ts = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_ts = ts
        else:
            formatted_ts = ts
        
        # Print table row
        typer.echo(f"│ {formatted_ts:<35} │ {valid:>6} │ {display_id:>11} │ {mode:>7} │ {attempts:>8} │ {duration_ms:>9}ms │")
    
    # Print table footer
    typer.echo("└─────────────────────────────────────┴────────┴─────────────┴─────────┴──────────┴─────────────┘")


@app.command()
def test(
    schema_path: str = typer.Argument(..., help="Path to schema JSON file"),
    input_path: str = typer.Argument(..., help="Path to input JSON file"),
    mode: str = typer.Option(
        "strict", "--mode", "-m", help="Validation mode (strict/coerce)"
    ),
) -> None:
    """Test validation with schema and input files."""
    try:
        # Parse validation mode with case-insensitive support
        validation_mode = parse_validation_mode(mode)
        
        # Load schema
        with open(schema_path, "r") as f:
            schema_data = json.load(f)
        
        # Handle both direct schema and wrapped schema formats
        if "schema" in schema_data:
            # Wrapped format: {"schema": {...}}
            schema = Schema.from_dict(schema_data)
        else:
            # Direct format: {...} - convert string types to Python types
            converted_schema = convert_string_schema_to_types(schema_data)
            schema = Schema(converted_schema)
        
        # Load input
        with open(input_path, "r") as f:
            input_data = json.load(f)
        
        # Validate
        result = validate(input_data, schema, mode=validation_mode)
        
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
    show_secrets: bool = typer.Option(False, "--show-secrets", help="Show sensitive values (license key, webhook secret)"),
    set_license_key: Optional[str] = typer.Option(None, "--set-license-key", help="Set license key"),
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
        
        # Handle sensitive values based on show_secrets flag
        if show_secrets:
            typer.echo(f"  license_key: {config.license_key or 'not set'}")
            typer.echo(f"  webhook_secret: {config.webhook_secret or 'not set'}")
        else:
            typer.echo(f"  license_key: {'***' if config.license_key else 'not set'}")
            typer.echo(f"  webhook_secret: {'***' if config.webhook_secret else 'not set'}")
        return
    
    if set_license_key is not None:
        config.license_key = set_license_key
        typer.echo("License key updated.")
    
    if set_endpoint is not None:
        config.cloud_endpoint = set_endpoint
        typer.echo("Cloud endpoint updated.")
    
    if set_log_to_cloud is not None:
        config.log_to_cloud = set_log_to_cloud
        typer.echo(f"Cloud logging {'enabled' if set_log_to_cloud else 'disabled'}.")
    
    # Save configuration
    save_config(config)


@app.command()
def cloud_logs(
    n: int = typer.Option(20, "--number", "-n", help="Number of log entries to show"),
) -> None:
    """Show recent validation logs from cloud service."""
    config = get_config()
    
    if not config.license_key:
        typer.echo("❌ No license key configured. Run 'agent-validator config --set-license-key <key>' first.")
        return
    
    try:
        import requests
        
        response = requests.get(
            f"{config.cloud_endpoint}/logs?limit={n}",
            headers={"license-key": config.license_key},
            timeout=10
        )
        response.raise_for_status()
        
        logs = response.json()
        if not logs:
            typer.echo("No logs found in cloud service.")
            return
        
        # Print table header
        typer.echo("┌─────────────────────────────────────┬────────┬─────────────┬─────────┬──────────┬─────────────┐")
        typer.echo("│ Timestamp                           │ Status │ Correlation │ Mode    │ Attempts │ Duration    │")
        typer.echo("├─────────────────────────────────────┼────────┼─────────────┼─────────┼──────────┼─────────────┤")
        
        for log in logs:
            ts = log.get("ts", "unknown")
            correlation_id = log.get("correlation_id")
            valid = "✓" if log.get("valid") else "✗"
            mode = log.get("mode", "unknown")
            attempts = log.get("attempts", 0)
            duration_ms = log.get("duration_ms", 0)
            
            # Format correlation ID - show "none" if missing, truncate if too long
            if correlation_id and correlation_id != "unknown":
                # Truncate long correlation IDs for readability
                display_id = correlation_id[:8] + "..." if len(correlation_id) > 12 else correlation_id
            else:
                display_id = "none"
            
            # Format timestamp for better readability
            if ts != "unknown":
                try:
                    # Parse ISO timestamp and format it nicely
                    from datetime import datetime
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    formatted_ts = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    formatted_ts = ts
            else:
                formatted_ts = ts
            
            # Print table row
            typer.echo(f"│ {formatted_ts:<35} │ {valid:>6} │ {display_id:>11} │ {mode:>7} │ {attempts:>8} │ {duration_ms:>9}ms │")
        
        # Print table footer
        typer.echo("└─────────────────────────────────────┴────────┴─────────────┴─────────┴──────────┴─────────────┘")
            
    except requests.exceptions.ConnectionError:
        typer.echo(f"❌ Cannot connect to {config.cloud_endpoint}. Is the server running?")
    except requests.exceptions.RequestException as e:
        typer.echo(f"❌ Failed to fetch cloud logs: {e}")


@app.command()
def dashboard(
    open_browser: bool = typer.Option(True, "--open", help="Open dashboard in browser"),
    show_url: bool = typer.Option(False, "--url", help="Show dashboard URL"),
    port: int = typer.Option(8080, "--port", "-p", help="Port for local proxy server"),
) -> None:
    """Open the web dashboard for viewing cloud logs via secure local proxy."""
    config = get_config()
    
    if not config.license_key:
        typer.echo("❌ No license key configured. Run 'agent-validator config --set-license-key <key>' first.")
        return
    
    try:
        import threading
        import time
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import urllib.request
        import urllib.parse
        
        class DashboardProxy(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    # Proxy the dashboard request with proper headers
                    try:
                        req = urllib.request.Request(
                            f"{config.cloud_endpoint}/dashboard",
                            headers={"license-key": config.license_key}
                        )
                        
                        with urllib.request.urlopen(req) as response:
                            content = response.read()
                            self.send_response(200)
                            self.send_header('Content-type', 'text/html')
                            self.end_headers()
                            self.wfile.write(content)
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        error_html = f"""
                        <html><body>
                        <h1>Error</h1>
                        <p>Failed to load dashboard: {e}</p>
                        </body></html>
                        """
                        self.wfile.write(error_html.encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                # Suppress logging
                pass
        
        # Start local proxy server
        server = HTTPServer(('localhost', port), DashboardProxy)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        local_url = f"http://localhost:{port}"
        
        if show_url:
            typer.echo(f"Dashboard URL: {local_url}")
        
        if open_browser:
            try:
                import webbrowser
                # Give server a moment to start
                time.sleep(0.5)
                webbrowser.open(local_url)
                typer.echo(f"🌐 Opening dashboard at {local_url}")
                typer.echo("Press Ctrl+C to stop the proxy server")
                
                # Keep the server running
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    typer.echo("\n🛑 Stopping proxy server...")
                    server.shutdown()
                    
            except Exception as e:
                typer.echo(f"❌ Failed to open browser: {e}")
                typer.echo(f"Please visit: {local_url}")
        else:
            typer.echo(f"Dashboard URL: {local_url}")
            typer.echo("Press Ctrl+C to stop the proxy server")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                typer.echo("\n🛑 Stopping proxy server...")
                server.shutdown()
            
    except Exception as e:
        typer.echo(f"❌ Failed to start dashboard proxy: {e}")


def main() -> None:
    """Main entry point."""
    # Create default config on first run
    create_default_config()
    
    app()


if __name__ == "__main__":
    main()
