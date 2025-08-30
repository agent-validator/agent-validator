"""Property-based fuzzing tests for JSON shapes."""

import json
import random
from typing import Any, Dict, List, Union

import pytest
from hypothesis import given, strategies as st

from agent_validator import validate, Schema, ValidationMode, ValidationError


def generate_random_schema(depth: int = 0, max_depth: int = 3) -> Dict[str, Any]:
    """Generate a random schema for testing."""
    if depth >= max_depth:
        return {"value": random.choice([str, int, float, bool])}
    
    schema = {}
    num_fields = random.randint(1, 5)
    
    for i in range(num_fields):
        field_name = f"field_{i}"
        field_type = random.choice([
            str, int, float, bool, list, dict, None  # None for optional
        ])
        
        if field_type is list:
            # List with random element type
            element_type = random.choice([str, int, float, bool, dict])
            if element_type is dict:
                schema[field_name] = [generate_random_schema(depth + 1, max_depth)]
            else:
                schema[field_name] = [element_type]
        elif field_type is dict:
            schema[field_name] = generate_random_schema(depth + 1, max_depth)
        else:
            schema[field_name] = field_type
    
    return schema


def generate_data_for_schema(schema: Dict[str, Any], depth: int = 0, max_depth: int = 3) -> Dict[str, Any]:
    """Generate data that matches a schema."""
    if depth >= max_depth:
        return {"value": "test"}
    
    data = {}
    
    for field_name, field_type in schema.items():
        if field_type is None:
            # Optional field - randomly include or exclude
            if random.choice([True, False]):
                data[field_name] = "optional_value"
        elif field_type is str:
            data[field_name] = f"string_{random.randint(1, 100)}"
        elif field_type is int:
            data[field_name] = random.randint(1, 1000)
        elif field_type is float:
            data[field_name] = random.uniform(0, 1000)
        elif field_type is bool:
            data[field_name] = random.choice([True, False])
        elif isinstance(field_type, list):
            # List field
            element_type = field_type[0]
            if isinstance(element_type, dict):
                # List of objects
                data[field_name] = [
                    generate_data_for_schema(element_type, depth + 1, max_depth)
                    for _ in range(random.randint(1, 3))
                ]
            else:
                # List of primitives
                if element_type is str:
                    data[field_name] = [f"item_{i}" for i in range(random.randint(1, 3))]
                elif element_type is int:
                    data[field_name] = [random.randint(1, 100) for _ in range(random.randint(1, 3))]
                elif element_type is float:
                    data[field_name] = [random.uniform(0, 100) for _ in range(random.randint(1, 3))]
                elif element_type is bool:
                    data[field_name] = [random.choice([True, False]) for _ in range(random.randint(1, 3))]
        elif isinstance(field_type, dict):
            # Nested object
            data[field_name] = generate_data_for_schema(field_type, depth + 1, max_depth)
    
    return data


def generate_invalid_data_for_schema(schema: Dict[str, Any], depth: int = 0, max_depth: int = 3) -> Dict[str, Any]:
    """Generate data that doesn't match a schema."""
    if depth >= max_depth:
        return {"value": 123}  # Wrong type
    
    data = {}
    
    for field_name, field_type in schema.items():
        if field_type is None:
            # Optional field - include with wrong type
            data[field_name] = 123
        elif field_type is str:
            data[field_name] = random.randint(1, 1000)  # Wrong type
        elif field_type is int:
            data[field_name] = "wrong_type"  # Wrong type
        elif field_type is float:
            data[field_name] = "wrong_type"  # Wrong type
        elif field_type is bool:
            data[field_name] = "wrong_type"  # Wrong type
        elif isinstance(field_type, list):
            # List field with wrong element type
            element_type = field_type[0]
            if isinstance(element_type, dict):
                # List of objects - give wrong type
                data[field_name] = "not_a_list"
            else:
                # List of primitives - give wrong element type
                if element_type is str:
                    data[field_name] = [123, 456]  # Wrong element type
                elif element_type is int:
                    data[field_name] = ["wrong", "types"]  # Wrong element type
                elif element_type is float:
                    data[field_name] = ["wrong", "types"]  # Wrong element type
                elif element_type is bool:
                    data[field_name] = ["wrong", "types"]  # Wrong element type
        elif isinstance(field_type, dict):
            # Nested object - give wrong type
            data[field_name] = "not_an_object"
    
    return data


