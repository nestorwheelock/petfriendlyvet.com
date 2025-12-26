"""Security event logging for fail2ban integration.

Outputs logs in a format compatible with fail2ban parsing:
    2025-12-26 10:15:23 [SECURITY] FAILED_LOGIN ip=192.168.1.100 path=/login/
    2025-12-26 10:15:24 [SECURITY] INVALID_TOKEN ip=192.168.1.100 path=/staff-xyz123/
    2025-12-26 10:15:25 [SECURITY] RATE_LIMIT ip=192.168.1.100 count=150
    2025-12-26 10:15:26 [SECURITY] SQLI_DETECTED ip=192.168.1.100 pattern="union select"
"""
import logging
import os
from datetime import datetime
from django.conf import settings


# Create a dedicated security logger
security_logger = logging.getLogger('waf.security')


def setup_security_logger():
    """Set up the security logger for fail2ban integration."""
    # Get log path from settings or use default
    log_path = getattr(settings, 'WAF_LOG_PATH', '/var/log/django/security.log')

    # Ensure directory exists
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except (OSError, PermissionError):
            # Fall back to project directory
            log_path = os.path.join(settings.BASE_DIR, 'logs', 'security.log')
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # Only add handler if not already configured
    if not security_logger.handlers:
        try:
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.INFO)

            # Format: timestamp [SECURITY] EVENT_TYPE key=value key=value
            formatter = logging.Formatter(
                '%(asctime)s [SECURITY] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            security_logger.addHandler(file_handler)
            security_logger.setLevel(logging.INFO)
        except (OSError, PermissionError) as e:
            # Log to console if file logging fails
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s [SECURITY] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            security_logger.addHandler(console_handler)
            security_logger.setLevel(logging.INFO)
            security_logger.warning(f"Could not set up file logging: {e}")


def log_failed_login(ip: str, path: str, username: str = None):
    """Log a failed login attempt.

    Args:
        ip: Client IP address.
        path: Request path.
        username: Attempted username if available.
    """
    msg = f"FAILED_LOGIN ip={ip} path={path}"
    if username:
        msg += f" username={username}"
    security_logger.info(msg)


def log_invalid_token(ip: str, path: str, token_type: str = 'unknown'):
    """Log an invalid token access attempt.

    Args:
        ip: Client IP address.
        path: Request path.
        token_type: Type of token (admin, staff).
    """
    security_logger.info(f"INVALID_TOKEN ip={ip} path={path} type={token_type}")


def log_rate_limit(ip: str, count: int, path: str = None):
    """Log rate limit exceeded.

    Args:
        ip: Client IP address.
        count: Number of requests made.
        path: Request path if available.
    """
    msg = f"RATE_LIMIT ip={ip} count={count}"
    if path:
        msg += f" path={path}"
    security_logger.info(msg)


def log_pattern_detected(ip: str, pattern_type: str, path: str, matched: str = None):
    """Log detected attack pattern.

    Args:
        ip: Client IP address.
        pattern_type: Type of pattern (sqli, xss, path_traversal).
        path: Request path.
        matched: Matched pattern string.
    """
    msg = f"PATTERN_DETECTED ip={ip} pattern={pattern_type} path={path}"
    if matched:
        # Sanitize matched pattern for logging
        safe_matched = matched.replace('"', '\\"')[:100]
        msg += f' matched="{safe_matched}"'
    security_logger.info(msg)


def log_ip_banned(ip: str, reason: str, duration: int = None):
    """Log IP ban.

    Args:
        ip: Client IP address.
        reason: Ban reason.
        duration: Ban duration in seconds.
    """
    msg = f"IP_BANNED ip={ip} reason={reason}"
    if duration:
        msg += f" duration={duration}s"
    security_logger.info(msg)


def log_banned_access(ip: str, path: str):
    """Log access attempt from banned IP.

    Args:
        ip: Client IP address.
        path: Request path.
    """
    security_logger.info(f"BANNED_ACCESS ip={ip} path={path}")


def log_geo_blocked(ip: str, country_code: str, path: str):
    """Log geo-blocked access.

    Args:
        ip: Client IP address.
        country_code: Country code of the IP.
        path: Request path.
    """
    security_logger.info(f"GEO_BLOCKED ip={ip} country={country_code} path={path}")


def log_security_event(event_type: str, ip: str, **kwargs):
    """Generic security event logger.

    Args:
        event_type: Type of event (uppercase).
        ip: Client IP address.
        **kwargs: Additional key=value pairs to log.
    """
    parts = [f"{event_type} ip={ip}"]
    for key, value in kwargs.items():
        if value is not None:
            parts.append(f"{key}={value}")
    security_logger.info(' '.join(parts))


# Initialize logger when module is imported
setup_security_logger()
