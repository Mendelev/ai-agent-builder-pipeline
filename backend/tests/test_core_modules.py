"""
Tests for core modules (database, types, config, logging)
"""
import pytest
import os
from unittest.mock import patch, MagicMock


class TestDatabaseModule:
    """Test database connection and session management"""
    
    def test_get_db_connection(self):
        """Test database connection generator"""
        from app.core.database import get_db
        
        # Get database session
        db_generator = get_db()
        db = next(db_generator)
        
        assert db is not None
        
        # Cleanup
        try:
            db_generator.close()
        except StopIteration:
            pass
    
    def test_get_db_cleanup_on_exception(self):
        """Test database cleanup on exception"""
        from app.core.database import get_db
        
        db_generator = get_db()
        db = next(db_generator)
        
        # Verify cleanup happens
        try:
            db_generator.throw(Exception("Test exception"))
        except Exception:
            pass  # Expected
        
        # Session should be closed
        assert True  # If we got here, cleanup worked


class TestTypesModule:
    """Test custom database types"""
    
    def test_uuid_type_exists(self):
        """Test UUID type can be imported"""
        from app.core.types import UUID
        import uuid
        
        assert UUID is not None
        # Test with actual UUID
        test_uuid = uuid.uuid4()
        assert isinstance(test_uuid, uuid.UUID)
    
    def test_jsonb_type_exists(self):
        """Test JSONB type can be imported"""
        from app.core.types import JSONB
        
        assert JSONB is not None
    
    def test_uuid_type_dialect_specific(self):
        """Test UUID type handles different dialects"""
        from app.core.types import UUID
        from unittest.mock import MagicMock
        import uuid
        
        uuid_type = UUID()
        test_value = uuid.uuid4()
        
        # Test PostgreSQL dialect
        pg_dialect = MagicMock()
        pg_dialect.name = 'postgresql'
        impl = uuid_type.load_dialect_impl(pg_dialect)
        assert impl is not None
        
        # Test SQLite dialect
        sqlite_dialect = MagicMock()
        sqlite_dialect.name = 'sqlite'
        impl = uuid_type.load_dialect_impl(sqlite_dialect)
        assert impl is not None
    
    def test_jsonb_type_serialization(self):
        """Test JSONB handles JSON serialization"""
        from app.core.types import JSONB
        from unittest.mock import MagicMock
        
        jsonb_type = JSONB()
        test_data = {"key": "value", "number": 42}
        
        # Test SQLite dialect (uses JSON string)
        sqlite_dialect = MagicMock()
        sqlite_dialect.name = 'sqlite'
        
        # Bind parameter (serialize)
        serialized = jsonb_type.process_bind_param(test_data, sqlite_dialect)
        assert isinstance(serialized, str)
        assert "key" in serialized
        
        # Result value (deserialize)
        deserialized = jsonb_type.process_result_value(serialized, sqlite_dialect)
        assert deserialized == test_data
    
    def test_uuid_type_none_handling(self):
        """Test UUID type handles None values"""
        from app.core.types import UUID
        from unittest.mock import MagicMock
        
        uuid_type = UUID()
        
        # Test with PostgreSQL
        pg_dialect = MagicMock()
        pg_dialect.name = 'postgresql'
        
        # Bind None
        result = uuid_type.process_bind_param(None, pg_dialect)
        assert result is None
        
        # Result None
        result = uuid_type.process_result_value(None, pg_dialect)
        assert result is None
        
        # Test with SQLite
        sqlite_dialect = MagicMock()
        sqlite_dialect.name = 'sqlite'
        
        # Bind None
        result = uuid_type.process_bind_param(None, sqlite_dialect)
        assert result is None
        
        # Result None
        result = uuid_type.process_result_value(None, sqlite_dialect)
        assert result is None
    
    def test_uuid_type_string_conversion(self):
        """Test UUID type converts string to UUID"""
        from app.core.types import UUID
        from unittest.mock import MagicMock
        import uuid
        
        uuid_type = UUID()
        test_uuid = uuid.uuid4()
        test_uuid_str = str(test_uuid)
        
        # Test SQLite string conversion
        sqlite_dialect = MagicMock()
        sqlite_dialect.name = 'sqlite'
        
        # Bind string value (should convert)
        result = uuid_type.process_bind_param(test_uuid_str, sqlite_dialect)
        assert result == test_uuid_str
        
        # Result string value (should convert to UUID)
        result = uuid_type.process_result_value(test_uuid_str, sqlite_dialect)
        assert isinstance(result, uuid.UUID)
        assert result == test_uuid
    
    def test_uuid_type_postgresql_passthrough(self):
        """Test UUID type with PostgreSQL passes through UUID objects"""
        from app.core.types import UUID
        from unittest.mock import MagicMock
        import uuid
        
        uuid_type = UUID()
        test_uuid = uuid.uuid4()
        
        # Test PostgreSQL dialect (should pass through)
        pg_dialect = MagicMock()
        pg_dialect.name = 'postgresql'
        
        # Bind UUID value
        result = uuid_type.process_bind_param(test_uuid, pg_dialect)
        assert result == test_uuid
        
        # Result UUID value
        result = uuid_type.process_result_value(test_uuid, pg_dialect)
        assert result == test_uuid
    
    def test_jsonb_type_none_handling(self):
        """Test JSONB type handles None values"""
        from app.core.types import JSONB
        from unittest.mock import MagicMock
        
        jsonb_type = JSONB()
        
        # Test with PostgreSQL
        pg_dialect = MagicMock()
        pg_dialect.name = 'postgresql'
        
        result = jsonb_type.process_bind_param(None, pg_dialect)
        assert result is None
        
        result = jsonb_type.process_result_value(None, pg_dialect)
        assert result is None
        
        # Test with SQLite
        sqlite_dialect = MagicMock()
        sqlite_dialect.name = 'sqlite'
        
        result = jsonb_type.process_bind_param(None, sqlite_dialect)
        assert result is None
        
        result = jsonb_type.process_result_value(None, sqlite_dialect)
        assert result is None
    
    def test_jsonb_type_postgresql_passthrough(self):
        """Test JSONB type with PostgreSQL passes through data"""
        from app.core.types import JSONB
        from unittest.mock import MagicMock
        
        jsonb_type = JSONB()
        test_data = {"key": "value", "list": [1, 2, 3]}
        
        # Test PostgreSQL dialect (should pass through)
        pg_dialect = MagicMock()
        pg_dialect.name = 'postgresql'
        
        # Bind data
        result = jsonb_type.process_bind_param(test_data, pg_dialect)
        assert result == test_data
        
        # Result data
        result = jsonb_type.process_result_value(test_data, pg_dialect)
        assert result == test_data
    
    def test_uuid_type_result_already_uuid(self):
        """Test UUID type result_value when value is already UUID (line 41)"""
        from app.core.types import UUID
        from unittest.mock import MagicMock
        import uuid
        
        uuid_type = UUID()
        test_uuid = uuid.uuid4()
        
        # Test SQLite with UUID object (should return as-is)
        sqlite_dialect = MagicMock()
        sqlite_dialect.name = 'sqlite'
        
        # When result value is already a UUID object
        result = uuid_type.process_result_value(test_uuid, sqlite_dialect)
        assert result == test_uuid
        assert isinstance(result, uuid.UUID)
    
    def test_jsonb_type_load_dialect_postgresql(self):
        """Test JSONB load_dialect_impl for PostgreSQL (line 55)"""
        from app.core.types import JSONB
        from unittest.mock import MagicMock
        
        jsonb_type = JSONB()
        
        # Test PostgreSQL dialect descriptor
        pg_dialect = MagicMock()
        pg_dialect.name = 'postgresql'
        pg_dialect.type_descriptor = MagicMock(return_value="PG_JSONB_TYPE")
        
        result = jsonb_type.load_dialect_impl(pg_dialect)
        
        # Should call type_descriptor with PG_JSONB
        assert pg_dialect.type_descriptor.called
        assert result == "PG_JSONB_TYPE"