@given(st.integers(min_value=1, max_value=3))
def test_schema_validation_accepts_valid_data(max_depth):
    """Test that schemas accept valid data."""
    schema_dict = generate_random_schema(max_depth=max_depth)
    schema = Schema(schema_dict)
    
    # Generate valid data
    valid_data = generate_data_for_schema(schema_dict, max_depth=max_depth)
    
    # Should validate successfully
    result = validate(valid_data, schema, mode=ValidationMode.STRICT)
    assert result == valid_data


@given(st.integers(min_value=1, max_value=3))
def test_schema_validation_rejects_invalid_data(max_depth):
    """Test that schemas reject invalid data."""
    schema_dict = generate_random_schema(max_depth=max_depth)
    schema = Schema(schema_dict)
    
    # Generate invalid data
    invalid_data = generate_invalid_data_for_schema(schema_dict, max_depth=max_depth)
    
    # Should fail validation
    with pytest.raises(ValidationError):
        validate(invalid_data, schema, mode=ValidationMode.STRICT)


@given(st.integers(min_value=1, max_value=3))
def test_coercion_mode_accepts_coercible_data(max_depth):
    """Test that coercion mode accepts data that can be coerced."""
    schema_dict = generate_random_schema(max_depth=max_depth)
    schema = Schema(schema_dict)
    
    # Generate data with string numbers/booleans that can be coerced
    coercible_data = {}
    for field_name, field_type in schema_dict.items():
        if field_type is int:
            coercible_data[field_name] = str(random.randint(1, 1000))
        elif field_type is float:
            coercible_data[field_name] = str(random.uniform(0, 1000))
        elif field_type is bool:
            coercible_data[field_name] = random.choice(["true", "false", "1", "0"])
        elif field_type is str:
            coercible_data[field_name] = f"string_{random.randint(1, 100)}"
        elif isinstance(field_type, list):
            element_type = field_type[0]
            if element_type is int:
                coercible_data[field_name] = [str(random.randint(1, 100)) for _ in range(3)]
            elif element_type is str:
                coercible_data[field_name] = [f"item_{i}" for i in range(3)]
        elif isinstance(field_type, dict):
            coercible_data[field_name] = generate_data_for_schema(field_type, max_depth=max_depth)
    
    # Should validate successfully with coercion
    result = validate(coercible_data, schema, mode=ValidationMode.COERCE)
    
    # Check that types were coerced correctly
    for field_name, field_type in schema_dict.items():
        if field_type is int:
            assert isinstance(result[field_name], int)
        elif field_type is float:
            assert isinstance(result[field_name], float)
        elif field_type is bool:
            assert isinstance(result[field_name], bool)


def test_schema_serialization():
    """Test that schemas can be serialized and deserialized."""
    schema_dict = generate_random_schema(max_depth=2)
    original_schema = Schema(schema_dict)
    
    # Serialize to dict
    serialized = original_schema.to_dict()
    
    # Deserialize
    deserialized_schema = Schema.from_dict(serialized)
    
    # Should be equivalent
    assert deserialized_schema.schema_dict == original_schema.schema_dict


def test_schema_json_serialization():
    """Test that schemas can be serialized to JSON and back."""
    schema_dict = generate_random_schema(max_depth=2)
    original_schema = Schema(schema_dict)
    
    # Serialize to JSON
    json_str = original_schema.to_json()
    
    # Deserialize
    deserialized_schema = Schema.from_json(json_str)
    
    # Should be equivalent
    assert deserialized_schema.schema_dict == original_schema.schema_dict


def test_size_limits_enforced():
    """Test that size limits are enforced."""
    # Create a schema with a string field
    schema = Schema({"data": str})
    
    # Create data that exceeds the default string length limit (8192)
    oversized_data = {"data": "x" * 10000}
    
    # Should fail validation
    with pytest.raises(ValidationError, match="size_limit"):
        validate(oversized_data, schema)


def test_nested_list_validation():
    """Test validation of nested lists."""
    schema = Schema({
        "users": [{
            "name": str,
            "scores": [int]
        }]
    })
    
    valid_data = {
        "users": [
            {
                "name": "Alice",
                "scores": [85, 92, 78]
            },
            {
                "name": "Bob",
                "scores": [91, 87, 95]
            }
        ]
    }
    
    result = validate(valid_data, schema)
    assert result == valid_data


def test_optional_fields_handling():
    """Test handling of optional fields."""
    schema = Schema({
        "name": str,
        "age": None,  # Optional
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
