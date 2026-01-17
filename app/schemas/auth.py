"""
Authentication Schemas

Pydantic models for user authentication and registration
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name of the user")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "securepass123",
                "full_name": "John Doe"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "securepass123"
            }
        }


class UserResponse(BaseModel):
    """Schema for user data in responses"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "created_at": "2026-01-17T10:30:00"
            }
        }


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=6)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "newemail@example.com",
                "full_name": "John Updated Doe"
            }
        }


class LoginResponse(BaseModel):
    """Response after successful login"""
    user: UserResponse
    message: str = "Login successful"
    
    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "username": "johndoe",
                    "email": "john@example.com",
                    "full_name": "John Doe",
                    "is_active": True,
                    "created_at": "2026-01-17T10:30:00"
                },
                "message": "Login successful"
            }
        }
