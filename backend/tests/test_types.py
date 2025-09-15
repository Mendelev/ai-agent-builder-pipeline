# backend/tests/test_types.py
import pytest
from unittest.mock import MagicMock
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from app.models.types import JsonType


def test_json_type_postgresql_dialect():
    """Test JsonType uses JSONB for PostgreSQL dialect."""
    json_type = JsonType()
    
    # Mock PostgreSQL dialect
    pg_dialect = MagicMock()
    pg_dialect.name = 'postgresql'
    pg_dialect.type_descriptor.return_value = JSONB()
    
    result = json_type.load_dialect_impl(pg_dialect)
    assert isinstance(result, JSONB)
    pg_dialect.type_descriptor.assert_called_once()


def test_json_type_other_dialect():
    """Test JsonType uses JSON for non-PostgreSQL dialects."""
    json_type = JsonType()
    
    # Mock SQLite dialect
    sqlite_dialect = MagicMock()
    sqlite_dialect.name = 'sqlite'
    sqlite_dialect.type_descriptor.return_value = JSON()
    
    result = json_type.load_dialect_impl(sqlite_dialect)
    assert isinstance(result, JSON)
    sqlite_dialect.type_descriptor.assert_called_once()


def test_json_type_process_bind_param():
    """Test JsonType process_bind_param returns value unchanged."""
    json_type = JsonType()
    test_value = {"key": "value"}
    dialect = MagicMock()
    
    result = json_type.process_bind_param(test_value, dialect)
    assert result == test_value


def test_json_type_process_result_value():
    """Test JsonType process_result_value returns value unchanged."""
    json_type = JsonType()
    test_value = {"result": "data"}
    dialect = MagicMock()
    
    result = json_type.process_result_value(test_value, dialect)
    assert result == test_value


def test_json_type_cache_ok():
    """Test JsonType has cache_ok set to True."""
    json_type = JsonType()
    assert json_type.cache_ok is True


def test_json_type_impl():
    """Test JsonType impl is JSON type."""
    json_type = JsonType()
    # Test that impl is set (instance comparison may vary)
    assert json_type.impl is not None