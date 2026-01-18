# Pydantic models for API requests and responses
from pydantic import BaseModel
from typing import Optional

class WorkflowParams(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None

class MatchingInputs(BaseModel):
    action: str
    anken: str
    text: Optional[str] = None
    mode: Optional[str] = None

class MatchingRequest(BaseModel):
    inputs: MatchingInputs
    response_mode: Optional[str] = None
    user: Optional[str] = None

class SuccessResponse(BaseModel):
    status: str
    message: str

class MatchingResponse(BaseModel):
    status: str
    result: dict

class HealthResponse(BaseModel):
    status: str