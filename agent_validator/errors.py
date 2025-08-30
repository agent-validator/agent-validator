"""Error classes for agent_validator."""

import uuid
from typing import Any, Dict, List, Optional


class ValidationError(Exception):
    """Raised when validation fails after all retries."""

    def __init__(
        self,
        path: str,
        reason: str,
        attempt: int,
        correlation_id: Optional[str] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        self.path = path
        self.reason = reason
        self.attempt = attempt
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.errors = errors or []

        super().__init__(f"Validation failed at {path}: {reason} (attempt {attempt})")


class SchemaError(Exception):
    """Raised when a schema is malformed."""

    def __init__(self, message: str, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        super().__init__(f"Schema error: {message}")


class CloudLogError(Exception):
    """Raised when cloud logging fails (non-fatal)."""

    def __init__(self, message: str, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        super().__init__(f"Cloud logging error: {message}")
