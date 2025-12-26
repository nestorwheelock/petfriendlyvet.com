"""Rate limiting using token bucket algorithm with Django cache backend."""
import time
from django.core.cache import cache


class TokenBucketRateLimiter:
    """Token bucket rate limiter using Django cache.

    Each IP has a bucket with a maximum number of tokens.
    Tokens are consumed on each request and refill over time.
    """

    def __init__(self, max_requests: int = 200, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in the window.
            window_seconds: Time window in seconds.
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.refill_rate = max_requests / window_seconds  # tokens per second

    def _get_bucket_key(self, ip: str) -> str:
        """Get cache key for an IP's bucket."""
        return f"waf:rate:{ip}"

    def is_allowed(self, ip: str) -> tuple[bool, int]:
        """Check if a request from this IP is allowed.

        Args:
            ip: The client IP address.

        Returns:
            Tuple of (allowed: bool, remaining: int)
        """
        key = self._get_bucket_key(ip)
        now = time.time()

        # Get current bucket state
        bucket = cache.get(key)

        if bucket is None:
            # New bucket - full capacity
            bucket = {
                'tokens': self.max_requests - 1,  # Consume one token
                'last_update': now,
            }
            cache.set(key, bucket, self.window_seconds * 2)
            return True, int(bucket['tokens'])

        # Calculate tokens to add based on time passed
        elapsed = now - bucket['last_update']
        tokens_to_add = elapsed * self.refill_rate

        # Update token count (cap at max)
        current_tokens = min(
            self.max_requests,
            bucket['tokens'] + tokens_to_add
        )

        if current_tokens < 1:
            # No tokens available - rate limited
            return False, 0

        # Consume a token
        bucket['tokens'] = current_tokens - 1
        bucket['last_update'] = now
        cache.set(key, bucket, self.window_seconds * 2)

        return True, int(bucket['tokens'])

    def get_remaining(self, ip: str) -> int:
        """Get remaining requests for an IP.

        Args:
            ip: The client IP address.

        Returns:
            Number of remaining requests allowed.
        """
        key = self._get_bucket_key(ip)
        bucket = cache.get(key)

        if bucket is None:
            return self.max_requests

        now = time.time()
        elapsed = now - bucket['last_update']
        tokens_to_add = elapsed * self.refill_rate

        return int(min(self.max_requests, bucket['tokens'] + tokens_to_add))

    def reset(self, ip: str) -> None:
        """Reset rate limit for an IP.

        Args:
            ip: The client IP address.
        """
        key = self._get_bucket_key(ip)
        cache.delete(key)


# Default rate limiter instance
rate_limiter = TokenBucketRateLimiter()


def check_rate_limit(ip: str, max_requests: int = 200, window: int = 60) -> tuple[bool, int]:
    """Check rate limit for an IP.

    Args:
        ip: Client IP address.
        max_requests: Max requests in window.
        window: Window in seconds.

    Returns:
        Tuple of (allowed, remaining).
    """
    limiter = TokenBucketRateLimiter(max_requests, window)
    return limiter.is_allowed(ip)
