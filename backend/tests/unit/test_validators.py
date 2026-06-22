"""
Unit tests for app/core/validators.py

Pure-function tests — no DB, no network.
"""
import pytest

from app.core.validators import ValidationRules


# ── validate_string_length ────────────────────────────────────────────────


def test_string_length_ok():
    result = ValidationRules.validate_string_length("hello", 10, "Field")
    assert result == "hello"


def test_string_length_strips_whitespace():
    result = ValidationRules.validate_string_length("  hi  ", 10, "Field")
    assert result == "hi"


def test_string_length_exactly_max_ok():
    result = ValidationRules.validate_string_length("a" * 50, 50, "Field")
    assert len(result) == 50


def test_string_length_over_max_raises():
    with pytest.raises(ValueError, match="must not exceed"):
        ValidationRules.validate_string_length("a" * 51, 50, "Field")


def test_string_length_none_returns_none():
    assert ValidationRules.validate_string_length(None, 50, "Field") is None


# ── validate_code ─────────────────────────────────────────────────────────


def test_validate_code_alphanumeric():
    assert ValidationRules.validate_code("ABC123") == "ABC123"


def test_validate_code_with_underscore():
    assert ValidationRules.validate_code("MY_CODE") == "MY_CODE"


def test_validate_code_with_hyphen():
    assert ValidationRules.validate_code("my-code") == "my-code"


def test_validate_code_strips_whitespace():
    assert ValidationRules.validate_code("  CODE  ") == "CODE"


def test_validate_code_lowercase_ok():
    assert ValidationRules.validate_code("mycode") == "mycode"


def test_validate_code_invalid_space_raises():
    with pytest.raises(ValueError, match="letters, numbers"):
        ValidationRules.validate_code("MY CODE")


def test_validate_code_invalid_dot_raises():
    with pytest.raises(ValueError):
        ValidationRules.validate_code("my.code")


def test_validate_code_too_long_raises():
    with pytest.raises(ValueError, match="must not exceed"):
        ValidationRules.validate_code("A" * 51)


def test_validate_code_none_returns_none():
    assert ValidationRules.validate_code(None) is None


# ── validate_uuid ─────────────────────────────────────────────────────────


def test_validate_uuid_valid():
    uid = "550e8400-e29b-41d4-a716-446655440000"
    assert ValidationRules.validate_uuid(uid) == uid


def test_validate_uuid_uppercase_ok():
    uid = "550E8400-E29B-41D4-A716-446655440000"
    result = ValidationRules.validate_uuid(uid)
    assert result.lower() == uid.lower()


def test_validate_uuid_strips_whitespace():
    uid = "  550e8400-e29b-41d4-a716-446655440000  "
    result = ValidationRules.validate_uuid(uid)
    assert result == uid.strip()


def test_validate_uuid_invalid_raises():
    with pytest.raises(ValueError, match="valid UUID"):
        ValidationRules.validate_uuid("not-a-uuid")


def test_validate_uuid_empty_raises():
    with pytest.raises(ValueError):
        ValidationRules.validate_uuid("")


def test_validate_uuid_none_returns_none():
    assert ValidationRules.validate_uuid(None) is None


# ── validate_name ─────────────────────────────────────────────────────────


def test_validate_name_ok():
    assert ValidationRules.validate_name("My Name") == "My Name"


def test_validate_name_strips():
    assert ValidationRules.validate_name("  Name  ") == "Name"


def test_validate_name_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        ValidationRules.validate_name("   ")


def test_validate_name_too_long_raises():
    with pytest.raises(ValueError):
        ValidationRules.validate_name("x" * 256)


def test_validate_name_script_tag_raises():
    with pytest.raises(ValueError, match="invalid characters"):
        ValidationRules.validate_name("Name<script>")


def test_validate_name_curly_brace_raises():
    with pytest.raises(ValueError):
        ValidationRules.validate_name("Name{bad}")


# ── sanitize_json_field ────────────────────────────────────────────────────


def test_sanitize_json_none_ok():
    assert ValidationRules.sanitize_json_field(None) is None


def test_sanitize_json_clean_string_ok():
    assert ValidationRules.sanitize_json_field("hello world") == "hello world"


def test_sanitize_json_script_raises():
    with pytest.raises(ValueError, match="dangerous"):
        ValidationRules.sanitize_json_field("<script>alert(1)</script>")


def test_sanitize_json_javascript_protocol_raises():
    with pytest.raises(ValueError):
        ValidationRules.sanitize_json_field("javascript:void(0)")


def test_sanitize_json_non_string_passes():
    assert ValidationRules.sanitize_json_field({"key": "value"}) == {"key": "value"}
    assert ValidationRules.sanitize_json_field(42) == 42
