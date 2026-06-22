"""
Unit tests for app/core/password_validator.py

Tests PasswordValidator.validate_strength() — no DB, no async required.
"""
import pytest

from app.core.password_validator import PasswordValidator
from app.core.security_config import PasswordPolicyConfig


def make_validator(**overrides) -> PasswordValidator:
    """Return a PasswordValidator with default strict policy, plus any overrides."""
    defaults = dict(
        min_length=8,
        max_length=128,
        require_uppercase=True,
        require_lowercase=True,
        require_digit=True,
        require_special_char=True,
        min_unique_chars=4,
        max_repeating_chars=3,
        allow_common=False,
        allow_username=False,
        history_count=0,
    )
    defaults.update(overrides)
    policy = PasswordPolicyConfig(**defaults)
    return PasswordValidator(policy)


# ── Length checks ─────────────────────────────────────────────────────────


def test_too_short_fails():
    v = make_validator(min_length=10)
    ok, errors = v.validate_strength("Short1!")
    assert not ok
    assert any("at least 10" in e for e in errors)


def test_exactly_min_length_passes_length_rule():
    v = make_validator(min_length=8, require_special_char=False,
                       require_uppercase=False, require_lowercase=False,
                       require_digit=False, allow_common=True,
                       min_unique_chars=1, max_repeating_chars=0)
    ok, errors = v.validate_strength("aaaaaaaa")
    # length rule itself should not appear in errors
    assert not any("at least 8" in e for e in errors)


def test_too_long_fails():
    v = make_validator(max_length=16)
    ok, errors = v.validate_strength("A" * 17 + "a1!")
    assert not ok
    assert any("must not exceed" in e for e in errors)


# ── Complexity requirements ───────────────────────────────────────────────


def test_missing_uppercase_fails():
    v = make_validator(require_uppercase=True)
    ok, errors = v.validate_strength("alllower1!")
    assert not ok
    assert any("uppercase" in e for e in errors)


def test_missing_lowercase_fails():
    v = make_validator(require_lowercase=True)
    ok, errors = v.validate_strength("ALLUPPER1!")
    assert not ok
    assert any("lowercase" in e for e in errors)


def test_missing_digit_fails():
    v = make_validator(require_digit=True)
    ok, errors = v.validate_strength("NoDigits!")
    assert not ok
    assert any("digit" in e for e in errors)


def test_missing_special_fails():
    v = make_validator(require_special_char=True)
    ok, errors = v.validate_strength("NoSpecial1")
    assert not ok
    assert any("special" in e for e in errors)


def test_all_complexity_met_no_complexity_errors():
    v = make_validator(allow_common=True, min_unique_chars=1, max_repeating_chars=0)
    ok, errors = v.validate_strength("Passw0rd!")
    complexity_errors = [e for e in errors if any(
        kw in e for kw in ["uppercase", "lowercase", "digit", "special"])]
    assert complexity_errors == []


# ── Unique characters ─────────────────────────────────────────────────────


def test_too_few_unique_chars_fails():
    v = make_validator(min_unique_chars=6, require_special_char=False,
                       require_uppercase=False, allow_common=True)
    ok, errors = v.validate_strength("aaaaa1b")  # only 3 unique
    assert not ok
    assert any("unique" in e for e in errors)


def test_enough_unique_chars_ok():
    v = make_validator(min_unique_chars=4, allow_common=True)
    ok, errors = v.validate_strength("Abcd1234!")
    unique_errors = [e for e in errors if "unique" in e]
    assert unique_errors == []


# ── Repeating characters ──────────────────────────────────────────────────


def test_repeating_chars_exceeds_max_fails():
    v = make_validator(max_repeating_chars=2, allow_common=True,
                       require_special_char=False)
    ok, errors = v.validate_strength("Aaaa1234")  # 'a' repeats 3 times
    assert not ok
    assert any("repeating" in e for e in errors)


def test_repeating_chars_within_limit_ok():
    v = make_validator(max_repeating_chars=3, allow_common=True,
                       require_special_char=False)
    ok, errors = v.validate_strength("Aaa12345")  # 'a' repeats 2 times
    rep_errors = [e for e in errors if "repeating" in e]
    assert rep_errors == []


def test_repeating_check_disabled_when_zero():
    v = make_validator(max_repeating_chars=0, allow_common=True,
                       require_special_char=False)
    ok, errors = v.validate_strength("Aaaaaaa1")  # many repeats, but disabled
    rep_errors = [e for e in errors if "repeating" in e]
    assert rep_errors == []


# ── Common passwords ──────────────────────────────────────────────────────


def test_common_password_rejected():
    v = make_validator(allow_common=False, require_special_char=False,
                       require_uppercase=False, min_unique_chars=1,
                       max_repeating_chars=0)
    ok, errors = v.validate_strength("password")
    assert not ok
    assert any("common" in e for e in errors)


def test_common_password_allowed_when_policy_permits():
    v = make_validator(allow_common=True, require_special_char=False,
                       require_uppercase=False, min_unique_chars=1,
                       max_repeating_chars=0)
    ok, errors = v.validate_strength("password")
    common_errors = [e for e in errors if "common" in e]
    assert common_errors == []


# ── Username / email similarity ───────────────────────────────────────────


def test_password_contains_email_fails():
    v = make_validator(allow_username=False)
    ok, errors = v.validate_strength("Alice@example.com1!", user_email="alice@example.com")
    assert not ok
    assert any("email" in e for e in errors)


def test_password_contains_username_fails():
    v = make_validator(allow_username=False)
    ok, errors = v.validate_strength("AlicePass1!", user_name="alice")
    assert not ok
    assert any("name" in e for e in errors)


def test_similarity_allowed_when_policy_permits():
    v = make_validator(allow_username=True)
    ok, errors = v.validate_strength("AlicePass1!", user_name="alice")
    name_errors = [e for e in errors if "name" in e]
    assert name_errors == []


def test_no_user_info_provided_no_similarity_error():
    v = make_validator(allow_username=False, allow_common=True,
                       require_special_char=False, min_unique_chars=1,
                       max_repeating_chars=0)
    ok, errors = v.validate_strength("Passw0rd")
    assert not any("email" in e or "name" in e for e in errors)


# ── Return type ───────────────────────────────────────────────────────────


def test_returns_tuple():
    v = make_validator()
    result = v.validate_strength("Str0ng!Pass")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], bool)
    assert isinstance(result[1], list)


def test_valid_password_returns_empty_errors():
    v = make_validator(allow_common=True)
    ok, errors = v.validate_strength("Str0ng!Pass")
    assert ok is True
    assert errors == []
