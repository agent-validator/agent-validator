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
        context={"correlation_id": "abc123"}  # Optional correlation ID for tracking
    )
    print("✅ Validation successful!")
    print(result)
except ValidationError as e:
    print(f"❌ Validation failed: {e}")
    print(f"Correlation ID: {e.correlation_id}")  # For debugging
```

### 🖥️ CLI Usage

```bash
# Test validation with files
agent-validator test schema.json input.json --mode COERCE

# View recent logs
agent-validator logs -n 20

# View cloud logs
agent-validator cloud-logs -n 20

# Open web dashboard (secure proxy)
agent-validator dashboard

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

### 📄 Schema File Formats

When using the CLI with JSON files, you can use either format:

#### **Direct Schema Format** (Recommended)

```json
{
  "name": "string",
  "age": "integer",
  "email": "string",
  "is_active": "boolean",
  "tags": ["string"],
  "metadata": {
    "source": "string",
    "version": "string"
  }
}
```

#### **Wrapped Schema Format**

```json
{
  "schema": {
    "name": "string",
    "age": "integer",
    "email": "string",
    "is_active": "boolean"
  }
}
```

**Supported string types**: `string`, `integer`, `int`, `float`, `number`, `boolean`, `bool`, `list`, `array`, `dict`, `object`

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
  "context": { "correlation_id": "abc123" },
  "output_sample": "{\"name\": \"John\", \"age\": 30}"
}
```

**Correlation IDs** are automatically generated for each validation attempt and help you:

- 🔍 **Track specific validations** across logs and error messages
- 🐛 **Debug issues** by correlating errors with specific validation attempts
- 📊 **Monitor performance** by tracking validation duration and retry attempts
- 🔗 **Link related operations** when using retry functions

When viewing logs with `agent-validator logs`, logs are displayed in a clear table format:

```bash
┌─────────────────────────────────────┬────────┬─────────────┬─────────┬──────────┬─────────────┬─────────┬─────────┐
│ Timestamp                           │ Status │ Correlation │ Mode    │ Attempts │ Duration    │ Errors  │ Size    │
├─────────────────────────────────────┼────────┼─────────────┼─────────┼──────────┼─────────────┼─────────┼─────────┤
│ 2025-08-30 18:40:00                 │      ✗ │        none │  strict │        1 │         0ms │       2 │    45B  │
│ 2025-08-30 18:40:00                 │      ✓ │        none │  coerce │        1 │         0ms │       0 │    45B  │
└─────────────────────────────────────┴────────┴─────────────┴─────────┴──────────┴─────────────┴─────────┴─────────┘
```

Correlation IDs are truncated for readability and show `[none]` when not set.

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

### 🔐 Webhook Secret Management

For enhanced security, generate a webhook secret for HMAC signature validation:

```bash
# Generate a new webhook secret
agent-validator webhook --generate

# Check webhook status
agent-validator webhook --status

# Show current webhook secret
agent-validator webhook --show

# Revoke webhook secret
agent-validator webhook --revoke
```

**Security Features:**

- ✅ **One-time display**: Webhook secrets are only shown once when generated
- ✅ **Secure storage**: Secrets are stored encrypted in the database
- ✅ **User isolation**: Each license key has its own webhook secret
- ✅ **Revocation**: Users can revoke and regenerate secrets as needed

#### Using HMAC Signatures

Once you have a webhook secret, requests can include an HMAC signature:

```python
import hmac
import hashlib

