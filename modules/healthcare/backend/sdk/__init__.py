"""
Healthcare SDK — public surface re-exports.

Patient OTP is **not** here: it is a platform service (`app.routers.otp`), per
ADR-009 and tasks-011 S6a. The module-local `otp.py` this SDK used to re-export was
a second implementation with no daily cap, and it is gone.

Import from here in healthcare sub-module code::

    from modules.healthcare.sdk import (
        get_current_patient,
        has_patient_permission,
        verify_hcaptcha,
        require_captcha,
        resolve_locale,
        t,
        encrypt_phi,
        decrypt_phi,
        EncryptedPHIType,
        generate_phi_key,
        BranchScopeListener,
        BranchScopeMissingError,
        healthcare_branch_session,
        HC_TENANT_RLS_POLICY_SQL,
        HC_BRANCH_RLS_POLICY_SQL,
        apply_tenant_rls,
        apply_branch_rls,
    )
"""
from .patient_auth import (
    PatientTokenData,
    get_current_patient,
    has_patient_permission,
)
from .captcha import (
    verify_hcaptcha,
    require_captcha,
)
from .locale import (
    resolve_locale,
    t,
    SUPPORTED_LOCALES,
    DEFAULT_LOCALE,
    FALLBACK_LOCALE,
)
from .phi_crypto import (
    EncryptedPHIType,
    generate_phi_key,
    encrypt_phi,
    decrypt_phi,
)
from .branch_scope import (
    BranchScopeListener,
    BranchScopeMissingError,
    healthcare_branch_session,
    set_branch_scope,
    clear_branch_scope,
)
from .rls_policies import (
    HC_TENANT_RLS_POLICY_SQL,
    HC_BRANCH_RLS_POLICY_SQL,
    apply_tenant_rls,
    apply_branch_rls,
)

__all__ = [
    # patient_auth
    "PatientTokenData",
    "get_current_patient",
    "has_patient_permission",
    # captcha
    "verify_hcaptcha",
    "require_captcha",
    # locale
    "resolve_locale",
    "t",
    "SUPPORTED_LOCALES",
    "DEFAULT_LOCALE",
    "FALLBACK_LOCALE",
    # phi_crypto
    "EncryptedPHIType",
    "generate_phi_key",
    "encrypt_phi",
    "decrypt_phi",
    # branch_scope
    "BranchScopeListener",
    "BranchScopeMissingError",
    "healthcare_branch_session",
    "set_branch_scope",
    "clear_branch_scope",
    # rls_policies
    "HC_TENANT_RLS_POLICY_SQL",
    "HC_BRANCH_RLS_POLICY_SQL",
    "apply_tenant_rls",
    "apply_branch_rls",
]
