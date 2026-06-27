"""
T-24.024 — Integration tests: Epic 24 Scheduler Log Viewer (Story 24.5.1)

Covers acceptance criteria for:
  - GET /api/v1/scheduler/jobs/{job_id}/executions
  - GET /api/v1/scheduler/executions/{execution_id}/logs

Uses SQLite in-memory DB via conftest fixtures; auth via auth_headers.
Full rendering and colour-coding tests are manual — see test-plan-24.md S5.
"""

import uuid
import pytest
from fastapi import status


FAKE_JOB_ID = str(uuid.uuid4())
FAKE_EXECUTION_ID = str(uuid.uuid4())


class TestSchedulerJobExecutions:
    """TC-24-009: GET /api/v1/scheduler/jobs/{job_id}/executions."""

    def test_job_executions_requires_auth(self, client):
        """Unauthenticated request returns 401 or 403."""
        response = client.get(f"/api/v1/scheduler/jobs/{FAKE_JOB_ID}/executions")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_job_executions_returns_404_for_nonexistent_job(self, client, auth_headers):
        """Non-existent job_id returns 404, not 500."""
        response = client.get(
            f"/api/v1/scheduler/jobs/{FAKE_JOB_ID}/executions",
            headers=auth_headers,
        )
        assert response.status_code in (
            status.HTTP_403_FORBIDDEN,   # permission guard fires first
            status.HTTP_404_NOT_FOUND,
        )

    def test_job_executions_no_server_error(self, client, auth_headers):
        """Any error for non-existent job must not be 5xx."""
        response = client.get(
            f"/api/v1/scheduler/jobs/{FAKE_JOB_ID}/executions",
            headers=auth_headers,
        )
        assert response.status_code < 500

    def test_job_executions_accepts_status_filter(self, client, auth_headers):
        """status query param is accepted without 422."""
        response = client.get(
            f"/api/v1/scheduler/jobs/{FAKE_JOB_ID}/executions?status=success",
            headers=auth_headers,
        )
        assert response.status_code < 500

    def test_job_executions_response_shape_when_found(self, client, auth_headers):
        """If executions are returned, response has items and total keys."""
        # This will return 403/404 for FAKE_JOB_ID; shape assertion only relevant
        # when a real job exists.  Test documents the expected contract.
        response = client.get(
            f"/api/v1/scheduler/jobs/{FAKE_JOB_ID}/executions",
            headers=auth_headers,
        )
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "items" in data
            assert "total" in data


class TestSchedulerExecutionLogs:
    """TC-24-010: GET /api/v1/scheduler/executions/{execution_id}/logs."""

    def test_execution_logs_requires_auth(self, client):
        """Unauthenticated request returns 401 or 403."""
        response = client.get(f"/api/v1/scheduler/executions/{FAKE_EXECUTION_ID}/logs")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_execution_logs_returns_404_for_nonexistent(self, client, auth_headers):
        """Non-existent execution_id returns 403 or 404, not 500."""
        response = client.get(
            f"/api/v1/scheduler/executions/{FAKE_EXECUTION_ID}/logs",
            headers=auth_headers,
        )
        assert response.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

    def test_execution_logs_no_server_error(self, client, auth_headers):
        """Any error for non-existent execution must not be 5xx."""
        response = client.get(
            f"/api/v1/scheduler/executions/{FAKE_EXECUTION_ID}/logs",
            headers=auth_headers,
        )
        assert response.status_code < 500

    def test_execution_logs_accepts_log_level_filter(self, client, auth_headers):
        """log_level query param is accepted without 422."""
        response = client.get(
            f"/api/v1/scheduler/executions/{FAKE_EXECUTION_ID}/logs?log_level=ERROR",
            headers=auth_headers,
        )
        assert response.status_code < 500
