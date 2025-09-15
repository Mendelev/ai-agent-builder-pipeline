# backend/tests/test_security.py
import pytest
from app.utils.security import remove_secrets, sanitize_content, generate_placeholder_config


def test_remove_secrets_api_keys():
    """Test removal of API keys."""
    content = "API_KEY=sk-1234567890abcdef"
    result = remove_secrets(content)
    assert "sk-1234567890abcdef" not in result
    assert "API_KEY=<REDACTED>" in result


def test_remove_secrets_aws_keys():
    """Test removal of AWS credentials."""
    content = "AWS_SECRET=ABCDEFGHIJKLMNOP1234567890+/="
    result = remove_secrets(content)
    assert "ABCDEFGHIJKLMNOP1234567890+/=" not in result
    assert "AWS_SECRET=<REDACTED>" in result
    
    access_key = "AKIA1234567890ABCDEF"
    result = remove_secrets(access_key)
    assert "AKIA1234567890ABCDEF" not in result
    assert "AWS_ACCESS_KEY_ID=<REDACTED>" in result


def test_remove_secrets_database_urls():
    """Test removal of database URLs."""
    url = "postgresql://user:password@localhost:5432/db"
    result = remove_secrets(url)
    assert "password" not in result
    assert "postgresql://<USER>:<PASSWORD>@<HOST>" in result


def test_remove_secrets_tokens():
    """Test removal of bearer tokens."""
    content = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    result = remove_secrets(content)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
    assert "Bearer <TOKEN>" in result


def test_remove_secrets_passwords():
    """Test removal of passwords."""
    content = "PASSWORD=mysecretpassword"
    result = remove_secrets(content)
    assert "mysecretpassword" not in result
    assert "PASSWORD=<REDACTED>" in result


def test_remove_secrets_private_keys():
    """Test removal of private keys."""
    content = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890
-----END RSA PRIVATE KEY-----"""
    result = remove_secrets(content)
    assert "MIIEpAIBAAKCAQEA1234567890" not in result
    assert "-----BEGIN PRIVATE KEY-----" in result
    assert "<REDACTED>" in result


def test_remove_secrets_empty_content():
    """Test handling of empty content."""
    assert remove_secrets("") == ""
    assert remove_secrets(None) is None


def test_sanitize_content_string():
    """Test sanitizing string content."""
    content = "API_KEY=secret123"
    result = sanitize_content(content)
    assert "secret123" not in result


def test_sanitize_content_dict():
    """Test sanitizing dictionary content."""
    data = {
        "api_key": "secret123",
        "password": "mypassword",
        "normal_field": "normal_value",
        "database_url": "postgresql://user:pass@host:5432/db"
    }
    result = sanitize_content(data)
    
    assert result["api_key"] == "<REDACTED>"
    assert result["password"] == "<REDACTED>"
    assert result["normal_field"] == "normal_value"
    assert "pass" not in result["database_url"]


def test_sanitize_content_list():
    """Test sanitizing list content."""
    data = ["normal", "API_KEY=secret123"]
    result = sanitize_content(data)
    
    assert result[0] == "normal"
    assert "secret123" not in result[1]


def test_sanitize_content_nested():
    """Test sanitizing nested structures."""
    data = {
        "config": {
            "secret": "mysecret",
            "public": "value"
        },
        "items": ["normal", "TOKEN=abc123"]
    }
    result = sanitize_content(data)
    
    assert result["config"]["secret"] == "<REDACTED>"
    assert result["config"]["public"] == "value"
    assert "abc123" not in result["items"][1]


def test_sanitize_content_non_dict_list_str():
    """Test sanitizing non-dict/list/str content."""
    assert sanitize_content(123) == 123
    assert sanitize_content(None) is None
    assert sanitize_content(True) is True


def test_generate_placeholder_config():
    """Test placeholder config generation."""
    config = generate_placeholder_config()
    
    assert isinstance(config, dict)
    assert "database_url" in config
    assert "redis_url" in config
    assert "api_key" in config
    assert "<PASSWORD>" in config["database_url"]
    assert "<YOUR_API_KEY>" in config["api_key"]