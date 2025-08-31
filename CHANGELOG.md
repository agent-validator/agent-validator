# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial release of agent-validator
- Core validation functionality with Python dict schemas
- Support for strict and coerce validation modes
- Automatic retry logic with exponential backoff
- Local JSON Lines logging with automatic redaction
- Cloud logging with secure authentication
- CLI interface for testing and log management
- Configuration management with environment variables and TOML files
- Size limits to prevent abuse
- Comprehensive test suite with property-based testing

### Features

- Schema validation for primitive types (str, int, float, bool)
- List and nested object validation
- Optional field support
- Type coercion for safe conversions
- Sensitive data redaction (API keys, emails, phone numbers, etc.)
- Correlation ID tracking for debugging
- Configurable limits and timeouts
- HMAC signature support for cloud logging

### CLI Commands

- `agent-validator test` - Test validation with schema and input files
- `agent-validator logs` - View recent validation logs
- `agent-validator id` - Generate correlation ID
- `agent-validator config` - Manage configuration

## [1.0.0] - 2025-08-30

### Added

- Initial release
