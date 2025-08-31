"""Schema definition and validation logic."""

import json
from typing import Any, Optional

from .errors import SchemaError
from .typing_ import ValidatorFunction


class Schema:
    """Schema definition for validating agent outputs."""

    def __init__(
        self,
        schema_dict: dict[str, Any],
        max_keys: Optional[int] = None,
        max_list_len: Optional[int] = None,
        max_str_len: Optional[int] = None,
        validators: Optional[dict[str, ValidatorFunction]] = None,
    ):
        self.schema_dict = schema_dict
        self.max_keys = max_keys
        self.max_list_len = max_list_len
        self.max_str_len = max_str_len
        self.validators = validators or {}

        # Validate the schema itself
        self._validate_schema()

    def _validate_schema(self) -> None:
        """Validate that the schema is well-formed."""
        if not isinstance(self.schema_dict, dict):
            raise SchemaError("Schema must be a dictionary")

        for key, value in self.schema_dict.items():
            if not isinstance(key, str):
                raise SchemaError(f"Schema keys must be strings, got {type(key)}")

            if value is None:
                continue  # Optional field

            if isinstance(value, type):
                # Simple type validation
                if value not in (str, int, float, bool, list, dict):
                    raise SchemaError(f"Unsupported type {value}")
            elif isinstance(value, dict):
                # Nested schema
                Schema(value)
            elif isinstance(value, list):
                # List schema
                if len(value) != 1:
                    raise SchemaError("List schemas must have exactly one element")
                if isinstance(value[0], type):
                    if value[0] not in (str, int, float, bool, list, dict):
                        raise SchemaError(f"Unsupported list element type {value[0]}")
                elif isinstance(value[0], dict):
                    Schema(value[0])
                else:
                    raise SchemaError(f"Invalid list element schema: {value[0]}")
            else:
                raise SchemaError(f"Invalid schema value type: {type(value)}")

    def to_dict(self) -> dict[str, Any]:
        """Convert schema to dictionary representation."""
        return {
            "schema": self.schema_dict,
            "max_keys": self.max_keys,
            "max_list_len": self.max_list_len,
            "max_str_len": self.max_str_len,
            "validators": list(self.validators.keys()) if self.validators else None,
        }

    def _serialize_schema_dict(self, schema_dict: dict[str, Any]) -> dict[str, Any]:
        """Serialize schema dict with type names instead of Python types."""
        serialized = {}
        for key, value in schema_dict.items():
            if value is None:
                serialized[key] = None
            elif isinstance(value, type):
                # Convert Python types to string names
                type_map = {
                    str: "string",
                    int: "integer",
                    float: "float",
                    bool: "boolean",
                    list: "list",
                    dict: "object",
                }
                serialized[key] = type_map.get(value, str(value))
            elif isinstance(value, dict):
                serialized[key] = self._serialize_schema_dict(value)
            elif isinstance(value, list):
                if len(value) == 1:
                    element = value[0]
                    if isinstance(element, type):
                        type_map = {
                            str: "string",
                            int: "integer",
                            float: "float",
                            bool: "boolean",
                            list: "list",
                            dict: "object",
                        }
                        serialized[key] = [type_map.get(element, str(element))]
                    elif isinstance(element, dict):
                        serialized[key] = [self._serialize_schema_dict(element)]
                    else:
                        serialized[key] = [str(element)]
                else:
                    serialized[key] = [
                        self._serialize_schema_dict(item)
                        if isinstance(item, dict)
                        else str(item)
                        for item in value
                    ]
            else:
                serialized[key] = str(value)
        return serialized

    def _deserialize_schema_dict(self, schema_dict: dict[str, Any]) -> dict[str, Any]:
        """Deserialize schema dict with string type names to Python types."""
        deserialized = {}
        for key, value in schema_dict.items():
            if value is None:
                deserialized[key] = None
            elif isinstance(value, str):
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
                    "object": dict,
                    "dict": dict,
                }
                deserialized[key] = type_map.get(value.lower(), value)
            elif isinstance(value, dict):
                deserialized[key] = self._deserialize_schema_dict(value)
            elif isinstance(value, list):
                if len(value) == 1:
                    element = value[0]
                    if isinstance(element, str):
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
                            "object": dict,
                            "dict": dict,
                        }
                        deserialized[key] = [type_map.get(element.lower(), element)]
                    elif isinstance(element, dict):
                        deserialized[key] = [self._deserialize_schema_dict(element)]
                    else:
                        deserialized[key] = [element]
                else:
                    deserialized[key] = [
                        self._deserialize_schema_dict(item)
                        if isinstance(item, dict)
                        else item
                        for item in value
                    ]
            else:
                deserialized[key] = value
        return deserialized

    def to_json(self) -> str:
        """Convert schema to JSON string."""
        serialized_dict = {
            "schema": self._serialize_schema_dict(self.schema_dict),
            "max_keys": self.max_keys,
            "max_list_len": self.max_list_len,
            "max_str_len": self.max_str_len,
            "validators": list(self.validators.keys()) if self.validators else None,
        }
        return json.dumps(serialized_dict, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Schema":
        """Create schema from dictionary representation."""
        schema_dict = data["schema"]
        # Deserialize if the schema contains string type names
        if isinstance(schema_dict, dict):
            # Check if any values are strings that look like type names
            has_string_types = any(
                isinstance(v, str)
                and v.lower()
                in [
                    "string",
                    "integer",
                    "int",
                    "float",
                    "number",
                    "boolean",
                    "bool",
                    "list",
                    "array",
                    "object",
                    "dict",
                ]
                for v in schema_dict.values()
            )
            if has_string_types:
                schema_dict = cls._deserialize_schema_dict_static(schema_dict)

        return cls(
            schema_dict=schema_dict,
            max_keys=data.get("max_keys"),
            max_list_len=data.get("max_list_len"),
            max_str_len=data.get("max_str_len"),
        )

    @classmethod
    def _deserialize_schema_dict_static(
        cls, schema_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """Static method to deserialize schema dict with string type names to Python types."""
        deserialized = {}
        for key, value in schema_dict.items():
            if value is None:
                deserialized[key] = None
            elif isinstance(value, str):
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
                    "object": dict,
                    "dict": dict,
                }
                deserialized[key] = type_map.get(value.lower(), value)
            elif isinstance(value, dict):
                deserialized[key] = cls._deserialize_schema_dict_static(value)
            elif isinstance(value, list):
                if len(value) == 1:
                    element = value[0]
                    if isinstance(element, str):
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
                            "object": dict,
                            "dict": dict,
                        }
                        deserialized[key] = [type_map.get(element.lower(), element)]
                    elif isinstance(element, dict):
                        deserialized[key] = [
                            cls._deserialize_schema_dict_static(element)
                        ]
                    else:
                        deserialized[key] = [element]
                else:
                    deserialized[key] = [
                        cls._deserialize_schema_dict_static(item)
                        if isinstance(item, dict)
                        else item
                        for item in value
                    ]
            else:
                deserialized[key] = value
        return deserialized

    @classmethod
    def from_json(cls, json_str: str) -> "Schema":
        """Create schema from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
