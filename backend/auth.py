"""
Authentication module for Athletic Spirit
Provides user registration, login, and JWT token management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
import bcrypt
import os
from datetime import datetime, timedelta
import secrets

router = APIRouter()
security = HTTPBearer()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# In-memory user storage (replace with database in production)
users_db = {}

class UserSignup(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    id_token: str

class TokenResponse(BaseModel):
    token: str
    user: dict

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_data: dict) -> str:
    """Create a JWT token for authenticated user"""
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_data["user_id"],
        "email": user_data["email"],
        "username": user_data["username"],
        "exp": expiration
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to get current authenticated user from JWT token"""
    token = credentials.credentials
    return verify_jwt_token(token)

@router.post("/signup", response_model=dict)
async def signup(user_data: UserSignup):
    """Register a new user"""
    # Check if user already exists
    if user_data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username is taken
    for user in users_db.values():
        if user["username"] == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Hash the password
    hashed_password = hash_password(user_data.password)
    
    # Create user record
    user_id = secrets.token_urlsafe(16)
    users_db[user_data.email] = {
        "user_id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": hashed_password,
        "created_at": datetime.utcnow().isoformat(),
        "preferences": {}
    }
    
    return {
        "message": "User registered successfully",
        "user_id": user_id
    }

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Authenticate user and return JWT token"""
    # Check if user exists
    if credentials.email not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user = users_db[credentials.email]
    
    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create JWT token
    user_info = {
        "user_id": user["user_id"],
        "email": user["email"],
        "username": user["username"]
    }
    token = create_jwt_token(user_info)
    
    return {
        "token": token,
        "user": user_info
    }

@router.post("/auth/google")
async def google_auth(auth_request: GoogleAuthRequest):
    """
    Authenticate user with Google OAuth
    Note: In production, verify the id_token with Google's API
    For now, this is a placeholder implementation
    """
    # In production, verify the Google ID token here
    # For now, we'll create a demo response
    
    # Extract user info from token (in production, use Google's API)
    # This is a simplified version - implement proper Google OAuth verification
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth integration requires proper configuration. Please use email/password login for now."
    )

@router.get("/auth/github")
async def github_auth():
    """
    GitHub OAuth endpoint
    Note: Requires GitHub OAuth app configuration
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="GitHub OAuth integration requires proper configuration. Please use email/password login for now."
    )

@router.post("/forgot-password")
async def forgot_password(email: EmailStr):
    """
    Initiate password reset process
    In production, this would send an email with a reset link
    """
    # Check if user exists
    if email not in users_db:
        # Don't reveal whether email exists for security
        return {
            "message": "If an account with that email exists, a reset link has been sent."
        }
    
    # In production, generate reset token and send email
    # For now, just return success message
    return {
        "message": "If an account with that email exists, a reset link has been sent."
    }

@router.post("/reset-password")
async def reset_password(token: str, password: str):
    """
    Reset user password with token
    In production, verify the reset token before allowing password change
    """
    # In production, verify token and update password
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset requires email service configuration. Please contact support."
    )

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    email = current_user["email"]
    if email in users_db:
        user = users_db[email]
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"],
            "preferences": user.get("preferences", {})
        }
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

@router.put("/me/preferences")
async def update_preferences(
    preferences: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update user preferences"""
    email = current_user["email"]
    if email in users_db:
        users_db[email]["preferences"] = preferences
        return {"message": "Preferences updated successfully"}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )
