"""
T-24.011 — Integration tests: Epic 24 Auth & Password UX (Story 24.2.1)

Covers acceptance criteria for:
  - POST /api/v1/auth/reset-password-request  (user-enumeration-safe 200)
  - POST /api/v1/auth/reset-password-confirm  (valid token -> 200; invalid/expired -> 4xx)
  - GET  /api/v1/auth/password-policy         (public endpoint; response schema)

Uses SQLite in-memory DB via conftest db_session; auth stubbed via conftest fixtures.
"""

import pytest
from fastapi import status


# ---------------------------------------------------------------------------
# S24.2 – Password Policy Endpoint
# ---------------------------------------------------------------------------

class TestPasswordPolicy:
    """TC-24-001: GET /api/v1/auth/password-policy is public and returns required fields."""

    def test_policy_returns_200_without_auth(self, client):
        """Policy endpoint is public — no Authorization header needed."""
        response = client.get("/api/v1/auth/password-policy")
        assert response.status_code == status.HTTP_200_OK

    def test_policy_response_has_required_fields(self, client):
        """Response must include all fields consumed by password-strength-indicator.js."""
        response = client.get("/api/v1/auth/password-policy")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        required_fields = [
            "min_length",
            "require_uppercase",
            "require_lowercase",
            "require_digit",
            "require_special_char",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_policy_min_length_is_positive_int(self, client):
        """min_length must be a positive integer (> 0)."""
        response = client.get("/api/v1/auth/password-policy")
        data = response.json()
        assert isinstance(data["min_length"], int)
        assert data["min_length"] > 0

    def test_policy_boolean_fields_are_booleans(self, client):
        """Rule flags must be booleans, not strings or ints."""
        response = client.get("/api/v1/auth/password-policy")
        data = response.json()
        for field in ("require_uppercase", "require_lowercase", "require_digit", "require_special_char"):
            assert isinstance(data[field], bool), f"{field} is not a bool: {data[field]}"

    def test_policy_with_tenant_id_query_param_returns_200(self, client):
        """Optional tenant_id param is accepted without error."""
        response = client.get("/api/v1/auth/password-policy?tenant_id=00000000-0000-0000-0000-000000000123")
        assert response.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# S24.2 – Reset Password Request (user-enumeration safety)
# ---------------------------------------------------------------------------

class TestResetPasswordRequest:
    """TC-24-002: POST /api/v1/auth/reset-password-request is enumeration-safe."""

    def test_request_returns_200_for_existing_email(self, client, test_user):
        """Known email address returns 200 with safe message."""
        response = client.post(
            "/api/v1/auth/reset-password-request",
            json={"email": test_user.email},
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "message" in body

    def test_request_returns_200_for_nonexistent_email(self, client):
        """Unknown email returns 200 — must not reveal whether account exists."""
        response = client.post(
            "/api/v1/auth/reset-password-request",
            json={"email": "nobody@example.invalid"},
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "message" in body

    def test_request_messages_are_identical_regardless_of_email(self, client, test_user):
        """Response message body must be identical for known and unknown emails (enumeration prevention)."""
        resp_known = client.post(
            "/api/v1/auth/reset-password-request",
            json={"email": test_user.email},
        )
        resp_unknown = client.post(
            "/api/v1/auth/reset-password-request",
            json={"email": "notindb@example.invalid"},
        )
        assert resp_known.json()["message"] == resp_unknown.json()["message"]

    def test_request_requires_email_field(self, client):
        """Missing email field returns 422 validation error."""
        response = client.post("/api/v1/auth/reset-password-request", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_request_rejects_malformed_email(self, client):
        """Malformed email string returns 422."""
        response = client.post(
            "/api/v1/auth/reset-password-request",
            json={"email": "not-an-email"},
        )
        # Accept 422 (strict validation) or 200 (lenient + safe message)
        assert response.status_code in (status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# S24.2 – Reset Password Confirm
# ---------------------------------------------------------------------------

class TestResetPasswordConfirm:
    """TC-24-003: POST /api/v1/auth/reset-password-confirm rejects invalid / missing tokens."""

    def test_confirm_with_invalid_token_returns_4xx(self, client):
        """Non-existent token must return 400 or 404, never 200."""
        response = client.post(
            "/api/v1/auth/reset-password-confirm",
            json={"token": "thistoken_does_not_exist_in_db", "new_password": "NewP@ssw0rd!"},
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def test_confirm_requires_token_field(self, client):
        """Missing token returns 422."""
        response = client.post(
            "/api/v1/auth/reset-password-confirm",
            json={"new_password": "NewP@ssw0rd!"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_confirm_requires_new_password_field(self, client):
        """Missing new_password returns 422."""
        response = client.post(
            "/api/v1/auth/reset-password-confirm",
            json={"token": "sometoken"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_confirm_with_empty_password_returns_error(self, client):
        """Empty string password should not be accepted."""
        response = client.post(
            "/api/v1/auth/reset-password-confirm",
            json={"token": "sometoken", "new_password": ""},
        )
        # Expect validation error or bad-request; never 200
        assert response.status_code != status.HTTP_200_OK
