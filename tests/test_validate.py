"""Tests for validation logic."""

import json
import pytest
from agent_validator import validate, Schema, ValidationMode, ValidationError, SchemaError


def test_basic_validation():
    """Test basic validation with simple schema."""
    schema = Schema({"name": str, "age": int})
    data = {"name": "John", "age": 30}
    
    result = validate(data, schema)
    assert result == data


def test_strict_mode():
    """Test strict mode validation."""
    schema = Schema({"age": int})
    data = {"age": "30"}  # String instead of int
    
    with pytest.raises(ValidationError):
        validate(data, schema, mode=ValidationMode.STRICT)


def test_coerce_mode():
    """Test coercion mode validation."""
    schema = Schema({"age": int, "is_active": bool})
    data = {"age": "30", "is_active": "true"}
    
    result = validate(data, schema, mode=ValidationMode.COERCE)
    assert result["age"] == 30
    assert result["is_active"] is True


def test_nested_schema():
    """Test validation with nested schemas."""
    schema = Schema({
        "user": {
            "name": str,
            "age": int
        },
        "tags": [str]
    })
    
    data = {
        "user": {
            "name": "John",
            "age": 30
        },
        "tags": ["developer", "python"]
    }
    
    result = validate(data, schema)
    assert result == data


def test_optional_fields():
    """Test validation with optional fields."""
    schema = Schema({
        "name": str,
        "age": None,  # Optional field
        "email": str
    })
    
    # With optional field
    data1 = {"name": "John", "age": 30, "email": "john@example.com"}
    result1 = validate(data1, schema)
    assert result1 == data1
    
    # Without optional field
    data2 = {"name": "John", "email": "john@example.com"}
    result2 = validate(data2, schema)
    assert result2 == data2


def test_list_validation():
    """Test validation of list fields."""
    schema = Schema({
        "numbers": [int],
        "strings": [str]
    })
    
    data = {
        "numbers": [1, 2, 3],
        "strings": ["a", "b", "c"]
    }
    
    result = validate(data, schema)
    assert result == data


def test_list_coercion():
    """Test coercion of list elements."""
    schema = Schema({
        "numbers": [int],
        "booleans": [bool]
    })
    
    data = {
        "numbers": ["1", "2", "3"],
        "booleans": ["true", "false", "1"]
    }
    
    result = validate(data, schema, mode=ValidationMode.COERCE)
    assert result["numbers"] == [1, 2, 3]
    assert result["booleans"] == [True, False, True]


def test_size_limits():
    """Test size limit validation."""
    schema = Schema({"data": str})
    
    # Test string length limit
    long_string = "x" * 10000
    data = {"data": long_string}
    
    with pytest.raises(ValidationError, match="size_limit"):
        validate(data, schema)


def test_missing_required_field():
    """Test validation with missing required field."""
    schema = Schema({"name": str, "age": int})
    data = {"name": "John"}  # Missing age
    
    with pytest.raises(ValidationError, match="Missing required field"):
        validate(data, schema)


def test_invalid_json_string():
    """Test validation of invalid JSON string."""
    schema = Schema({"name": str})
    
    # Invalid JSON
    with pytest.raises(ValidationError, match="Invalid JSON"):
        validate("invalid json", schema, mode=ValidationMode.STRICT)
    
    # Valid JSON string
    result = validate('{"name": "John"}', schema, mode=ValidationMode.STRICT)
    assert result == {"name": "John"}


def test_retry_function():
    """Test validation with retry function."""
    schema = Schema({"name": str, "age": int})
    
    attempts = []
    
    def retry_fn(prompt: str, context: dict):
        attempts.append(1)
        if len(attempts) == 1:
            return "invalid json"  # First attempt fails
        return json.dumps({"name": "John", "age": 30})  # Second attempt succeeds
    
    result = validate(
        "invalid json",
        schema,
        retry_fn=retry_fn,
        retries=2,
        mode=ValidationMode.STRICT
    )
    
    assert result == {"name": "John", "age": 30}
    assert len(attempts) == 2


def test_schema_validation():
    """Test schema validation."""
    # Valid schema
    Schema({"name": str, "age": int})
    
    # Invalid schema - unsupported type
    with pytest.raises(SchemaError):
        Schema({"name": bytes})
    
    # Invalid schema - malformed list
    with pytest.raises(SchemaError):
        Schema({"items": [str, int]})  # List with multiple elements


def test_boolean_coercion():
    """Test boolean coercion."""
    schema = Schema({"active": bool})
    
    test_cases = [
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
        ("yes", True),
        ("no", False),
        ("on", True),
        ("off", False),
    ]
    
    for input_val, expected in test_cases:
        data = {"active": input_val}
        result = validate(data, schema, mode=ValidationMode.COERCE)
        assert result["active"] == expected


def test_number_coercion():
    """Test number coercion."""
    schema = Schema({"age": int, "score": float})
    
    data = {"age": "30", "score": "95.5"}
    result = validate(data, schema, mode=ValidationMode.COERCE)
    
    assert result["age"] == 30
    assert result["score"] == 95.5
