from pydantic import BaseModel, HttpUrl, Field, ConfigDict
from uuid import UUID

class MonitorCreate(BaseModel):
    name: str
    url: HttpUrl
    method: str = "GET"
    interval_seconds: int = Field(default=30, ge=10)
    timeout_ms: int = Field(default=5000, le=30000)

class MonitorResponse(BaseModel):
    id: UUID
    name: str
    url: str
    method: str
    interval_seconds: int
    is_active: bool
    
    # Modern Pydantic V2 configuration
    model_config = ConfigDict(from_attributes=True)
