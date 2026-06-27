"""
T-24.021 — Integration tests: Epic 24 Automation Visibility (Stories 24.4.1, 24.4.2)

Covers acceptance criteria for:
  - POST /api/v1/automations/rules/{rule_id}/test
  - GET  /api/v1/automations/executions              (list with optional filters)
  - GET  /api/v1/automations/executions/{id}         (detail)

Uses SQLite in-memory DB via conftest fixtures; auth via auth_headers.
Full service-path tests (rule execution, pagination) are manual — see test-plan-24.md S4.
"""

import uuid
import pytest
from fastapi import status


FAKE_RULE_ID = str(uuid.uuid4())
FAKE_EXECUTION_ID = str(uuid.uuid4())


class TestAutomationRuleTest:
    """TC-24-006: POST /api/v1/automations/rules/{rule_id}/test."""

    def test_rule_test_requires_auth(self, client):
        """Unauthenticated request returns 401 or 403."""
        response = client.post(
            f"/api/v1/automations/rules/{FAKE_RULE_ID}/test",
            json={},
        )
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_rule_test_returns_404_for_nonexistent_rule(self, client, auth_headers):
        """Non-existent rule_id returns 404 (not 500)."""
        response = client.post(
            f"/api/v1/automations/rules/{FAKE_RULE_ID}/test",
            json={},
            headers=auth_headers,
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        )

    def test_rule_test_no_server_error(self, client, auth_headers):
        """Any error response for non-existent rule must not be 5xx."""
        response = client.post(
            f"/api/v1/automations/rules/{FAKE_RULE_ID}/test",
            json={"sample_payload": {}},
            headers=auth_headers,
        )
        assert response.status_code < 500

    def test_rule_test_accepts_empty_payload(self, client, auth_headers):
        """Empty JSON body is accepted (sample_payload is optional per spec)."""
        response = client.post(
            f"/api/v1/automations/rules/{FAKE_RULE_ID}/test",
            json={},
            headers=auth_headers,
        )
        # 404 expected for non-existent rule, but not 422 (body shape OK)
        assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAutomationExecutionsList:
    """TC-24-007: GET /api/v1/automations/executions."""

    def test_executions_list_requires_auth(self, client):
        """Unauthenticated request returns 401 or 403."""
        response = client.get("/api/v1/automations/executions")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_executions_list_returns_200_when_authed(self, client, auth_headers):
        """Authenticated request returns 200 with list (may be empty)."""
        response = client.get("/api/v1/automations/executions", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_executions_list_returns_list_type(self, client, auth_headers):
        """Response body must be a JSON array."""
        response = client.get("/api/v1/automations/executions", headers=auth_headers)
        assert isinstance(response.json(), list)

    def test_executions_list_accepts_rule_id_filter(self, client, auth_headers):
        """rule_id query param is accepted without error."""
        response = client.get(
            f"/api/v1/automations/executions?rule_id={FAKE_RULE_ID}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK

    def test_executions_list_accepts_status_filter(self, client, auth_headers):
        """status query param is accepted without error."""
        response = client.get(
            "/api/v1/automations/executions?status=success",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK

    def test_executions_list_date_params_do_not_cause_500(self, client, auth_headers):
        """from/to date params (if supported) must not cause 5xx; 400/422 acceptable if unsupported.
        This test documents T-24.017 verdict: server accepts or gracefully rejects date params."""
        response = client.get(
            "/api/v1/automations/executions?from=2026-01-01&to=2026-12-31",
            headers=auth_headers,
        )
        # 200 (params supported) or 422 (unsupported) — never 5xx
        assert response.status_code < 500


class TestAutomationExecutionDetail:
    """TC-24-008: GET /api/v1/automations/executions/{execution_id}."""

    def test_execution_detail_requires_auth(self, client):
        """Unauthenticated request returns 401 or 403."""
        response = client.get(f"/api/v1/automations/executions/{FAKE_EXECUTION_ID}")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_execution_detail_returns_404_for_nonexistent(self, client, auth_headers):
        """Non-existent execution_id returns 404, not 500."""
        response = client.get(
            f"/api/v1/automations/executions/{FAKE_EXECUTION_ID}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_execution_detail_no_server_error(self, client, auth_headers):
        """Any error for non-existent execution must not be 5xx."""
        response = client.get(
            f"/api/v1/automations/executions/{FAKE_EXECUTION_ID}",
            headers=auth_headers,
        )
        assert response.status_code < 500
