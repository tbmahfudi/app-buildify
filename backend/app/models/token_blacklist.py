from sqlalchemy import Column, String, DateTime, func, Index
from .base import Base

class TokenBlacklist(Base):
    """
    Token blacklist for JWT revocation.
    Uses UNLOGGED table for PostgreSQL or MEMORY engine for MySQL for performance.
    Tokens are automatically cleaned up after expiration.
    """
    __tablename__ = "token_blacklist"
    __table_args__ = (
        Index('ix_token_blacklist_jti', 'jti'),
        Index('ix_token_blacklist_expires_at', 'expires_at'),
        # MySQL MEMORY engine option for better performance
        {'mysql_engine': 'MEMORY'}
    )

    jti = Column(String(255), primary_key=True)  # JWT ID (unique token identifier)
    user_id = Column(String(36), nullable=False, index=True)
    token_type = Column(String(20), nullable=False)  # 'access' or 'refresh'
    expires_at = Column(DateTime, nullable=False)
    blacklisted_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<TokenBlacklist(jti={self.jti}, user_id={self.user_id}, type={self.token_type})>"
