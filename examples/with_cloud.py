"""Example using agent_validator with cloud logging."""

import json
import os
from agent_validator import validate, Schema, ValidationMode, Config


def call_agent(prompt: str, context: dict) -> str:
    """Mock agent function that returns structured data."""
    return json.dumps({
        "name": "Alice Smith",
        "age": "25",  # String that needs coercion
        "email": "alice@example.com",
        "is_active": "true",  # String that needs coercion
        "preferences": {
            "theme": "dark",
            "notifications": True
        }
    })


def main():
    # Configure for cloud logging
    config = Config(
        log_to_cloud=True,
        api_key=os.getenv("AGENT_VALIDATOR_API_KEY"),
        cloud_endpoint=os.getenv("AGENT_VALIDATOR_ENDPOINT", "https://api.agentvalidator.dev")
    )
    
    # Define schema with nested structure
    schema = Schema({
        "name": str,
        "age": int,
        "email": str,
        "is_active": bool,
        "preferences": {
            "theme": str,
            "notifications": bool
        }
    })
    
    # Mock agent output
    agent_output = call_agent("Generate user profile", {"task_id": "456"})
    
    print(f"Agent output: {agent_output}")
    
    try:
        # Validate with cloud logging
        result = validate(
            agent_output,
            schema,
            retry_fn=call_agent,
            retries=1,
            mode=ValidationMode.COERCE,
            log_to_cloud=True,
            context={
                "task_id": "456",
                "user_id": "user_123",
                "environment": "production"
            },
            config=config
        )
        
        print("✓ Validation successful!")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Show that coercion worked
        print(f"Age type: {type(result['age'])} (was coerced from string)")
        print(f"is_active type: {type(result['is_active'])} (was coerced from string)")
        
    except Exception as e:
        print(f"✗ Validation failed: {e}")


if __name__ == "__main__":
    main()
