"""
TEMPLATE module test suite.

Run with:  pytest modules/TEMPLATE/tests/
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def module_path(tmp_path):
    """Create a minimal module directory for testing."""
    manifest = {
        "name": "TEMPLATE",
        "version": "1.0.0",
        "display_name": "TEMPLATE",
        "description": "Test module",
    }
    import json
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    return tmp_path


@pytest.fixture
def module(module_path):
    from modules.template.module import TEMPLATEModule
    from modules.sdk import PlatformBridge
    bridge = PlatformBridge()
    return TEMPLATEModule(module_path, bridge)


class TestTEMPLATEModule:

    def test_module_loads(self, module):
        assert module.name == "TEMPLATE"
        assert module.version == "1.0.0"

    def test_get_permissions_returns_list(self, module):
        perms = module.get_permissions()
        assert isinstance(perms, list)

    def test_post_install_runs_without_error(self, module):
        db = MagicMock()
        module.post_install(db)  # should not raise

    def test_post_enable_runs_without_error(self, module):
        db = MagicMock()
        module.post_enable(db, tenant_id="test-tenant-id")  # should not raise

    # TODO: add tests for your specific routes and models
