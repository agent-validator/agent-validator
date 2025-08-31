"""Basic example of using agent_validator."""

import json

from agent_validator import Schema, ValidationMode, validate


def call_agent(prompt: str, context: dict) -> str:
    """Mock agent function that returns structured data."""
    # Simulate an agent that sometimes returns malformed output
    import random

    if random.random() < 0.3:  # 30% chance of malformed output
        return "This is not valid JSON"

    # Return valid JSON
    return json.dumps(
        {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com",
            "tags": ["developer", "python"],
        }
    )


def main():
    # Define schema
    schema = Schema({"name": str, "age": int, "email": str, "tags": [str]})

    # Mock agent output (could be malformed)
    agent_output = call_agent("Generate user profile", {"task_id": "123"})

    print(f"Agent output: {agent_output}")

    try:
        # Validate with retries
        result = validate(
            agent_output,
            schema,
            retry_fn=call_agent,
            retries=2,
            mode=ValidationMode.COERCE,
            context={"task_id": "123"},
        )

        print("✓ Validation successful!")
        print(f"Result: {json.dumps(result, indent=2)}")

    except Exception as e:
        print(f"✗ Validation failed: {e}")


if __name__ == "__main__":
    main()
