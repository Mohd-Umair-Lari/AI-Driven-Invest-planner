
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    Name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)
    Age: Optional[str] = ""
    employment_status: Optional[str] = Field("Salaried", alias="employment-status")
    Goal: Optional[Dict[str, Any]] = {}
    financials: Optional[Dict[str, Any]] = {}
    investments: Optional[Dict[str, Any]] = {}
    progress: Optional[Dict[str, Any]] = {}

    model_config = {"populate_by_name": True}

class OnboardingStartRequest(BaseModel):
    email: EmailStr

class OnboardingSaveRequest(BaseModel):
    email: EmailStr
    step: int = 0
    payload: Dict[str, Any] = {}

class OnboardingCancelRequest(BaseModel):
    email: EmailStr
    current_step: Optional[int] = None

class OnboardingCompleteRequest(BaseModel):
    email: EmailStr

class UserUpdateRequest(BaseModel):
    Name: Optional[str] = ""
    Age: Optional[str] = ""
    employment_status: Optional[str] = Field("", alias="employment-status")
    Goal: Optional[Dict[str, Any]] = {}
    financials: Optional[Dict[str, Any]] = {}
    investments: Optional[Dict[str, Any]] = {}
    progress: Optional[Dict[str, Any]] = {}

    model_config = {"populate_by_name": True}

class ChatContext(BaseModel):
    monthly_income: float = 0
    monthly_expenses: float = 0
    total_savings: float = 0
    debt: float = 0
    risk_appetite: str = "Moderate"

class AdvisorChatRequest(BaseModel):
    email: EmailStr
    question: str = Field(..., min_length=1)
    context: Optional[ChatContext] = ChatContext()

class IntelligenceRequest(BaseModel):
    income: float
    expenses: float
    savings: float
    debt: float
    risk_score: float
    investment_exposure: float
    goal_horizon_months: int
    emergency_fund_months: float

class StatusResponse(BaseModel):
    status: str
    message: Optional[str] = None
