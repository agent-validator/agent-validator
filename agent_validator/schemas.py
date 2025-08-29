"""Schema definition and validation logic."""

import json
from typing import Any, Dict, List, Optional, Union, Callable
from .errors import SchemaError
from .typing_ import ValidatorFunction


class Schema:
    """Schema definition for validating agent outputs."""
    
    def __init__(
        self,
        schema_dict: Dict[str, Any],
        max_keys: Optional[int] = None,
        max_list_len: Optional[int] = None,
        max_str_len: Optional[int] = None,
        validators: Optional[Dict[str, ValidatorFunction]] = None,
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary representation."""
        return {
            "schema": self.schema_dict,
            "max_keys": self.max_keys,
            "max_list_len": self.max_list_len,
            "max_str_len": self.max_str_len,
            "validators": list(self.validators.keys()) if self.validators else None,
        }
    
    def to_json(self) -> str:
        """Convert schema to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Schema":
        """Create schema from dictionary representation."""
        schema_dict = data["schema"]
        return cls(
            schema_dict=schema_dict,
            max_keys=data.get("max_keys"),
            max_list_len=data.get("max_list_len"),
            max_str_len=data.get("max_str_len"),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "Schema":
        """Create schema from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
