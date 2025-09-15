# backend/app/utils/security.py
import re
from typing import Any, Dict

# Common secret patterns
SECRET_PATTERNS = [
    # API Keys
    (r'[aA][pP][iI][-_]?[kK][eE][yY]\s*[:=]\s*["\']?[\w\-]+["\']?', "API_KEY=<REDACTED>"),
    # AWS Keys
    (r'[aA][wW][sS][-_]?[sS][eE][cC][rR][eE][tT]\s*[:=]\s*["\']?[\w/+=]+["\']?', "AWS_SECRET=<REDACTED>"),
    (r"AKIA[0-9A-Z]{16}", "AWS_ACCESS_KEY_ID=<REDACTED>"),
    # Database URLs
    (r"(mongodb|postgresql|postgres|mysql|redis)://[^:]+:[^@]+@[^/\s]+", r"\1://<USER>:<PASSWORD>@<HOST>"),
    # JWT/Tokens
    (r"[bB][eE][aA][rR][eE][rR]\s+[\w\-_.]+", "Bearer <TOKEN>"),
    (r'[tT][oO][kK][eE][nN]\s*[:=]\s*["\']?[\w\-_.]+["\']?', "TOKEN=<REDACTED>"),
    # Generic secrets
    (r'[pP][aA][sS][sS][wW][oO][rR][dD]\s*[:=]\s*["\']?[^"\'\s]+["\']?', "PASSWORD=<REDACTED>"),
    (r'[sS][eE][cC][rR][eE][tT]\s*[:=]\s*["\']?[\w\-]+["\']?', "SECRET=<REDACTED>"),
    # Private keys
    (
        r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[\s\S]+?-----END (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "-----BEGIN PRIVATE KEY-----\n<REDACTED>\n-----END PRIVATE KEY-----",
    ),
]


def remove_secrets(content: str) -> str:
    """Remove secrets and sensitive information from content"""
    if not content:
        return content

    sanitized = content
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE | re.MULTILINE)

    return sanitized


def sanitize_content(data: Any) -> Any:
    """Recursively sanitize content in various data structures"""
    if isinstance(data, str):
        return remove_secrets(data)
    elif isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            # Check if the key indicates sensitive data
            key_lower = k.lower()
            if any(sensitive in key_lower for sensitive in ["password", "secret", "key", "token"]):
                if isinstance(v, str):
                    sanitized[k] = "<REDACTED>"
                else:
                    sanitized[k] = sanitize_content(v)
            else:
                # Also sanitize values that look sensitive (like database URLs)
                sanitized[k] = sanitize_content(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_content(item) for item in data]
    else:
        return data


def generate_placeholder_config() -> Dict[str, str]:
    """Generate placeholder configuration template"""
    return {
        "database_url": "postgresql://<USER>:<PASSWORD>@<HOST>:<PORT>/<DATABASE>",
        "redis_url": "redis://<HOST>:<PORT>/<DB>",
        "api_key": "<YOUR_API_KEY>",
        "secret_key": "<GENERATE_STRONG_SECRET>",
        "jwt_secret": "<GENERATE_JWT_SECRET>",
        "aws_access_key_id": "<AWS_ACCESS_KEY>",
        "aws_secret_access_key": "<AWS_SECRET_KEY>",
    }
