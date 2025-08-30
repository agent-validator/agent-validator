# 🚀 Agent Validator

> **A simple drop-in tool to validate LLM/agent outputs against schemas with automatic retries, logging, and optional cloud monitoring.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## ✨ Features

- 🔍 **Schema Validation**: Validate JSON outputs against Python dict schemas
- 🔄 **Automatic Retries**: Retry failed validations with exponential backoff
- 🔧 **Type Coercion**: Optional safe type coercion (e.g., `"42"` → `42`)
- 📝 **Local Logging**: JSON Lines logging with automatic redaction
- ☁️ **Cloud Monitoring**: Optional cloud logging with secure authentication
- 🛠️ **CLI Tools**: Command-line interface for testing and log management
- 🛡️ **Size Limits**: Configurable limits to prevent abuse

---

## 🚀 Quick Start

### 📦 Installation

```bash
pip install agent-validator
```

### 💻 Basic Usage

```python
from agent_validator import validate, Schema, ValidationMode

# Define your schema
schema = Schema({
    "name": str,
    "age": int,
    "email": str,
    "tags": [str]
})

# Validate agent output
try:
    result = validate(
        agent_output,  # Your agent's output (string or dict)
        schema,
        retry_fn=call_agent,  # Function to retry if validation fails
        retries=2,
        mode=ValidationMode.COERCE,  # Allow type coercion
        context={"task_id": "abc123"}
    )
    print("✅ Validation successful!")
    print(result)
except ValidationError as e:
    print(f"❌ Validation failed: {e}")
```

### 🖥️ CLI Usage

```bash
# Test validation with files
agent-validator test schema.json input.json --mode COERCE

# View recent logs
agent-validator logs -n 20

# Generate correlation ID
agent-validator id

# Configure cloud logging
agent-validator config --set-license-key YOUR_LICENSE_KEY
agent-validator config --set-log-to-cloud true
```

---

## 📋 Schema Definition

Schemas are defined using Python dictionaries with type annotations:

```python
schema = Schema({
    "name": str,           # Required string field
    "age": int,            # Required integer field
    "email": str,          # Required string field
    "is_active": bool,     # Required boolean field
    "score": float,        # Required float field
    "tags": [str],         # List of strings
    "metadata": None,      # Optional field (can be omitted)
    "address": {           # Nested object
        "street": str,
        "city": str,
        "zip": str
    },
    "scores": [int]        # List of integers
})
```

### 🎯 Supported Types

- **Primitives**: `str`, `int`, `float`, `bool`
- **Lists**: `[type]` for lists of that type
- **Objects**: `dict` for nested objects
- **Optional**: `None` for optional fields

---

## 🔄 Validation Modes

### 🚫 Strict Mode (Default)

No type coercion allowed. Input must match schema exactly.

```python
schema = Schema({"age": int})
data = {"age": "30"}  # String instead of int

# This will fail
validate(data, schema, mode=ValidationMode.STRICT)
```

### 🔧 Coerce Mode

Safe type coercion is performed:

```python
schema = Schema({"age": int, "is_active": bool})
data = {"age": "30", "is_active": "true"}

# This will succeed and coerce types
result = validate(data, schema, mode=ValidationMode.COERCE)
# result = {"age": 30, "is_active": True}
```

#### 🔄 Coercion Rules

| Input Type | Target Type | Coercion |
| ---------- | ----------- | -------- |
| `"42"`     | `int`       | `42`     |
| `"42.5"`   | `float`     | `42.5`   |
| `"true"`   | `bool`      | `True`   |
| `"false"`  | `bool`      | `False`  |
| `"1"`      | `bool`      | `True`   |
| `"0"`      | `bool`      | `False`  |
| `"yes"`    | `bool`      | `True`   |
| `"no"`     | `bool`      | `False`  |
| `"on"`     | `bool`      | `True`   |
| `"off"`    | `bool`      | `False`  |

---

## 🔄 Retry Logic

When validation fails and a `retry_fn` is provided, the system will automatically retry:

```python
def call_agent(prompt: str, context: dict) -> str:
    """Your agent function that returns JSON string."""
    # Call your LLM/agent here
    return json.dumps({"name": "John", "age": 30})

result = validate(
    malformed_output,
    schema,
    retry_fn=call_agent,
    retries=2,  # Retry up to 2 times
    timeout_s=20  # 20 second timeout per attempt
)
```

