"""
Authentication API Endpoints

User registration, login, and management
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
import hashlib
import logging

from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, UserUpdate, LoginResponse
)
from app.db.models import User
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


def hash_password(password: str) -> str:
    """Hash a password using SHA256 (simple hashing for development)"""
    # In production, use proper password hashing like bcrypt or argon2
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(plain_password) == hashed_password


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username, email, and password"
)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 6 characters)
    - **full_name**: Optional full name
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"New user registered: {new_user.username} (ID: {new_user.id})")
    
    return new_user


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Login with username/email and password"
)
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user.
    
    - **username**: Username or email
    - **password**: User password
    
    Returns user information on successful login.
    """
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    logger.info(f"User logged in: {user.username} (ID: {user.id})")
    
    return LoginResponse(user=user, message="Login successful")


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve user information by user ID"
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return user


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user profile",
    description="Update user email, full name, or password"
)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update user profile"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Update fields if provided
    if user_update.email is not None:
        # Check if email is already taken by another user
        existing_email = db.query(User).filter(
            User.email == user_update.email,
            User.id != user_id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another user"
            )
        user.email = user_update.email
    
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    
    if user_update.password is not None:
        user.hashed_password = hash_password(user_update.password)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User updated: {user.username} (ID: {user.id})")
    
    return user


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="List all users",
    description="Get a list of all registered users"
)
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all users with pagination"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user account (soft delete by setting is_active to False)"
)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete (deactivate) a user"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Soft delete - just deactivate the user
    user.is_active = False
    db.commit()
    
    logger.info(f"User deactivated: {user.username} (ID: {user.id})")
    
    return None

