"""
Unit tests for app/core/module_system/loader.py

Tests ModuleLoader.discover_modules() and validate_manifest() using
a temporary filesystem — no DB, no running app.
"""
import json
import tempfile
from pathlib import Path

import pytest

from app.core.module_system.loader import ModuleLoader


# ── Helpers ───────────────────────────────────────────────────────────────


def _make_module_dir(root: Path, name: str, manifest: dict = None, has_module_py: bool = True):
    """Create a minimal valid module directory under root."""
    d = root / name
    d.mkdir()
    if manifest is not None:
        (d / "manifest.json").write_text(json.dumps(manifest))
    if has_module_py:
        (d / "module.py").write_text("# stub")
    return d


VALID_MANIFEST = {
    "name": "test_module",
    "version": "1.0.0",
    "display_name": "Test Module",
    "description": "A test module",
    "author": "Tester",
    "category": "core",
    "permissions": [],
    "menu_items": [],
    "dependencies": [],
}


# ── discover_modules ───────────────────────────────────────────────────────


def test_discover_empty_directory():
    with tempfile.TemporaryDirectory() as tmp:
        loader = ModuleLoader(Path(tmp))
        modules = loader.discover_modules()
        assert modules == []


def test_discover_nonexistent_path():
    loader = ModuleLoader(Path("/nonexistent/path/xyz"))
    modules = loader.discover_modules()
    assert modules == []


def test_discover_single_valid_module():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_module_dir(root, "billing", manifest=VALID_MANIFEST)
        loader = ModuleLoader(root)
        modules = loader.discover_modules()
        assert "billing" in modules


def test_discover_multiple_valid_modules():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name in ["crm", "billing", "hr"]:
            _make_module_dir(root, name, manifest=VALID_MANIFEST)
        loader = ModuleLoader(root)
        modules = loader.discover_modules()
        assert set(modules) == {"crm", "billing", "hr"}


def test_discover_skips_missing_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # has module.py but no manifest.json
        _make_module_dir(root, "no_manifest", manifest=None, has_module_py=True)
        loader = ModuleLoader(root)
        assert loader.discover_modules() == []


def test_discover_skips_missing_module_py():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # has manifest.json but no module.py
        d = root / "no_module"
        d.mkdir()
        (d / "manifest.json").write_text(json.dumps(VALID_MANIFEST))
        loader = ModuleLoader(root)
        assert loader.discover_modules() == []


def test_discover_skips_pycache():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pycache = root / "__pycache__"
        pycache.mkdir()
        (pycache / "manifest.json").write_text("{}")
        (pycache / "module.py").write_text("")
        loader = ModuleLoader(root)
        modules = loader.discover_modules()
        assert "__pycache__" not in modules


def test_discover_skips_hidden_directories():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        hidden = root / ".hidden"
        hidden.mkdir()
        (hidden / "manifest.json").write_text("{}")
        (hidden / "module.py").write_text("")
        loader = ModuleLoader(root)
        modules = loader.discover_modules()
        assert ".hidden" not in modules


def test_discover_skips_files_not_directories():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "not_a_dir.txt").write_text("hello")
        _make_module_dir(root, "valid", manifest=VALID_MANIFEST)
        loader = ModuleLoader(root)
        modules = loader.discover_modules()
        assert "not_a_dir.txt" not in modules
        assert "valid" in modules


def test_discover_returns_list():
    with tempfile.TemporaryDirectory() as tmp:
        loader = ModuleLoader(Path(tmp))
        result = loader.discover_modules()
        assert isinstance(result, list)


# ── validate_manifest ─────────────────────────────────────────────────────


def test_validate_manifest_valid():
    with tempfile.TemporaryDirectory() as tmp:
        loader = ModuleLoader(Path(tmp))
        # validate_manifest should not raise for a complete manifest
        result = loader.validate_manifest(VALID_MANIFEST)
        # returns truthy or None — just must not raise
        assert result is not False


jsonschema_installed = pytest.importorskip.__doc__ and True
try:
    import jsonschema as _js  # noqa: F401
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False

requires_jsonschema = pytest.mark.skipif(
    not _HAS_JSONSCHEMA, reason="jsonschema not installed"
)


@requires_jsonschema
def test_validate_manifest_missing_name_fails():
    with tempfile.TemporaryDirectory() as tmp:
        loader = ModuleLoader(Path(tmp))
        bad = {k: v for k, v in VALID_MANIFEST.items() if k != "name"}
        result = loader.validate_manifest(bad)
        assert result is False or (isinstance(result, tuple) and not result[0])


@requires_jsonschema
def test_validate_manifest_missing_version_fails():
    with tempfile.TemporaryDirectory() as tmp:
        loader = ModuleLoader(Path(tmp))
        bad = {k: v for k, v in VALID_MANIFEST.items() if k != "version"}
        result = loader.validate_manifest(bad)
        assert result is False or (isinstance(result, tuple) and not result[0])


@requires_jsonschema
def test_validate_manifest_empty_dict_fails():
    with tempfile.TemporaryDirectory() as tmp:
        loader = ModuleLoader(Path(tmp))
        result = loader.validate_manifest({})
        assert result is False or (isinstance(result, tuple) and not result[0])


# ── Module caching ────────────────────────────────────────────────────────


def test_loaded_modules_starts_empty():
    with tempfile.TemporaryDirectory() as tmp:
        loader = ModuleLoader(Path(tmp))
        assert loader.loaded_modules == {}


def test_modules_path_stored_as_path():
    with tempfile.TemporaryDirectory() as tmp:
        loader = ModuleLoader(Path(tmp))
        assert isinstance(loader.modules_path, Path)
