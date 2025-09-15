# backend/app/models/types.py
from sqlalchemy import JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.types import TypeEngine

class JsonType(TypeDecorator):
    """A type that uses JSONB for PostgreSQL and JSON for other databases."""
    
    impl = JSON
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())
    
    def process_bind_param(self, value, dialect):
        return value
    
    def process_result_value(self, value, dialect):
        return value