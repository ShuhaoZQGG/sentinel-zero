"""Tests for database-backed authentication"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.base import Base
from src.models.user import User
from src.api.middleware.auth_db import (
    authenticate_user,
    create_user,
    get_user_by_username,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)


@pytest.fixture
def test_db():
    """Create a test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def test_create_user(test_db):
    """Test creating a new user"""
    user = create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        is_admin=False,
        db=test_db
    )
    
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.is_admin is False
    assert verify_password("testpass123", user.hashed_password)


def test_create_duplicate_user(test_db):
    """Test creating duplicate user raises error"""
    create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        db=test_db
    )
    
    with pytest.raises(ValueError, match="already exists"):
        create_user(
            username="testuser",
            email="different@example.com",
            password="testpass123",
            db=test_db
        )


def test_authenticate_user_success(test_db):
    """Test successful user authentication"""
    create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        db=test_db
    )
    
    user = authenticate_user("testuser", "testpass123", test_db)
    assert user is not None
    assert user.username == "testuser"
    assert user.last_login is not None


def test_authenticate_user_wrong_password(test_db):
    """Test authentication with wrong password"""
    create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        db=test_db
    )
    
    user = authenticate_user("testuser", "wrongpass", test_db)
    assert user is None


def test_authenticate_user_not_found(test_db):
    """Test authentication with non-existent user"""
    user = authenticate_user("nonexistent", "anypass", test_db)
    assert user is None


def test_get_user_by_username(test_db):
    """Test retrieving user by username"""
    create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        db=test_db
    )
    
    user = get_user_by_username("testuser", test_db)
    assert user is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"


def test_password_hashing():
    """Test password hashing and verification"""
    password = "mySecurePassword123!"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_create_access_token():
    """Test creating access token"""
    token = create_access_token(data={"sub": "testuser"})
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token():
    """Test creating refresh token"""
    token = create_refresh_token(data={"sub": "testuser"})
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_admin_user_creation(test_db):
    """Test creating admin user"""
    user = create_user(
        username="admin",
        email="admin@example.com",
        password="admin123",
        is_admin=True,
        db=test_db
    )
    
    assert user.username == "admin"
    assert user.is_admin is True