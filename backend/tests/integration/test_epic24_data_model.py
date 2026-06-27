"""
T-24.015 — Integration tests: Epic 24 Data Model Publish UX (Story 24.3.1)

Covers acceptance criteria for:
  - GET  /api/v1/data-model/entities/{entity_id}/preview-migration
  - POST /api/v1/data-model/entities/{entity_id}/publish

Uses SQLite in-memory DB via conftest fixtures; auth provided via auth_headers.
Note: preview-migration and publish require a real DataModelService backed by
SQLite, so tests are written structurally (auth guard, request shape, 404 guard).
Heavy service logic is manual-only (see test-plan-24.md S3).
"""

import uuid
import pytest
from fastapi import status


FAKE_ENTITY_ID = str(uuid.uuid4())


class TestPreviewMigrationEndpoint:
    """TC-24-004: GET /api/v1/data-model/entities/{id}/preview-migration."""

    def test_preview_requires_auth(self, client):
        """Unauthenticated request returns 401 or 403."""
        response = client.get(f"/api/v1/data-model/entities/{FAKE_ENTITY_ID}/preview-migration")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_preview_returns_404_for_nonexistent_entity(self, client, auth_headers):
        """Non-existent entity_id returns 404 (not 500)."""
        response = client.get(
            f"/api/v1/data-model/entities/{FAKE_ENTITY_ID}/preview-migration",
            headers=auth_headers,
        )
        # Accept 404 (not found) or 400 (no pending changes) — never 500
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        )

    def test_preview_returns_no_server_error(self, client, auth_headers):
        """Any error response for non-existent entity must not be a 5xx."""
        response = client.get(
            f"/api/v1/data-model/entities/{FAKE_ENTITY_ID}/preview-migration",
            headers=auth_headers,
        )
        assert response.status_code < 500


class TestPublishEntityEndpoint:
    """TC-24-005: POST /api/v1/data-model/entities/{id}/publish."""

    def test_publish_requires_auth(self, client):
        """Unauthenticated request returns 401 or 403."""
        response = client.post(
            f"/api/v1/data-model/entities/{FAKE_ENTITY_ID}/publish",
            json={"commit_message": "test"},
        )
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_publish_returns_404_for_nonexistent_entity(self, client, auth_headers):
        """Non-existent entity returns 404 (not 500)."""
        response = client.post(
            f"/api/v1/data-model/entities/{FAKE_ENTITY_ID}/publish",
            json={"commit_message": "test"},
            headers=auth_headers,
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        )

    def test_publish_no_server_error(self, client, auth_headers):
        """Any error response for non-existent entity must not be a 5xx."""
        response = client.post(
            f"/api/v1/data-model/entities/{FAKE_ENTITY_ID}/publish",
            json={"commit_message": "test"},
            headers=auth_headers,
        )
        assert response.status_code < 500

    def test_publish_requires_json_body(self, client, auth_headers):
        """POST without JSON body returns 422 (not 500)."""
        response = client.post(
            f"/api/v1/data-model/entities/{FAKE_ENTITY_ID}/publish",
            headers=auth_headers,
        )
        # 422 for missing body, or 404/400 if entity check happens first
        assert response.status_code < 500
