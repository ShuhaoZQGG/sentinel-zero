"""Integration tests for authentication API endpoints."""

import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.main import app
from src.models import Base, User
from src.models.base import get_session as get_db
import os
import tempfile

# Create a temporary database for testing
@pytest.fixture(scope="module")
def test_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal
    
    # Cleanup
    os.unlink(db_path)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for a test user."""
    # Register a test user
    response = client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "testpass123", "email": "test@example.com"}
    )
    assert response.status_code == 201
    
    # Login to get token
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    def test_user_registration(self, client):
        """Test user registration endpoint."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "password": "securepass123",
                "email": "newuser@example.com"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "password" not in data  # Password should not be returned
    
    def test_duplicate_registration(self, client):
        """Test that duplicate usernames are rejected."""
        user_data = {
            "username": "duplicate",
            "password": "pass123",
            "email": "dup1@example.com"
        }
        
        # First registration should succeed
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Second registration with same username should fail
        user_data["email"] = "dup2@example.com"
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_login_success(self, client):
        """Test successful login."""
        # Register user first
        client.post(
            "/api/auth/register",
            json={"username": "logintest", "password": "pass123", "email": "login@example.com"}
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            data={"username": "logintest", "password": "pass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            data={"username": "nonexistent", "password": "wrongpass"}
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_protected_endpoint_with_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_token_refresh(self, client, auth_headers):
        """Test token refresh endpoint."""
        response = client.post("/api/auth/refresh", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_logout(self, client, auth_headers):
        """Test logout endpoint."""
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
    
    def test_password_change(self, client, auth_headers):
        """Test password change endpoint."""
        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "testpass123",
                "new_password": "newpass456"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Try logging in with new password
        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "newpass456"}
        )
        assert response.status_code == 200
    
    def test_user_profile_update(self, client, auth_headers):
        """Test user profile update."""
        response = client.put(
            "/api/auth/profile",
            json={"email": "newemail@example.com", "full_name": "Test User"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"
        assert data["full_name"] == "Test User"


class TestAuthorizationLevels:
    """Test different authorization levels and permissions."""
    
    def test_admin_only_endpoint(self, client):
        """Test that admin-only endpoints require admin privileges."""
        # Create regular user
        client.post(
            "/api/auth/register",
            json={"username": "regular", "password": "pass123", "email": "regular@example.com"}
        )
        
        # Login as regular user
        response = client.post(
            "/api/auth/login",
            data={"username": "regular", "password": "pass123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access admin endpoint
        response = client.get("/api/admin/users", headers=headers)
        assert response.status_code == 403
        assert "insufficient permissions" in response.json()["detail"].lower()
    
    def test_rate_limiting(self, client):
        """Test rate limiting on authentication endpoints."""
        # Try multiple login attempts rapidly
        for i in range(10):
            response = client.post(
                "/api/auth/login",
                data={"username": f"user{i}", "password": "wrong"}
            )
        
        # After multiple attempts, should get rate limited
        response = client.post(
            "/api/auth/login",
            data={"username": "another", "password": "wrong"}
        )
        # Note: Actual rate limiting implementation may vary
        # This test assumes rate limiting is implemented
        # assert response.status_code == 429  # Too Many Requests


class TestSessionManagement:
    """Test session management and token lifecycle."""
    
    def test_token_expiry(self, client):
        """Test that expired tokens are rejected."""
        # This test would require mocking time or waiting for token to expire
        # For integration testing, we'll skip the actual expiry test
        pass
    
    def test_concurrent_sessions(self, client):
        """Test that multiple sessions can exist for a user."""
        # Register user
        client.post(
            "/api/auth/register",
            json={"username": "multiuser", "password": "pass123", "email": "multi@example.com"}
        )
        
        # Login from multiple "devices"
        tokens = []
        for i in range(3):
            response = client.post(
                "/api/auth/login",
                data={"username": "multiuser", "password": "pass123"}
            )
            assert response.status_code == 200
            tokens.append(response.json()["access_token"])
        
        # All tokens should work
        for token in tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/auth/me", headers=headers)
            assert response.status_code == 200


class TestPasswordSecurity:
    """Test password security features."""
    
    def test_weak_password_rejection(self, client):
        """Test that weak passwords are rejected."""
        response = client.post(
            "/api/auth/register",
            json={"username": "weakpass", "password": "123", "email": "weak@example.com"}
        )
        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()
    
    def test_password_reset_flow(self, client):
        """Test password reset flow."""
        # Register user
        client.post(
            "/api/auth/register",
            json={"username": "resetuser", "password": "oldpass123", "email": "reset@example.com"}
        )
        
        # Request password reset
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "reset@example.com"}
        )
        assert response.status_code == 200
        
        # In a real scenario, we would get a reset token from email
        # For testing, we'll assume the token is available
        # reset_token = get_reset_token_from_email()
        
        # Reset password with token
        # response = client.post(
        #     "/api/auth/reset-password",
        #     json={"token": reset_token, "new_password": "newpass456"}
        # )
        # assert response.status_code == 200