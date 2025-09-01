"""Database-backed authentication router for API"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.api.models.schemas import TokenRequest, TokenResponse, UserCreate
from src.api.middleware.auth_db import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_password_hash,
    create_user,
    get_user_by_username
)
from src.models import get_session

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(request: TokenRequest, db: Session = Depends(get_session)):
    """Authenticate user and return JWT tokens"""
    user = authenticate_user(request.username, request.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800  # 30 minutes
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: Session = Depends(get_session)):
    """Refresh access token using refresh token"""
    payload = await verify_refresh_token(refresh_token)
    username = payload.get("sub")
    
    user = get_user_by_username(username, db)
    if not user:
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


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_session)):
    """Register a new user"""
    try:
        new_user = create_user(
            username=user.username,
            email=user.email,
            password=user.password,
            is_admin=False,
            db=db
        )
        return {"message": "User registered successfully", "username": new_user.username}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )