"""Authentication router for API"""

from fastapi import APIRouter, HTTPException, status
from src.api.models.schemas import TokenRequest, TokenResponse, UserCreate
from src.api.middleware.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_password_hash,
    users_db
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(request: TokenRequest):
    """Authenticate user and return JWT tokens"""
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user["username"]})
    refresh_token = create_refresh_token(data={"sub": user["username"]})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800  # 30 minutes
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    payload = await verify_refresh_token(refresh_token)
    username = payload.get("sub")
    
    if not username or username not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": username})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,  # Return same refresh token
        token_type="bearer",
        expires_in=1800
    )


@router.post("/register", response_model=dict)
async def register(user: UserCreate):
    """Register a new user (simplified for MVP)"""
    if user.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Add user to in-memory store
    users_db[user.username] = {
        "username": user.username,
        "hashed_password": get_password_hash(user.password),
        "email": user.email
    }
    
    return {"message": "User registered successfully"}