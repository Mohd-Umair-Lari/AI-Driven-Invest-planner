from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=20, description="Reset token from email link")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")
    confirm_password: str = Field(..., description="Password confirmation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456...",
                "new_password": "NewSecurePassword123",
                "confirm_password": "NewSecurePassword123"
            }
        }


class VerifyResetTokenRequest(BaseModel):
    token: str = Field(..., min_length=20, description="Reset token to verify")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456..."
            }
        }