### ⚡ Retry Behavior

- **Exponential Backoff**: Delays increase with each retry (0.5s, 1s, 2s)
- **Jitter**: Random variation to prevent thundering herd
- **Timeout**: Per-attempt timeout to prevent hanging
- **Context Preservation**: Original context is passed to retry function

---

## 📝 Logging

### 💾 Local Logging

All validation attempts are logged to `~/.agent_validator/logs/YYYY-MM-DD.jsonl`:

```json
{
  "ts": "2023-12-01T10:30:00Z",
  "correlation_id": "abc123-def456",
  "valid": true,
  "errors": [],
  "attempts": 1,
  "duration_ms": 150,
  "mode": "coerce",
  "limits": {
    "max_output_bytes": 131072,
    "max_str_len": 8192,
    "max_list_len": 2048,
    "max_dict_keys": 512
  },
  "context": { "task_id": "abc123" },
  "output_sample": "{\"name\": \"John\", \"age\": 30}"
}
```

### ☁️ Cloud Logging

Enable cloud logging for monitoring and recovery:

```python
from agent_validator import Config

config = Config(
    log_to_cloud=True,
    license_key="your-license-key",
    cloud_endpoint="https://api.agentvalidator.dev"
)

result = validate(
    agent_output,
    schema,
    log_to_cloud=True,
    config=config
)
```

---

## ⚙️ Configuration

### 🌍 Environment Variables

```bash
export AGENT_VALIDATOR_LICENSE_KEY="your-license-key"
export AGENT_VALIDATOR_LOG_TO_CLOUD="1"
export AGENT_VALIDATOR_ENDPOINT="https://api.agentvalidator.dev"
export AGENT_VALIDATOR_MAX_OUTPUT_BYTES="131072"
export AGENT_VALIDATOR_MAX_STR_LEN="8192"
export AGENT_VALIDATOR_MAX_LIST_LEN="2048"
export AGENT_VALIDATOR_MAX_DICT_KEYS="512"
export AGENT_VALIDATOR_TIMEOUT_S="20"
export AGENT_VALIDATOR_RETRIES="2"
```

### 📄 Configuration File

Configuration is stored in `~/.agent_validator/config.toml`:

```toml
max_output_bytes = 131072
max_str_len = 8192
max_list_len = 2048
max_dict_keys = 512
log_to_cloud = false
cloud_endpoint = "https://api.agentvalidator.dev"
timeout_s = 20
retries = 2
license_key = "your-license-key"
webhook_secret = "your-webhook-secret"
```

---

## 🔒 Security & Privacy

### 🚫 Redaction

Sensitive data is automatically redacted before logging:

- **API Keys**: `sk-1234567890abcdef` → `[REDACTED]`
- **JWT Tokens**: `Bearer eyJ...` → `[REDACTED]`
- **Emails**: `john@example.com` → `j***n@example.com`
- **Phone Numbers**: `+1-555-123-4567` → `***-***-4567`
- **SSNs**: `123-45-6789` → `***-**-6789`
- **Credit Cards**: `1234-5678-9012-3456` → `************3456`
- **Passwords**: `secret123` → `[REDACTED]`

### 🔧 Custom Redaction Patterns

```python
from agent_validator.redact import add_redaction_pattern

# Add custom pattern
add_redaction_pattern("custom_token", r"custom-[a-zA-Z0-9]{20,}")
```

---

## 📏 Size Limits

Default limits to prevent abuse:

| Limit              | Default | Description              |
| ------------------ | ------- | ------------------------ |
| `max_output_bytes` | 131,072 | Total JSON size in bytes |
| `max_str_len`      | 8,192   | Maximum string length    |
| `max_list_len`     | 2,048   | Maximum list length      |
| `max_dict_keys`    | 512     | Maximum dictionary keys  |

---

## ⚠️ Error Handling

### 🚨 ValidationError

Raised when validation fails after all retries:

```python
from agent_validator import ValidationError

try:
    result = validate(data, schema)
except ValidationError as e:
    print(f"Path: {e.path}")
    print(f"Reason: {e.reason}")
    print(f"Attempt: {e.attempt}")
    print(f"Correlation ID: {e.correlation_id}")
```

### 📋 SchemaError

Raised when schema definition is invalid:

