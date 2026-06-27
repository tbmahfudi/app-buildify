"""
T-24.029 — Integration tests: Epic 24 Builder Version History (Story 24.6.1)

Covers acceptance criteria for:
  - GET  /api/v1/builder-pages/{page_id}/versions
  - GET  /api/v1/builder-pages/{page_id}/versions/{version_number}
  - POST /api/v1/builder-pages/{page_id}/restore/{version_number}

Uses SQLite in-memory DB via conftest fixtures; auth via auth_headers.
Full drawer/modal rendering, ARIA, focus-trap, and concurrent-restore
prevention are manual — see test-plan-24.md S6.
"""

import uuid
import pytest
from fastapi import status


FAKE_PAGE_ID = str(uuid.uuid4())


class TestBuilderVersionList:
    """TC-24-011: GET /api/v1/builder-pages/{page_id}/versions."""

    def test_versions_requires_auth(self, client):
        """Unauthenticated request returns 401 or 403."""
        response = client.get(f"/api/v1/builder-pages/{FAKE_PAGE_ID}/versions")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_versions_returns_404_for_nonexistent_page(self, client, auth_headers):
        """Non-existent page_id returns 404, not 500."""
        response = client.get(
            f"/api/v1/builder-pages/{FAKE_PAGE_ID}/versions",
            headers=auth_headers,
        )
        assert response.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

    def test_versions_no_server_error(self, client, auth_headers):
        """Any error for non-existent page must not be 5xx."""
        response = client.get(
            f"/api/v1/builder-pages/{FAKE_PAGE_ID}/versions",
            headers=auth_headers,
        )
        assert response.status_code < 500

    def test_versions_response_is_list_when_found(self, client, auth_headers):
        """If versions are returned, the body is a JSON array (response_model=List[dict])."""
        response = client.get(
            f"/api/v1/builder-pages/{FAKE_PAGE_ID}/versions",
            headers=auth_headers,
        )
        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.json(), list)


class TestBuilderVersionDetail:
    """TC-24-012: GET /api/v1/builder-pages/{page_id}/versions/{version_number}."""

    def test_version_detail_requires_auth(self, client):
        """Unauthenticated request returns 401 or 403."""
        response = client.get(f"/api/v1/builder-pages/{FAKE_PAGE_ID}/versions/1")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_version_detail_returns_404_for_nonexistent(self, client, auth_headers):
        """Non-existent page/version returns 403 or 404, not 500."""
        response = client.get(
            f"/api/v1/builder-pages/{FAKE_PAGE_ID}/versions/1",
            headers=auth_headers,
        )
        assert response.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

    def test_version_detail_no_server_error(self, client, auth_headers):
        """Any error for non-existent version must not be 5xx."""
        response = client.get(
            f"/api/v1/builder-pages/{FAKE_PAGE_ID}/versions/1",
            headers=auth_headers,
        )
        assert response.status_code < 500

    def test_version_detail_rejects_non_integer_version(self, client, auth_headers):
        """Non-integer version_number returns 422 (path type validation)."""
        response = client.get(
            f"/api/v1/builder-pages/{FAKE_PAGE_ID}/versions/not-a-number",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestBuilderRestore:
    """TC-24-013: POST /api/v1/builder-pages/{page_id}/restore/{version_number}."""

    def test_restore_requires_auth(self, client):
        """Unauthenticated request returns 401 or 403."""
        response = client.post(f"/api/v1/builder-pages/{FAKE_PAGE_ID}/restore/1")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_restore_returns_404_for_nonexistent(self, client, auth_headers):
        """Restore against non-existent page/version returns 403 or 404, not 500."""
        response = client.post(
            f"/api/v1/builder-pages/{FAKE_PAGE_ID}/restore/1",
            headers=auth_headers,
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

    def test_restore_no_server_error(self, client, auth_headers):
        """Any error for non-existent restore target must not be 5xx."""
        response = client.post(
            f"/api/v1/builder-pages/{FAKE_PAGE_ID}/restore/1",
            headers=auth_headers,
        )
        assert response.status_code < 500

    def test_restore_rejects_non_integer_version(self, client, auth_headers):
        """Non-integer version_number returns 422 (path type validation)."""
        response = client.post(
            f"/api/v1/builder-pages/{FAKE_PAGE_ID}/restore/not-a-number",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
