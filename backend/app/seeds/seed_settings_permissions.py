"""
Create settings management permissions
Covers: General Settings, Integration, API Keys, Email, SMS, Metadata
"""
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission

def seed_settings_permissions():
    """Seed all settings-related permissions"""
    db = SessionLocal()

    try:
        # Define all settings permissions
        permissions = [
            # ==================== GENERAL SETTINGS ====================
            {
                "code": "settings:read:all",
                "name": "View All Settings",
                "description": "View all system settings (Superuser only)",
                "resource": "settings",
                "action": "read",
                "scope": "all",
                "category": "settings"
            },
            {
                "code": "settings:read:tenant",
                "name": "View Tenant Settings",
                "description": "View tenant settings",
                "resource": "settings",
                "action": "read",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "settings:read:own",
                "name": "View Own Settings",
                "description": "View own user settings",
                "resource": "settings",
                "action": "read",
                "scope": "own",
                "category": "settings"
            },
            {
                "code": "settings:update:all",
                "name": "Update All Settings",
                "description": "Update all system settings (Superuser only)",
                "resource": "settings",
                "action": "update",
                "scope": "all",
                "category": "settings"
            },
            {
                "code": "settings:update:tenant",
                "name": "Update Tenant Settings",
                "description": "Update tenant settings",
                "resource": "settings",
                "action": "update",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "settings:update:own",
                "name": "Update Own Settings",
                "description": "Update own user settings (theme, language, etc.)",
                "resource": "settings",
                "action": "update",
                "scope": "own",
                "category": "settings"
            },

            # ==================== BRANDING SETTINGS ====================
            {
                "code": "settings:branding:read:tenant",
                "name": "View Branding Settings",
                "description": "View tenant branding settings",
                "resource": "settings",
                "action": "branding:read",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "settings:branding:update:tenant",
                "name": "Update Branding Settings",
                "description": "Update branding (logo, colors, theme)",
                "resource": "settings",
                "action": "branding:update",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "settings:branding:tenant",
                "name": "Manage Branding (Legacy)",
                "description": "Manage branding - legacy permission for frontend compatibility",
                "resource": "settings",
                "action": "branding",
                "scope": "tenant",
                "category": "settings"
            },

            # ==================== THEME & LANGUAGE ====================
            {
                "code": "settings:theme:own",
                "name": "Change Own Theme",
                "description": "Change user theme preference",
                "resource": "settings",
                "action": "theme",
                "scope": "own",
                "category": "settings"
            },
            {
                "code": "settings:language:own",
                "name": "Change Own Language",
                "description": "Change user language preference",
                "resource": "settings",
                "action": "language",
                "scope": "own",
                "category": "settings"
            },

            # ==================== INTEGRATION SETTINGS ====================
            {
                "code": "settings:integration:read:all",
                "name": "View All Integrations",
                "description": "View all integration settings (Admin)",
                "resource": "settings",
                "action": "integration:read",
                "scope": "all",
                "category": "settings"
            },
            {
                "code": "settings:integration:read:tenant",
                "name": "View Tenant Integrations",
                "description": "View integration settings for tenant",
                "resource": "settings",
                "action": "integration:read",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "settings:integration:update:tenant",
                "name": "Configure Integrations",
                "description": "Configure integration settings",
                "resource": "settings",
                "action": "integration:update",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "integrations:read:tenant",
                "name": "View Integrations (Legacy)",
                "description": "View integrations - legacy permission for frontend compatibility",
                "resource": "integrations",
                "action": "read",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "integrations:configure:tenant",
                "name": "Configure Integrations (Legacy)",
                "description": "Configure integrations - legacy permission for frontend compatibility",
                "resource": "integrations",
                "action": "configure",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "integrations:enable:tenant",
                "name": "Enable Integrations",
                "description": "Enable third-party integrations",
                "resource": "integrations",
                "action": "enable",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "integrations:disable:tenant",
                "name": "Disable Integrations",
                "description": "Disable third-party integrations",
                "resource": "integrations",
                "action": "disable",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "integrations:test:tenant",
                "name": "Test Integrations",
                "description": "Test integration connections",
                "resource": "integrations",
                "action": "test",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "integrations:logs:read:tenant",
                "name": "View Integration Logs",
                "description": "View integration activity logs",
                "resource": "integrations",
                "action": "logs:read",
                "scope": "tenant",
                "category": "settings"
            },

            # ==================== API KEY MANAGEMENT ====================
            {
                "code": "settings:api_keys:read:all",
                "name": "View All API Keys",
                "description": "View all API keys (Admin)",
                "resource": "settings",
                "action": "api_keys:read",
                "scope": "all",
                "category": "settings"
            },
            {
                "code": "settings:api_keys:read:tenant",
                "name": "View Tenant API Keys",
                "description": "View API keys for tenant",
                "resource": "settings",
                "action": "api_keys:read",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "settings:api_keys:create:tenant",
                "name": "Generate API Keys",
                "description": "Generate new API keys",
                "resource": "settings",
                "action": "api_keys:create",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "settings:api_keys:revoke:tenant",
                "name": "Revoke API Keys",
                "description": "Revoke/disable API keys",
                "resource": "settings",
                "action": "api_keys:revoke",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "settings:api_keys:delete:tenant",
                "name": "Delete API Keys",
                "description": "Permanently delete API keys",
                "resource": "settings",
                "action": "api_keys:delete",
                "scope": "tenant",
                "category": "settings"
            },

            # ==================== EMAIL CONFIGURATION ====================
            {
                "code": "settings:email:read:all",
                "name": "View All Email Config",
                "description": "View all email configurations (Admin)",
                "resource": "settings",
                "action": "email:read",
                "scope": "all",
                "category": "settings"
            },
            {
                "code": "settings:email:read:tenant",
                "name": "View Tenant Email Config",
                "description": "View email configuration for tenant",
                "resource": "settings",
                "action": "email:read",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "settings:email:update:tenant",
                "name": "Update Email Config",
                "description": "Update email server settings",
                "resource": "settings",
                "action": "email:update",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "settings:email:test:tenant",
                "name": "Test Email Config",
                "description": "Send test emails",
                "resource": "settings",
                "action": "email:test",
                "scope": "tenant",
                "category": "settings"
            },

            # ==================== SMS CONFIGURATION ====================
            {
                "code": "settings:sms:read:all",
                "name": "View All SMS Config",
                "description": "View all SMS configurations (Admin)",
                "resource": "settings",
                "action": "sms:read",
                "scope": "all",
                "category": "settings"
            },
            {
                "code": "settings:sms:read:tenant",
                "name": "View Tenant SMS Config",
                "description": "View SMS configuration for tenant",
                "resource": "settings",
                "action": "sms:read",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "settings:sms:update:tenant",
                "name": "Update SMS Config",
                "description": "Update SMS gateway settings",
                "resource": "settings",
                "action": "sms:update",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "settings:sms:test:tenant",
                "name": "Test SMS Config",
                "description": "Send test SMS messages",
                "resource": "settings",
                "action": "sms:test",
                "scope": "tenant",
                "category": "settings"
            },

            # ==================== METADATA MANAGEMENT ====================
            {
                "code": "metadata:read:all",
                "name": "View All Metadata",
                "description": "View all entity metadata (Superuser)",
                "resource": "metadata",
                "action": "read",
                "scope": "all",
                "category": "settings"
            },
            {
                "code": "metadata:read:tenant",
                "name": "View Tenant Metadata",
                "description": "View entity metadata for tenant",
                "resource": "metadata",
                "action": "read",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "metadata:create:tenant",
                "name": "Create Entity Metadata",
                "description": "Create new entity metadata",
                "resource": "metadata",
                "action": "create",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "metadata:update:tenant",
                "name": "Update Entity Metadata",
                "description": "Update entity metadata definitions",
                "resource": "metadata",
                "action": "update",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "metadata:delete:tenant",
                "name": "Delete Entity Metadata",
                "description": "Delete entity metadata",
                "resource": "metadata",
                "action": "delete",
                "scope": "tenant",
                "category": "settings"
            },

            # ==================== SCHEMA DESIGN ====================
            {
                "code": "metadata:schema:design:tenant",
                "name": "Design Database Schemas",
                "description": "Design custom database schemas",
                "resource": "metadata",
                "action": "schema:design",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "metadata:schema:deploy:tenant",
                "name": "Deploy Schema Changes",
                "description": "Deploy database schema changes",
                "resource": "metadata",
                "action": "schema:deploy",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "metadata:schema:export:tenant",
                "name": "Export Schemas",
                "description": "Export schema definitions",
                "resource": "metadata",
                "action": "schema:export",
                "scope": "tenant",
                "category": "settings"
            },

            # ==================== FIELD CUSTOMIZATION ====================
            {
                "code": "metadata:fields:create:tenant",
                "name": "Add Custom Fields",
                "description": "Add custom fields to entities",
                "resource": "metadata",
                "action": "fields:create",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "metadata:fields:update:tenant",
                "name": "Update Field Definitions",
                "description": "Update custom field definitions",
                "resource": "metadata",
                "action": "fields:update",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "metadata:fields:delete:tenant",
                "name": "Remove Custom Fields",
                "description": "Remove custom fields from entities",
                "resource": "metadata",
                "action": "fields:delete",
                "scope": "tenant",
                "category": "settings"
            },

            # ==================== AUTH POLICIES ====================
            {
                "code": "auth_policies:read:tenant",
                "name": "View Auth Policies",
                "description": "View authentication policies",
                "resource": "auth_policies",
                "action": "read",
                "scope": "tenant",
                "category": "settings"
            },
            {
                "code": "auth_policies:update:tenant",
                "name": "Update Auth Policies",
                "description": "Update authentication policies (OAuth, SAML, LDAP)",
                "resource": "auth_policies",
                "action": "update",
                "scope": "tenant",
                "category": "settings"
            },
        ]

        # Create permissions
        created_count = 0
        updated_count = 0

        for perm_data in permissions:
            perm = db.query(Permission).filter(
                Permission.code == perm_data["code"]
            ).first()

            if not perm:
                perm = Permission(**perm_data, is_active=True)
                db.add(perm)
                db.flush()
                print(f"✓ Created: {perm_data['code']}")
                created_count += 1
            else:
                # Update existing permission details
                for key, value in perm_data.items():
                    setattr(perm, key, value)
                perm.is_active = True
                print(f"• Updated: {perm_data['code']}")
                updated_count += 1

        db.commit()

        print(f"\n{'='*60}")
        print(f"Settings Permissions Seed Complete")
        print(f"{'='*60}")
        print(f"✓ Created: {created_count} permissions")
        print(f"• Updated: {updated_count} permissions")
        print(f"📊 Total: {len(permissions)} settings permissions")
        print(f"{'='*60}\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_settings_permissions()
