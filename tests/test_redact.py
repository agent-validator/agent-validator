"""Tests for redaction functionality."""

from agent_validator.redact import (
    Redactor,
    add_redaction_pattern,
    redact_sensitive_data,
)


def test_license_key_redaction():
    """Test redaction of license keys."""
    data = {
        "config": {
            "license_key": "license-1234567890abcdef1234567890abcdef12345678",
            "other": "value",
        }
    }

    redacted = redact_sensitive_data(data)

    assert redacted["config"]["license_key"] == "[REDACTED]"
    assert redacted["config"]["other"] == "value"


def test_jwt_redaction():
    """Test redaction of JWT tokens."""
    data = {
        "headers": {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        }
    }

    redacted = redact_sensitive_data(data)

    assert redacted["headers"]["Authorization"] == "[REDACTED]"


def test_email_redaction():
    """Test redaction of email addresses."""
    data = {"user": {"email": "john.doe@example.com", "name": "John Doe"}}

    redacted = redact_sensitive_data(data)

    # Should redact email (any redaction is acceptable)
    assert redacted["user"]["email"] != "john.doe@example.com"
    assert redacted["user"]["name"] == "John Doe"


def test_phone_redaction():
    """Test redaction of phone numbers."""
    data = {"contact": {"phone": "+1-555-123-4567", "name": "John Doe"}}

    redacted = redact_sensitive_data(data)

    # Should redact phone (any redaction is acceptable)
    assert redacted["contact"]["phone"] != "+1-555-123-4567"
    assert redacted["contact"]["name"] == "John Doe"


def test_ssn_redaction():
    """Test redaction of social security numbers."""
    data = {"user": {"ssn": "123-45-6789", "name": "John Doe"}}

    redacted = redact_sensitive_data(data)

    # Should redact SSN (any redaction is acceptable)
    assert redacted["user"]["ssn"] != "123-45-6789"
    assert redacted["user"]["name"] == "John Doe"


def test_credit_card_redaction():
    """Test redaction of credit card numbers."""
    data = {"payment": {"card_number": "1234-5678-9012-3456", "name": "John Doe"}}

    redacted = redact_sensitive_data(data)

    # Should redact card number (any redaction is acceptable)
    assert redacted["payment"]["card_number"] != "1234-5678-9012-3456"
    assert redacted["payment"]["name"] == "John Doe"


def test_password_redaction():
    """Test redaction of passwords."""
    data = {"credentials": {"password": "secretpassword123", "username": "john_doe"}}

    redacted = redact_sensitive_data(data)

    assert redacted["credentials"]["password"] != "secretpassword123"
    # Username should not be redacted (it's not sensitive)
    assert redacted["credentials"]["username"] == "john_doe"


def test_nested_structure_redaction():
    """Test redaction in nested data structures."""
    data = {
        "users": [
            {
                "email": "alice@example.com",
                "license_key": "license-alice1234567890abcdef",
            },
            {"email": "bob@example.com", "license_key": "license-bob1234567890abcdef"},
        ]
    }

    redacted = redact_sensitive_data(data)

    assert redacted["users"][0]["email"] != "alice@example.com"
    assert redacted["users"][0]["license_key"] != "license-alice1234567890abcdef"
    assert redacted["users"][1]["email"] != "bob@example.com"
    assert redacted["users"][1]["license_key"] != "license-bob1234567890abcdef"


def test_string_redaction():
    """Test redaction of sensitive data in strings."""
    text = "My license key is license-1234567890abcdef and my email is john@example.com"

    redacted = redact_sensitive_data(text)

    assert "license-1234567890abcdef" not in redacted
    assert "[REDACTED]" in redacted
    assert "j***n@example.com" in redacted


def test_custom_redaction_pattern():
    """Test adding custom redaction patterns."""
    # Add custom pattern for custom tokens
    add_redaction_pattern("custom_token", r"custom-[a-zA-Z0-9]{20,}")

    data = {"token": "custom-abcdefghijklmnopqrstuvwxyz123456"}

    redacted = redact_sensitive_data(data)

    assert redacted["token"] != "custom-abcdefghijklmnopqrstuvwxyz123456"


def test_redactor_with_custom_patterns():
    """Test Redactor with custom patterns."""
    custom_patterns = {"custom_id": r"id-[a-zA-Z0-9]{10,}"}

    redactor = Redactor(custom_patterns)

    data = {"user_id": "id-1234567890abcdef"}

    redacted = redactor.redact_dict(data)

    assert redacted["user_id"] != "id-1234567890abcdef"


def test_max_depth_redaction():
    """Test redaction with max depth limit."""
    # Create deeply nested structure
    data = {
        "level1": {
            "level2": {
                "level3": {
                    "level4": {
                        "level5": {
                            "level6": {
                                "level7": {
                                    "level8": {
                                        "level9": {
                                            "level10": {"level11": {"secret": "value"}}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    redacted = redact_sensitive_data(data, max_depth=5)

    # Should hit max depth and redact
    assert "level5" in str(redacted)
    assert "level6" not in str(redacted)
    assert "[REDACTED - MAX DEPTH]" in str(redacted)


def test_no_sensitive_data():
    """Test redaction when no sensitive data is present."""
    data = {"name": "John Doe", "age": 30, "city": "New York"}

    redacted = redact_sensitive_data(data)

    # Should be unchanged
    assert redacted == data


def test_mixed_data_types():
    """Test redaction with mixed data types."""
    data = {
        "string": "john@example.com",
        "number": 42,
        "boolean": True,
        "list": ["alice@example.com", "bob@example.com"],
        "dict": {"email": "charlie@example.com"},
    }

    redacted = redact_sensitive_data(data)

    # Should redact emails in all data types
    assert redacted["string"] != "john@example.com"
    assert redacted["number"] == 42
    assert redacted["boolean"] is True
    assert redacted["list"][0] != "alice@example.com"
    assert redacted["list"][1] != "bob@example.com"
    assert redacted["dict"]["email"] != "charlie@example.com"
