"""
Token Blacklist Cleanup Utility

This module provides functionality to clean up expired tokens from the blacklist.
Run this periodically (e.g., via cron job or background task) to prevent the blacklist
from growing indefinitely.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from ..models.token_blacklist import TokenBlacklist
import logging

logger = logging.getLogger(__name__)


def cleanup_expired_tokens(db: Session) -> int:
    """
    Remove expired tokens from the blacklist.

    Args:
        db: SQLAlchemy database session

    Returns:
        Number of tokens removed
    """
    try:
        # Delete tokens where expires_at is in the past
        result = db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at < datetime.utcnow()
        ).delete()

        db.commit()
        logger.info(f"Cleaned up {result} expired tokens from blacklist")
        return result

    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {e}")
        db.rollback()
        return 0


def get_blacklist_stats(db: Session) -> dict:
    """
    Get statistics about the token blacklist.

    Args:
        db: SQLAlchemy database session

    Returns:
        Dictionary with blacklist statistics
    """
    total = db.query(TokenBlacklist).count()
    expired = db.query(TokenBlacklist).filter(
        TokenBlacklist.expires_at < datetime.utcnow()
    ).count()
    active = total - expired

    return {
        "total": total,
        "expired": expired,
        "active": active
    }
