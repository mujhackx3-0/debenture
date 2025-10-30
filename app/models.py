"""
Pydantic models for API request/response schemas.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, List
from datetime import datetime
from enum import Enum


class LoanStatus(str, Enum):
    """Loan application status enum."""
    INITIATED = "initiated"
    KYC_PENDING = "kyc_pending"
    CREDIT_CHECK_PENDING = "credit_check_pending"
    OFFER_MADE = "offer_made"
    SANCTIONED = "sanctioned"
    REJECTED = "rejected"
    COMPLETED = "completed"


class CreditEligibility(str, Enum):
    """Credit eligibility status enum."""
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    PENDING = "pending"


# Request Models
class ChatMessageRequest(BaseModel):
    """Request model for chat messages."""
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for continuing conversation")
    
    @validator('message')
    def sanitize_message(cls, v):
        """Sanitize input message."""
        return v.strip()


class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""
    user_id: Optional[str] = Field(None, description="Optional user identifier")


class LoanApplicationRequest(BaseModel):
    """Request to create or update loan application."""
    applicant_name: Optional[str] = Field(None, min_length=2, max_length=100)
    desired_amount: Optional[int] = Field(None, gt=0, le=10000000)
    loan_term_months: Optional[int] = Field(None, ge=12, le=360)
    purpose: Optional[str] = Field(None, max_length=500)
    
    @validator('applicant_name')
    def validate_name(cls, v):
        if v and not v.replace(' ', '').isalpha():
            raise ValueError('Name must contain only letters and spaces')
        return v.strip() if v else v
    
    @validator('desired_amount')
    def validate_amount(cls, v):
        if v and v < 10000:
            raise ValueError('Minimum loan amount is ₹10,000')
        return v


# Response Models
class LoanApplicationResponse(BaseModel):
    """Response model for loan application details."""
    applicant_name: Optional[str] = None
    desired_amount: Optional[int] = None
    loan_term_months: Optional[int] = None
    purpose: Optional[str] = None
    kyc_verified: bool = False
    credit_score: Optional[int] = None
    credit_eligibility: CreditEligibility = CreditEligibility.PENDING
    offered_amount: Optional[int] = None
    offered_interest_rate: Optional[float] = None
    sanction_letter_generated: bool = False
    sanction_letter_url: Optional[str] = None
    status: LoanStatus = LoanStatus.INITIATED


class ChatMessageResponse(BaseModel):
    """Response model for chat messages."""
    session_id: str
    message: str
    loan_application: LoanApplicationResponse
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SessionResponse(BaseModel):
    """Response for session creation."""
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    greeting_message: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetricsResponse(BaseModel):
    """Metrics response."""
    total_sessions: int
    active_sessions: int
    total_messages: int
    avg_response_time_ms: float
    uptime_seconds: float


class RAGQueryRequest(BaseModel):
    """Request to query the RAG knowledge base."""
    query: str = Field(..., min_length=1, max_length=500)
    top_k: Optional[int] = Field(3, ge=1, le=10)


class RAGQueryResponse(BaseModel):
    """Response from RAG query."""
    query: str
    results: List[str]
    sources: List[str]


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""
    type: Literal["message", "status", "error", "end"]
    content: str
    session_id: Optional[str] = None
    loan_application: Optional[LoanApplicationResponse] = None


class StreamChunk(BaseModel):
    """Streaming response chunk."""
    session_id: str
    chunk: str
    is_final: bool = False

