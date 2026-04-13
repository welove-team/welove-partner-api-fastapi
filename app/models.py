from pydantic import BaseModel


class VerifyMemberRequest(BaseModel):
    phoneNumber: str
    name: str


class VerifyMemberResponse(BaseModel):
    leadership: bool
    community: str | None
    group: str | None


class HealthCheckResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class ErrorResponse(BaseModel):
    error: str
    message: str