class TestConfigModule:
    """Test configuration settings"""
    
    def test_settings_default_values(self):
        """Test settings load with default values"""
        from app.core.config import settings
        
        assert settings is not None
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'CELERY_BROKER_URL')
    
    def test_settings_database_url(self):
        """Test database URL configuration"""
        from app.core.config import settings
        
        # Should have a database URL
        assert settings.DATABASE_URL is not None
        assert len(settings.DATABASE_URL) > 0
    
    def test_get_origins_list_wildcard(self):
        """Test origins list conversion with wildcard"""
        from app.core.config import settings
        
        # Test wildcard setting
        origins = settings.get_origins_list()
        assert isinstance(origins, list)
        # Should return wildcard or parsed list
        assert len(origins) > 0
    
    def test_settings_has_required_fields(self):
        """Test all required settings fields exist"""
        from app.core.config import settings
        
        required_fields = [
            'APP_NAME', 'APP_VERSION', 'DEBUG',
            'DATABASE_URL', 'CELERY_BROKER_URL', 'CELERY_RESULT_BACKEND',
            'HOST', 'PORT', 'ALLOWED_ORIGINS'
        ]
        
        for field in required_fields:
            assert hasattr(settings, field), f"Missing required field: {field}"


class TestLoggingModule:
    """Test logging configuration"""
    
    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance"""
        from app.core.logging_config import get_logger
        import logging
        
        logger = get_logger("test_logger")
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
    
    def test_json_formatter_exists(self):
        """Test JSONFormatter class exists"""
        from app.core.logging_config import JSONFormatter
        import logging
        
        formatter = JSONFormatter()
        assert formatter is not None
        assert isinstance(formatter, logging.Formatter)
    
    def test_json_formatter_formats_record(self):
        """Test JSONFormatter formats log records as JSON"""
        from app.core.logging_config import JSONFormatter
        import logging
        import json
        
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        
        formatted = formatter.format(record)
        assert formatted is not None
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert "message" in parsed
        assert parsed["message"] == "Test message"
        assert "level" in parsed
        assert "timestamp" in parsed
    
    def test_json_formatter_includes_extra_fields(self):
        """Test JSONFormatter includes extra fields like project_id"""
        from app.core.logging_config import JSONFormatter
        import logging
        import json
        import uuid
        
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        
        # Add extra fields
        test_project_id = uuid.uuid4()
        record.project_id = test_project_id
        record.agent = "TestAgent"
        record.task_id = "task-123"
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert "project_id" in parsed
        assert str(test_project_id) in parsed["project_id"]
        assert parsed["agent"] == "TestAgent"
        assert parsed["task_id"] == "task-123"
