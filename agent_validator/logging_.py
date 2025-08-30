"""Logging utilities for validation results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .config import get_config
from .errors import CloudLogError
from .redact import redact_sensitive_data


def log_validation_result(
    correlation_id: Optional[str],
    valid: bool,
    errors: List[Dict[str, Any]],
    attempts: int,
    duration_ms: int,
    mode: str,
    context: Dict[str, Any],
    output_sample: str,
    log_to_cloud: bool = False,
    config: Optional[Any] = None,
) -> None:
    """
    Log validation result to local file and optionally to cloud.
    
    Args:
        correlation_id: Unique identifier for the validation
        valid: Whether validation succeeded
        errors: List of validation errors
        attempts: Number of attempts made
        duration_ms: Duration in milliseconds
        mode: Validation mode used
        context: Additional context
        output_sample: Sample of the output (truncated)
        log_to_cloud: Whether to log to cloud service
        config: Configuration object
    """
    config = config or get_config()

    # Create log entry
    log_entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "correlation_id": correlation_id,
        "valid": valid,
        "errors": errors,
        "attempts": attempts,
        "duration_ms": duration_ms,
        "mode": mode,
        "limits": {
            "max_output_bytes": config.max_output_bytes,
            "max_str_len": config.max_str_len,
            "max_list_len": config.max_list_len,
            "max_dict_keys": config.max_dict_keys,
        },
        "context": context,
        "output_sample": output_sample,
    }

    # Redact sensitive data
    redacted_entry = redact_sensitive_data(log_entry)

    # Log locally
    _log_locally(redacted_entry)

    # Log to cloud if requested
    if log_to_cloud:
        try:
            _log_to_cloud(redacted_entry, config)
        except Exception as e:
            # Cloud logging errors should not crash the application
            print(f"Warning: Cloud logging failed: {e}")


def _log_locally(log_entry: Dict[str, Any]) -> None:
    """Log entry to local JSONL file."""
    # Create logs directory
    logs_dir = Path.home() / ".agent_validator" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Create daily log file
    today = datetime.utcnow().strftime("%Y-%m-%d")
    log_file = logs_dir / f"{today}.jsonl"

    # Write log entry
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


def _log_to_cloud(log_entry: Dict[str, Any], config: Any) -> None:
    """Log entry to cloud service."""
    if not config.license_key:
        raise CloudLogError("No license key configured for cloud logging")

    # Prepare payload
    payload = json.dumps(log_entry)

    # Check payload size limit (64KB)
    if len(payload.encode()) > 65536:
        # Truncate output_sample
        truncated_sample = log_entry["output_sample"][:500] + "…[truncated]"
        log_entry["output_sample"] = truncated_sample
        payload = json.dumps(log_entry)

        # If still too large, truncate further
        if len(payload.encode()) > 65536:
            log_entry["output_sample"] = "[truncated]"
            payload = json.dumps(log_entry)

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "license-key": config.license_key,
    }

    # Add HMAC signature if webhook secret is configured
    if config.webhook_secret:
        import hashlib
        import hmac

        signature = hmac.new(
            config.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        headers["x-signature"] = signature

    # Send request
    try:
        response = requests.post(
            f"{config.cloud_endpoint}/logs",
            data=payload,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise CloudLogError(f"HTTP request failed: {e}")


def get_recent_logs(n: int = 20) -> List[Dict[str, Any]]:
    """
    Get recent log entries from local files.
    
    Args:
        n: Number of entries to return
        
    Returns:
        List of log entries (most recent first)
    """
    logs_dir = Path.home() / ".agent_validator" / "logs"
    if not logs_dir.exists():
        return []

    all_entries = []

    # Read from all log files
    for log_file in sorted(logs_dir.glob("*.jsonl"), reverse=True):
        try:
            with open(log_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            all_entries.append(entry)
                        except json.JSONDecodeError:
                            continue
        except OSError:
            continue

    # Sort by timestamp and return most recent
    all_entries.sort(key=lambda x: x.get("ts", ""), reverse=True)
    return all_entries[:n]


def clear_logs() -> None:
    """Clear all local log files."""
    logs_dir = Path.home() / ".agent_validator" / "logs"
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.jsonl"):
            try:
                log_file.unlink()
            except OSError:
                pass
