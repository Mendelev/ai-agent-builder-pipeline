from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class GatewayActionEnum(str, Enum):
    finalizar = "finalizar"
    planejar = "planejar"
    validar_codigo = "validar_codigo"


class RequirementsGatewayRequest(BaseModel):
    """Request schema for requirements gateway endpoint"""
    action: GatewayActionEnum = Field(..., description="Decision type: finalizar, planejar, or validar_codigo")
    correlation_id: Optional[UUID] = Field(None, description="Optional correlation ID for tracking")
    request_id: Optional[UUID] = Field(default_factory=uuid4, description="Idempotency key")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        if v not in ["finalizar", "planejar", "validar_codigo"]:
            raise ValueError(f'Invalid action. Must be one of: finalizar, planejar, validar_codigo')
        return v


class AuditReference(BaseModel):
    """Audit trail reference with correlation data"""
    correlation_id: UUID
    request_id: UUID
    project_id: UUID
    timestamp: datetime
    action: str
    user_id: Optional[UUID] = None


class RequirementsGatewayResponse(BaseModel):
    """Response schema for requirements gateway endpoint"""
    from_state: str = Field(..., alias="from", description="Previous project state")
    to_state: str = Field(..., alias="to", description="New project state") 
    reason: str = Field(..., description="Transition reason based on action")
    audit_ref: AuditReference = Field(..., description="Audit trail reference")

    model_config = ConfigDict(populate_by_name=True)


class RequirementsGatewayAuditRead(BaseModel):
    """Read schema for requirements gateway audit records"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    project_id: UUID
    correlation_id: UUID
    request_id: UUID
    action: str
    from_state: str
    to_state: str
    user_id: Optional[UUID]
    created_at: datetime


class GatewayError(BaseModel):
    """Error response schema for gateway operations"""
    detail: str
    error_code: str
    current_state: Optional[str] = None
    requested_action: Optional[str] = None