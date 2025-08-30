"""Command-line interface for agent_validator."""

import json
import sys
import uuid
from typing import Any, Optional

import typer

from agent_validator import Schema, ValidationMode, validate
from agent_validator.config import create_default_config, get_config, save_config
from agent_validator.logging_ import clear_logs, get_recent_logs


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
    typer.echo("┌─────────────────────────────────────┬────────┬─────────────┬─────────┬──────────┬─────────────┬─────────┬─────────┐")
    typer.echo("│ Timestamp                           │ Status │ Correlation │ Mode    │ Attempts │ Duration    │ Errors  │ Size    │")
    typer.echo("├─────────────────────────────────────┼────────┼─────────────┼─────────┼──────────┼─────────────┼─────────┼─────────┤")

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

        # Get additional info
        errors = entry.get("errors", [])
        error_count = len(errors) if errors else 0

        # Calculate output size from output_sample
        output_sample = entry.get("output_sample", "")
        output_size = len(output_sample.encode('utf-8')) if output_sample else 0

        # Format size (show KB if > 1KB)
        if output_size > 1024:
            size_display = f"{output_size // 1024}KB"
        else:
            size_display = f"{output_size}B"

        # Print table row
        typer.echo(f"│ {formatted_ts:<35} │ {valid:>6} │ {display_id:>11} │ {mode:>7} │ {attempts:>8} │ {duration_ms:>9}ms │ {error_count:>7} │ {size_display:>7} │")

    # Print table footer
    typer.echo("└─────────────────────────────────────┴────────┴─────────────┴─────────┴──────────┴─────────────┴─────────┴─────────┘")


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
        with open(schema_path) as f:
            schema_data = json.load(f)

        # Handle both direct schema and wrapped schema formats
        if "schema" in schema_data:
            # Wrapped format: {"schema": {...}}
            # Convert string types in the nested schema
            converted_schema_dict = convert_string_schema_to_types(schema_data["schema"])
            schema = Schema(converted_schema_dict)
        else:
            # Direct format: {...} - convert string types to Python types
            converted_schema = convert_string_schema_to_types(schema_data)
            schema = Schema(converted_schema)

        # Load input
        with open(input_path) as f:
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
    set_webhook_secret: Optional[str] = typer.Option(None, "--set-webhook-secret", help="Set webhook secret"),
    set_log_to_cloud: Optional[bool] = typer.Option(
        None, "--set-log-to-cloud", help="Enable/disable cloud logging", is_flag=True
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

    if set_webhook_secret is not None:
        config.webhook_secret = set_webhook_secret
        typer.echo("Webhook secret updated.")

    if set_log_to_cloud is not None:
        config.log_to_cloud = set_log_to_cloud
        typer.echo(f"Cloud logging {'enabled' if set_log_to_cloud else 'disabled'}.")

    # Save configuration
    save_config(config)


@app.command()
def webhook(
    generate: bool = typer.Option(False, "--generate", "-g", help="Generate a new webhook secret"),
    status: bool = typer.Option(False, "--status", "-s", help="Check webhook secret status"),
    show: bool = typer.Option(False, "--show", help="Show the current webhook secret"),
    revoke: bool = typer.Option(False, "--revoke", "-r", help="Revoke current webhook secret"),
    force: bool = typer.Option(False, "--force", "-f", help="Force generation even if secret exists"),
) -> None:
    """Manage webhook secrets for HMAC signature validation."""
    config = get_config()

    if not config.license_key:
        typer.echo("❌ No license key configured. Run 'agent-validator config --set-license-key <key>' first.")
        return

    try:
        import requests

        if generate:
            # Generate new webhook secret
            url = f"{config.cloud_endpoint}/webhooks/generate"
            params = {"force": force} if force else {}

            response = requests.post(
                url,
                headers={"license-key": config.license_key},
                params=params,
                timeout=10
            )

            if response.status_code == 409 and not force:
                typer.echo("⚠️  Webhook secret already exists.")
                typer.echo("   Use --force to generate a new one (this will invalidate the old secret).")
                return

            response.raise_for_status()
            data = response.json()

            typer.echo("🔐 Webhook secret generated successfully!")
            typer.echo(f"   Secret: {data['webhook_secret']}")
            typer.echo("")
            typer.echo("⚠️  WARNING: This is the only time you will see this secret!")
            typer.echo("")

            # Check if webhook secret already exists locally
            if config.webhook_secret:
                typer.echo("⚠️  You already have a webhook secret configured locally.")
                typer.echo("   This will overwrite your existing webhook secret.")
                typer.echo("   Your old secret will no longer work for HMAC validation.")

                # Ask for confirmation
                confirm = typer.confirm("Do you want to continue and overwrite the existing secret?")
                if not confirm:
                    typer.echo("❌ Webhook secret generation cancelled.")
                    typer.echo("   You can manually configure the secret later with:")
                    typer.echo(f"   agent-validator config --set-webhook-secret {data['webhook_secret']}")
                    return

            # Auto-set the webhook secret
            config.webhook_secret = data['webhook_secret']
            save_config(config)
            typer.echo("✅ Webhook secret automatically configured in your local settings.")
            typer.echo("   You can now use HMAC signatures for enhanced security.")

        elif show:
            # Show current webhook secret
            if config.webhook_secret:
                typer.echo("🔐 Current webhook secret:")
                typer.echo(f"   {config.webhook_secret}")
                typer.echo("")
                typer.echo("⚠️  Keep this secret secure and don't share it!")
            else:
                typer.echo("❌ No webhook secret configured locally.")
                typer.echo("   Run 'agent-validator webhook --generate' to create one.")

        elif status:
            # Check webhook status
            response = requests.get(
                f"{config.cloud_endpoint}/webhooks/status",
                headers={"license-key": config.license_key},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data["has_webhook_secret"]:
                typer.echo("✅ Webhook secret is configured")
                typer.echo(f"   Created: {data['created_at']}")
            else:
                typer.echo("❌ No webhook secret configured")
                typer.echo("   Run 'agent-validator webhook --generate' to create one")

        elif revoke:
            # Revoke webhook secret
            response = requests.delete(
                f"{config.cloud_endpoint}/webhooks/revoke",
                headers={"license-key": config.license_key},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            typer.echo("🗑️  Webhook secret revoked successfully")
            typer.echo("   Generate a new one with 'agent-validator webhook --generate' to continue using HMAC signatures")

        else:
            # Show help
            typer.echo("Webhook secret management commands:")
            typer.echo("  --generate, -g    Generate a new webhook secret")
            typer.echo("  --status, -s      Check if webhook secret is configured")
            typer.echo("  --show            Show the current webhook secret")
            typer.echo("  --revoke, -r      Revoke current webhook secret")
            typer.echo("  --force, -f       Force generation (overwrites existing secret)")

    except requests.exceptions.RequestException as e:
        typer.echo(f"❌ Failed to communicate with API: {e}")
        return


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
        typer.echo("┌─────────────────────────────────────┬────────┬─────────────┬─────────┬──────────┬─────────────┬─────────┬─────────┐")
        typer.echo("│ Timestamp                           │ Status │ Correlation │ Mode    │ Attempts │ Duration    │ Errors  │ Size    │")
        typer.echo("├─────────────────────────────────────┼────────┼─────────────┼─────────┼──────────┼─────────────┼─────────┼─────────┤")

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

            # Get additional info
            errors = log.get("errors", [])
            error_count = len(errors) if errors else 0

            # Calculate output size from output_sample
            output_sample = log.get("output_sample", "")
            output_size = len(output_sample.encode('utf-8')) if output_sample else 0

            # Format size (show KB if > 1KB)
            if output_size > 1024:
                size_display = f"{output_size // 1024}KB"
            else:
                size_display = f"{output_size}B"

            # Print table row
            typer.echo(f"│ {formatted_ts:<35} │ {valid:>6} │ {display_id:>11} │ {mode:>7} │ {attempts:>8} │ {duration_ms:>9}ms │ {error_count:>7} │ {size_display:>7} │")

        # Print table footer
        typer.echo("└─────────────────────────────────────┴────────┴─────────────┴─────────┴──────────┴─────────────┴─────────┴─────────┘")

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
        import urllib.parse
        import urllib.request
        from http.server import BaseHTTPRequestHandler, HTTPServer

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
