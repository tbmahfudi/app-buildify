from typing import Optional
import redis
from datetime import timedelta
from .config import get_settings
from .logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RedisClient:
    """Redis client wrapper for token revocation and caching"""

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    def connect(self) -> bool:
        """
        Connect to Redis server.

        Returns:
            True if connection successful, False otherwise
        """
        if not settings.REDIS_URL and not settings.REDIS_HOST:
            logger.warning("Redis not configured, token revocation will be disabled")
            return False

        try:
            self._client = redis.from_url(
                settings.redis_url_computed,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Test connection
            self._client.ping()
            logger.info("Successfully connected to Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._client = None
            return False

    def disconnect(self):
        """Disconnect from Redis"""
        if self._client:
            self._client.close()
            logger.info("Disconnected from Redis")

    @property
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not self._client:
            return False
        try:
            self._client.ping()
            return True
        except:
            return False

    def revoke_token(self, token_jti: str, expires_in: int) -> bool:
        """
        Revoke a JWT token by adding it to the revocation list.

        Args:
            token_jti: The JWT ID (jti) claim from the token
            expires_in: Time until token expires (in seconds)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            logger.warning("Redis unavailable, cannot revoke token")
            return False

        try:
            key = f"revoked_token:{token_jti}"
            self._client.setex(key, expires_in, "revoked")
            logger.info(f"Token revoked: {token_jti}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    def is_token_revoked(self, token_jti: str) -> bool:
        """
        Check if a token has been revoked.

        Args:
            token_jti: The JWT ID (jti) claim from the token

        Returns:
            True if token is revoked, False otherwise
        """
        if not self.is_available:
            # If Redis is down, allow the token (fail open)
            return False

        try:
            key = f"revoked_token:{token_jti}"
            return self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check token revocation: {e}")
            # If Redis fails, allow the token (fail open)
            return False

    def set_cache(self, key: str, value: str, ttl: int = 300) -> bool:
        """
        Set a cached value.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 5 minutes)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False

        try:
            self._client.setex(f"cache:{key}", ttl, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False

    def get_cache(self, key: str) -> Optional[str]:
        """
        Get a cached value.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.is_available:
            return None

        try:
            return self._client.get(f"cache:{key}")
        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return None

    def delete_cache(self, key: str) -> bool:
        """
        Delete a cached value.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False

        try:
            self._client.delete(f"cache:{key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Get the global Redis client instance"""
    return redis_client