# Create signature
signature = hmac.new(
    webhook_secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()

# Include in request headers
headers = {
    "license-key": "your-license-key",
    "x-signature": signature
}
```

#### Security Notes

- **One-time display**: Webhook secrets are only shown once when generated
- **Secure storage**: Secrets are stored encrypted in the database
- **User isolation**: Each license key has its own webhook secret
- **Revocation**: Users can revoke and regenerate secrets as needed

### 🌐 Web Dashboard

Access your validation logs through a secure web dashboard:

```bash
# Configure your license key
agent-validator config --set-license-key your-license-key

# Open dashboard with secure local proxy
agent-validator dashboard
```

This opens a local proxy server at `http://localhost:8080` that securely forwards requests to the cloud API with proper authentication headers. The dashboard shows:

- Recent validation attempts
- Success/failure rates
- Performance metrics
- Error details
- Correlation IDs for debugging

**Security Features:**

- ✅ No credentials in URLs
- ✅ Secure header authentication
- ✅ User data isolation
- ✅ Local proxy prevents credential exposure

---

## ⚙️ Configuration

### 🌍 Environment Variables

```bash
export AGENT_VALIDATOR_LICENSE_KEY="your-license-key"
export AGENT_VALIDATOR_WEBHOOK_SECRET="your-webhook-secret"
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

### 🔄 Configuration Precedence

Configuration values are loaded in the following order (highest to lowest priority):

1. **CLI Arguments** (highest priority)

   ```bash
   agent-validator test schema.json input.json --mode COERCE --timeout-s 30
   ```

2. **Environment Variables**

   ```bash
   export AGENT_VALIDATOR_MODE="COERCE"
   export AGENT_VALIDATOR_TIMEOUT_S="30"
   ```

3. **Configuration File** (lowest priority)
   ```toml
   # ~/.agent_validator/config.toml
   mode = "STRICT"
   timeout_s = 20
   ```

**Example**: If you have `timeout_s = 20` in your config file, but set `export AGENT_VALIDATOR_TIMEOUT_S="30"`, the environment variable (30 seconds) will take precedence.

**Note**: CLI arguments always override environment variables and config file settings.

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

# View local logs
agent-validator logs [-n <number>] [--clear]

# View cloud logs
agent-validator cloud-logs [-n <number>]

# Open web dashboard
agent-validator dashboard [--port <port>] [--url] [--open]

# Generate correlation ID
agent-validator id

# Manage configuration
agent-validator config [--show] [--show-secrets] [--set-license-key <key>] [--set-endpoint <url>] [--set-webhook-secret <secret>] [--set-log-to-cloud <true|false>]

# Manage webhook secrets
agent-validator webhook [--generate] [--status] [--show] [--revoke] [--force]
```

### 📊 Exit Codes

- `0`: Success
- `1`: General error
- `2`: Validation failed

### 🔒 Security Notes

- **Configuration Display**: By default, sensitive values (license key, webhook secret) are masked as `***` when showing configuration
- **Show Secrets**: Use `--show-secrets` flag to display actual values for debugging/verification
- **Example**:

  ```bash
  # Default (masked)
  agent-validator config --show
  # Output: license_key: ***

  # With secrets visible
  agent-validator config --show --show-secrets
  # Output: license_key: my-actual-key
  ```

---

## 🛠️ Development

### 📦 Installation

```bash
git clone https://github.com/agent-validator/agent-validator.git
cd agent-validator
pip install -e ".[dev]"
```

**Note**: The `[dev]` extras include build tools (`build`, `twine`) needed for creating releases.

### 🧪 Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
pytest --cov=agent_validator

# Run property-based tests
python -m pytest tests/property/ -v

# Run type checking
mypy agent_validator cli

# Run linting
ruff check .
black --check .
isort --check-only .

# Run smoke tests (isolated environment)
python smoke_tests/smoke_tests.py
```

### 🔧 Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

### 🚀 Smoke Tests

Smoke tests verify the complete user experience in an isolated environment:

```bash
# Run comprehensive smoke tests
python smoke_tests/smoke_tests.py

# With backend URL for cloud testing
python smoke_tests/smoke_tests.py --backend-url http://localhost:9090
```

**What gets tested:**

- ✅ Package installation in isolated environment
- ✅ CLI command availability and functionality
- ✅ Library imports and basic operations
- ✅ Configuration management
- ✅ Log generation and retrieval
- ✅ Schema validation (strict and coerce modes)
- ✅ Error handling and edge cases

**Benefits:**

- 🛡️ No pollution to your development environment
- 🔄 Clean testing environment every time
- 🧪 Tests real installation and usage scenarios
- 🚀 Perfect for CI/CD integration

### 📦 Releasing New Versions

The project uses automated CI/CD for releases. When you push a version tag, the CI automatically builds and publishes to PyPI.

#### 1. **Update Version**

Update the version in `agent_validator/version.py`:

```python
__version__ = "1.0.1"  # Increment version number
```

#### 2. **Update CHANGELOG**

Add a new entry to `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [1.0.1] - 2025-01-01

### Added

- New feature description

### Changed

- Breaking change description

### Fixed

- Bug fix description
```

#### 3. **Run Pre-release Checks**

```bash
# Install build dependencies (if not already installed)
pip install -e ".[dev]"

# Run all tests
python -m pytest tests/ -v

# Run smoke tests
python smoke_tests/smoke_tests.py

# Check code quality (matches CI)
ruff check .
mypy agent_validator cli

# Verify package builds
python -m build
```

#### 4. **Commit and Push Changes**

```bash
# Commit version and changelog updates
git add agent_validator/version.py CHANGELOG.md
git commit -m "Release v1.0.1"
git push origin master
```

#### 5. **Create and Push Git Tag**

```bash
# Create version tag
git tag v1.0.1

# Push tag to trigger automated release
git push origin v1.0.1
```

**That's it!** 🚀 The CI/CD pipeline will automatically:

- ✅ Run tests across Python 3.9, 3.10, 3.11, and 3.12
- ✅ Run linting and type checking
- ✅ Build the package
- ✅ Publish to PyPI (if tag starts with `v`)

#### 6. **Verify Release**

After the CI completes (usually 2-3 minutes):

```bash
# Test installation from PyPI
pip install agent-validator==1.0.1 --force-reinstall

# Verify functionality
agent-validator --help
python -c "import agent_validator; print(agent_validator.__version__)"
```

#### 7. **Create GitHub Release**

- Go to [GitHub Releases](https://github.com/agent-validator/agent-validator/releases)
- Click "Create a new release"
- Select the tag you just pushed
- Copy the changelog content
- Publish the release

**Release Checklist:**

- [ ] Version updated in `agent_validator/version.py`
- [ ] CHANGELOG.md updated
- [ ] All tests pass locally
- [ ] Smoke tests pass
- [ ] Code quality checks pass
- [ ] Package builds successfully
- [ ] Changes committed and pushed to master
- [ ] Git tag created and pushed
- [ ] CI/CD pipeline completes successfully
- [ ] Installation from PyPI verified
- [ ] GitHub release created with changelog

**CI/CD Pipeline Details:**

The `.github/workflows/ci.yml` workflow automatically:

- **Tests**: Runs on Python 3.9, 3.10, 3.11, 3.12
- **Quality**: Runs `ruff check` and `mypy`
- **Coverage**: Generates and uploads coverage reports
- **Publishing**: Automatically publishes to PyPI when a tag starting with `v` is pushed
- **Security**: Uses GitHub secrets for PyPI authentication

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

**Q: How do I access the web dashboard securely?**  
A: Use `agent-validator dashboard` which creates a secure local proxy server. Never put your license key in URLs - the CLI handles authentication securely via headers.

**Q: How do I verify my license key is set correctly?**  
A: Use `agent-validator config --show --show-secrets` to display the actual license key value. By default, sensitive values are masked as `***` for security.

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
- [x] Web dashboard for monitoring
- [ ] Alerting and notifications
- [ ] Schema versioning
- [ ] Performance metrics

---

<div align="center">

**Made with ❤️ by the Agent Validator community**

[![GitHub stars](https://img.shields.io/github/stars/agent-validator/agent-validator?style=social)](https://github.com/agent-validator/agent-validator)
[![GitHub forks](https://img.shields.io/github/forks/agent-validator/agent-validator?style=social)](https://github.com/agent-validator/agent-validator)

</div>
