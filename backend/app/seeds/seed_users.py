"""Seed users with hashed passwords"""
import os
import uuid
from sqlalchemy import create_engine, text
from app.core.auth import hash_password

DB_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "sqlite:///./app.db")
engine = create_engine(DB_URL, future=True)

def run():
    with engine.begin() as conn:
        # Create admin user
        admin_id = str(uuid.uuid4())
        admin_password = hash_password("admin123")
        
        conn.execute(text("""
            INSERT INTO users (id, email, hashed_password, is_active, is_superuser, full_name, roles)
            VALUES (:id, :email, :password, :active, :superuser, :name, :roles)
        """), dict(
            id=admin_id,
            email="admin@example.com",
            password=admin_password,
            active=True,
            superuser=True,
            name="System Administrator",
            roles='["admin", "user"]'
        ))
        
        # Create regular user
        user_id = str(uuid.uuid4())
        user_password = hash_password("user123")
        
        conn.execute(text("""
            INSERT INTO users (id, email, hashed_password, is_active, is_superuser, full_name, roles, tenant_id)
            VALUES (:id, :email, :password, :active, :superuser, :name, :roles, :tenant)
        """), dict(
            id=user_id,
            email="user@example.com",
            password=user_password,
            active=True,
            superuser=False,
            name="Regular User",
            roles='["user", "viewer"]',
            tenant="ACME"
        ))
        
        # Create viewer user
        viewer_id = str(uuid.uuid4())
        viewer_password = hash_password("viewer123")
        
        conn.execute(text("""
            INSERT INTO users (id, email, hashed_password, is_active, is_superuser, full_name, roles)
            VALUES (:id, :email, :password, :active, :superuser, :name, :roles)
        """), dict(
            id=viewer_id,
            email="viewer@example.com",
            password=viewer_password,
            active=True,
            superuser=False,
            name="View Only User",
            roles='["viewer"]'
        ))
    
    print("User seed completed.")
    print("\nTest Credentials:")
    print("  Admin: admin@example.com / admin123")
    print("  User:  user@example.com / user123")
    print("  Viewer: viewer@example.com / viewer123")

if __name__ == "__main__":
    run()