```python
from agent_validator import SchemaError

try:
    schema = Schema({"name": bytes})  # Unsupported type
except SchemaError as e:
    print(f"Schema error: {e}")
```

### ☁️ CloudLogError

Raised when cloud logging fails (non-fatal):

```python
from agent_validator import CloudLogError

try:
    result = validate(data, schema, log_to_cloud=True)
except CloudLogError as e:
    print(f"Cloud logging failed: {e}")
    # Validation still succeeds
```

---

## 💡 Examples

### 🎯 Basic Example

```python
from agent_validator import validate, Schema, ValidationMode

def call_agent(prompt: str, context: dict) -> str:
    """Mock agent function."""
    import random
    if random.random() < 0.3:
        return "This is not valid JSON"
    return '{"name": "John", "age": 30, "email": "john@example.com"}'

schema = Schema({
    "name": str,
    "age": int,
    "email": str
})

result = validate(
    call_agent("", {}),
    schema,
    retry_fn=call_agent,
    retries=2,
    mode=ValidationMode.COERCE
)
```

### ☁️ With Cloud Logging

```python
from agent_validator import validate, Schema, Config

config = Config(
    log_to_cloud=True,
    license_key=os.getenv("AGENT_VALIDATOR_LICENSE_KEY")
)

schema = Schema({
    "user": {
        "name": str,
        "age": int,
        "preferences": {
            "theme": str,
            "notifications": bool
        }
    }
})

result = validate(
    agent_output,
    schema,
    log_to_cloud=True,
    config=config,
    context={"user_id": "123", "environment": "production"}
)
```

---

## 🖥️ CLI Reference

### 🛠️ Commands

```bash
# Test validation
agent-validator test <schema.json> <input.json> [--mode STRICT|COERCE]

# View logs
agent-validator logs [-n <number>] [--clear]

# Generate correlation ID
agent-validator id

# Manage configuration
agent-validator config [--show] [--set-license-key <key>] [--set-endpoint <url>] [--set-log-to-cloud <true|false>]
```

### 📊 Exit Codes

- `0`: Success
- `1`: General error
- `2`: Validation failed

---

## 🛠️ Development

### 📦 Installation

```bash
git clone https://github.com/agent-validator/agent-validator.git
cd agent-validator
pip install -e ".[dev]"
```

### 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agent_validator

# Run property-based tests
pytest tests/property/

# Run type checking
mypy agent_validator cli

# Run linting
ruff check .
black --check .
isort --check-only .
```

### 🔧 Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

---

## 🤝 Contributing

1. 🍴 Fork the repository
2. 🌿 Create a feature branch
3. ✏️ Make your changes
4. 🧪 Add tests
5. ✅ Run the test suite
6. 📤 Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## ❓ FAQ

**Q: Can I use this with any LLM/agent?**  
A: Yes! The library is framework-agnostic. Just pass your agent's output to the `validate` function.

**Q: What happens if my agent returns malformed JSON?**  
A: In strict mode, it will fail immediately. In coerce mode, it will try to parse as JSON first, then fall back to treating it as a plain string.

**Q: How do I handle sensitive data in logs?**  
A: Sensitive data is automatically redacted before logging. You can also add custom redaction patterns.

**Q: Can I use this in production?**  
A: Yes! The library is designed for production use with proper error handling, logging, and monitoring capabilities.

**Q: What's the performance impact?**  
A: Minimal. Validation is fast, and logging is asynchronous. The main overhead comes from retry attempts when validation fails.

**Q: Can I use my own schema format?**  
A: Currently only Python dict schemas are supported. JSONSchema support is planned for v0.1.

---

## 🗺️ Roadmap

- [ ] JSONSchema import/export
- [ ] Pydantic model support
- [ ] Custom validators per field
- [ ] Schema composition and inheritance
- [ ] Web dashboard for monitoring
- [ ] Alerting and notifications
- [ ] Schema versioning
- [ ] Performance metrics

---

<div align="center">

**Made with ❤️ by the Agent Validator community**

[![GitHub stars](https://img.shields.io/github/stars/agent-validator/agent-validator?style=social)](https://github.com/agent-validator/agent-validator)
[![GitHub forks](https://img.shields.io/github/forks/agent-validator/agent-validator?style=social)](https://github.com/agent-validator/agent-validator)

</div>
