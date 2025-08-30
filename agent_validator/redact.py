"""Redaction utilities for sensitive data."""

import re
from typing import Any, Dict, List, Optional, Union


# Default redaction patterns
DEFAULT_PATTERNS = {
    "license_key": r"(?i)(license[_-]?key|licensekey)[\s]*[:=][\s]*['\"]?([a-zA-Z0-9_-]{20,})['\"]?",
    "license_key_value": r"^license-[a-zA-Z0-9_-]{20,}$",
    "api_key": r"(?i)(api[_-]?key|apikey)[\s]*[:=][\s]*['\"]?([a-zA-Z0-9_-]{20,})['\"]?",
    "jwt": r"(?i)(bearer|jwt|token)[\s]*[:=][\s]*['\"]?([a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)['\"]?",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"(?i)(phone|tel|mobile)[\s]*[:=][\s]*['\"]?(\+?[\d\s\-\(\)]{10,})['\"]?",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "password": r"(?i)(password|passwd|pwd)[\s]*[:=][\s]*['\"]?([^\s'\"]+)['\"]?",
    "secret": r"(?i)(secret|key)[\s]*[:=][\s]*['\"]?([a-zA-Z0-9_-]{20,})['\"]?",
}


class Redactor:
    """Redactor for sensitive data patterns."""
    
    def __init__(self, patterns: Optional[Dict[str, str]] = None):
        """
        Initialize redactor with patterns.
        
        Args:
            patterns: Dictionary of pattern_name -> regex_pattern
        """
        self.patterns = patterns or DEFAULT_PATTERNS.copy()
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for name, pattern in self.patterns.items()
        }
    
    def redact_text(self, text: str) -> str:
        """
        Redact sensitive data from text.
        
        Args:
            text: Text to redact
            
        Returns:
            Redacted text
        """
        if not isinstance(text, str):
            return text
        
        redacted = text
        
        for pattern_name, pattern in self.compiled_patterns.items():
            if pattern_name in ["license_key", "license_key_value", "api_key", "jwt", "password", "secret"]:
                # Replace the entire match
                redacted = pattern.sub("[REDACTED]", redacted)
            elif pattern_name == "email":
                # Replace with redacted email
                redacted = pattern.sub(lambda m: self._redact_email(m.group(0)), redacted)
            elif pattern_name == "phone":
                # Replace with redacted phone
                redacted = pattern.sub(lambda m: self._redact_phone(m.group(0)), redacted)
            elif pattern_name == "ssn":
                # Replace with redacted SSN
                redacted = pattern.sub(lambda m: self._redact_ssn(m.group(0)), redacted)
            elif pattern_name == "credit_card":
                # Replace with redacted credit card
                redacted = pattern.sub(lambda m: self._redact_credit_card(m.group(0)), redacted)
        
        return redacted
    
    def redact_dict(self, data: Any, max_depth: int = 10) -> Any:
        """
        Recursively redact sensitive data from dictionary or other data structures.
        
        Args:
            data: Data to redact
            max_depth: Maximum recursion depth
            
        Returns:
            Redacted data
        """
        if max_depth <= 0:
            return "[REDACTED - MAX DEPTH]"
        
        if isinstance(data, dict):
            return {
                key: self.redact_dict(value, max_depth - 1)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                self.redact_dict(item, max_depth - 1)
                for item in data
            ]
        elif isinstance(data, str):
            return self.redact_text(data)
        else:
            return data
    
    def _redact_email(self, email: str) -> str:
        """Redact email address."""
        if "@" not in email:
            return "[REDACTED]"
        
        username, domain = email.split("@", 1)
        if len(username) <= 2:
            redacted_username = "*" * len(username)
        else:
            redacted_username = username[0] + "*" * (len(username) - 2) + username[-1]
        
        return f"{redacted_username}@{domain}"
    
    def _redact_phone(self, phone: str) -> str:
        """Redact phone number."""
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 4:
            return "[REDACTED]"
        
        return f"***-***-{digits[-4:]}"
    
    def _redact_ssn(self, ssn: str) -> str:
        """Redact social security number."""
        return "***-**-" + ssn[-4:]
    
    def _redact_credit_card(self, card: str) -> str:
        """Redact credit card number."""
        digits = re.sub(r"\D", "", card)
        if len(digits) < 4:
            return "[REDACTED]"
        
        return "*" * (len(digits) - 4) + digits[-4:]


# Global redactor instance
_default_redactor = Redactor()


def redact_sensitive_data(data: Any, patterns: Optional[Dict[str, str]] = None) -> Any:
    """
    Redact sensitive data from any data structure.
    
    Args:
        data: Data to redact
        patterns: Optional custom patterns
        
    Returns:
        Redacted data
    """
    if patterns:
        redactor = Redactor(patterns)
    else:
        redactor = _default_redactor
    
    return redactor.redact_dict(data)


def add_redaction_pattern(name: str, pattern: str) -> None:
    """
    Add a custom redaction pattern to the default redactor.
    
    Args:
        name: Pattern name
        pattern: Regex pattern
    """
    _default_redactor.patterns[name] = pattern
    _default_redactor.compiled_patterns[name] = re.compile(
        pattern, re.IGNORECASE | re.MULTILINE
    )
