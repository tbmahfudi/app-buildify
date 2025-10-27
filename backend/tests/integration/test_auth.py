import pytest
from fastapi import status


class TestAuthentication:
    """Test authentication endpoints"""

    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user(self, client, test_user, auth_headers):
        """Test getting current user profile"""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["tenant_id"] == test_user.tenant_id

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_refresh_token(self, client, test_user):
        """Test token refresh"""
        # First login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh the token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_logout(self, client, test_user, auth_headers):
        """Test logout endpoint"""
        response = client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK


class TestTenantIsolation:
    """Test tenant isolation security"""

    def test_tenant_id_from_jwt(self, client, test_user, auth_headers):
        """Verify tenant ID comes from JWT token, not headers"""
        # Try to access with different tenant ID in header
        headers = {
            **auth_headers,
            "X-Tenant-Id": "different-tenant"
        }

        response = client.get(
            "/api/v1/auth/me",
            headers=headers
        )

        # Should still work, tenant ID from JWT is used
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["tenant_id"] == test_user.tenant_id
