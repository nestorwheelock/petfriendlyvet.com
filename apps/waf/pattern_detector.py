"""Pattern detection for SQL injection, XSS, path traversal, and data leaks."""
import re
from typing import NamedTuple


class DetectionResult(NamedTuple):
    """Result of pattern detection."""
    detected: bool
    pattern_type: str | None
    matched_pattern: str | None
    is_outbound: bool = False  # True for data leak detection in responses


# SQL Injection patterns
SQL_INJECTION_PATTERNS = [
    # Basic SQL keywords
    r"(?:union\s+(?:all\s+)?select)",
    r"(?:select\s+.+\s+from)",
    r"(?:insert\s+into)",
    r"(?:update\s+.+\s+set)",
    r"(?:delete\s+from)",
    r"(?:drop\s+(?:table|database))",
    r"(?:truncate\s+table)",
    # Comment-based attacks
    r"(?:--\s*$|#\s*$)",
    r"(?:/\*[\s\S]*?\*/)",
    # String-based attacks
    r"(?:'\s*or\s+'?1'?\s*=\s*'?1)",
    r"(?:'\s*or\s+''=')",
    r"(?:'\s*and\s+'?1'?\s*=\s*'?1)",
    # Function calls
    r"(?:sleep\s*\(\s*\d+\s*\))",
    r"(?:benchmark\s*\()",
    r"(?:load_file\s*\()",
    r"(?:into\s+(?:outfile|dumpfile))",
    # Information schema
    r"(?:information_schema)",
    r"(?:table_schema)",
    # EXEC/EXECUTE
    r"(?:exec(?:ute)?\s*\()",
    r"(?:xp_cmdshell)",
]

# XSS patterns
XSS_PATTERNS = [
    # Script tags
    r"(?:<\s*script[^>]*>)",
    r"(?:</\s*script\s*>)",
    # Event handlers
    r"(?:on(?:click|load|error|mouseover|submit|focus|blur|change)\s*=)",
    # JavaScript protocol
    r"(?:javascript\s*:)",
    r"(?:vbscript\s*:)",
    r"(?:data\s*:)",
    # Base64 encoded scripts
    r"(?:base64\s*,)",
    # Expression/eval
    r"(?:expression\s*\()",
    r"(?:eval\s*\()",
    # Document manipulation
    r"(?:document\s*\.\s*(?:cookie|location|write))",
    r"(?:window\s*\.\s*location)",
    # Alert/confirm/prompt
    r"(?:alert\s*\()",
    r"(?:confirm\s*\()",
    r"(?:prompt\s*\()",
    # SVG/object/embed
    r"(?:<\s*(?:svg|object|embed|iframe)[^>]*>)",
    # Style with expression
    r"(?:style\s*=\s*['\"][^'\"]*expression\s*\()",
]

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    # Basic traversal
    r"(?:\.\.\/)",
    r"(?:\.\.\\)",
    # URL encoded
    r"(?:%2e%2e%2f)",
    r"(?:%2e%2e/)",
    r"(?:\.\.%2f)",
    r"(?:%2e%2e%5c)",
    r"(?:%252e%252e%252f)",
    # Double URL encoded
    r"(?:%c0%ae%c0%ae/)",
    r"(?:%c0%ae%c0%ae\\)",
    # Null byte
    r"(?:%00)",
    # Absolute paths
    r"(?:/etc/passwd)",
    r"(?:/etc/shadow)",
    r"(?:c:\\windows)",
    r"(?:c:\\boot\.ini)",
]

# Compile patterns for performance
_sql_patterns = [re.compile(p, re.IGNORECASE) for p in SQL_INJECTION_PATTERNS]
_xss_patterns = [re.compile(p, re.IGNORECASE) for p in XSS_PATTERNS]
_path_patterns = [re.compile(p, re.IGNORECASE) for p in PATH_TRAVERSAL_PATTERNS]


def detect_sql_injection(text: str) -> DetectionResult:
    """Detect SQL injection patterns in text.

    Args:
        text: Text to scan (URL, query string, body, etc.)

    Returns:
        DetectionResult with detection status and matched pattern.
    """
    for pattern in _sql_patterns:
        match = pattern.search(text)
        if match:
            return DetectionResult(
                detected=True,
                pattern_type='sqli',
                matched_pattern=match.group(0)
            )
    return DetectionResult(detected=False, pattern_type=None, matched_pattern=None)


def detect_xss(text: str) -> DetectionResult:
    """Detect XSS patterns in text.

    Args:
        text: Text to scan (URL, query string, body, etc.)

    Returns:
        DetectionResult with detection status and matched pattern.
    """
    for pattern in _xss_patterns:
        match = pattern.search(text)
        if match:
            return DetectionResult(
                detected=True,
                pattern_type='xss',
                matched_pattern=match.group(0)
            )
    return DetectionResult(detected=False, pattern_type=None, matched_pattern=None)


def detect_path_traversal(text: str) -> DetectionResult:
    """Detect path traversal patterns in text.

    Args:
        text: Text to scan (URL, path, etc.)

    Returns:
        DetectionResult with detection status and matched pattern.
    """
    for pattern in _path_patterns:
        match = pattern.search(text)
        if match:
            return DetectionResult(
                detected=True,
                pattern_type='path_traversal',
                matched_pattern=match.group(0)
            )
    return DetectionResult(detected=False, pattern_type=None, matched_pattern=None)


def detect_all(text: str) -> DetectionResult:
    """Detect all attack patterns in text.

    Args:
        text: Text to scan.

    Returns:
        First DetectionResult found, or negative result.
    """
    # Check SQL injection
    result = detect_sql_injection(text)
    if result.detected:
        return result

    # Check XSS
    result = detect_xss(text)
    if result.detected:
        return result

    # Check path traversal
    result = detect_path_traversal(text)
    if result.detected:
        return result

    return DetectionResult(detected=False, pattern_type=None, matched_pattern=None)


def scan_request(request) -> DetectionResult:
    """Scan a Django request for attack patterns.

    Args:
        request: Django HttpRequest object.

    Returns:
        DetectionResult if attack detected, otherwise negative result.
    """
    # Scan URL path
    result = detect_all(request.path)
    if result.detected:
        return result

    # Scan query string
    query_string = request.META.get('QUERY_STRING', '')
    if query_string:
        result = detect_all(query_string)
        if result.detected:
            return result

    # Scan request body (for POST/PUT/PATCH)
    if request.method in ('POST', 'PUT', 'PATCH'):
        try:
            body = request.body.decode('utf-8', errors='ignore')
            if body:
                result = detect_all(body)
                if result.detected:
                    return result
        except Exception:
            pass

    return DetectionResult(detected=False, pattern_type=None, matched_pattern=None)


# Data leak patterns for response scanning

# Social Security Number patterns (US)
SSN_PATTERNS = [
    # Standard format: 123-45-6789
    r"(?<!\d)(\d{3})-(\d{2})-(\d{4})(?!\d)",
    # No dashes: 123456789
    r"(?<!\d)(\d{9})(?!\d)",
    # With spaces: 123 45 6789
    r"(?<!\d)(\d{3})\s(\d{2})\s(\d{4})(?!\d)",
]

# Credit Card patterns
CREDIT_CARD_PATTERNS = [
    # Visa: starts with 4, 13 or 16 digits
    r"(?<!\d)4[0-9]{12}(?:[0-9]{3})?(?!\d)",
    # MasterCard: starts with 51-55 or 2221-2720, 16 digits
    r"(?<!\d)(?:5[1-5][0-9]{14}|2(?:22[1-9]|2[3-9][0-9]|[3-6][0-9]{2}|7[01][0-9]|720)[0-9]{12})(?!\d)",
    # American Express: starts with 34 or 37, 15 digits
    r"(?<!\d)3[47][0-9]{13}(?!\d)",
    # Discover: starts with 6011, 622126-622925, 644-649, 65, 16 digits
    r"(?<!\d)6(?:011|5[0-9]{2})[0-9]{12}(?!\d)",
    # With dashes/spaces
    r"(?<!\d)4[0-9]{3}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}(?!\d)",
    r"(?<!\d)5[1-5][0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}(?!\d)",
    r"(?<!\d)3[47][0-9]{2}[-\s]?[0-9]{6}[-\s]?[0-9]{5}(?!\d)",
]

# API Key / Secret patterns (common formats)
API_KEY_PATTERNS = [
    # AWS Access Key
    r"(?:AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
    # AWS Secret Key
    r"(?:[A-Za-z0-9+/]{40})",
    # Generic API keys (long alphanumeric strings)
    r"(?:api[_-]?key|apikey|api[_-]?secret)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{20,})",
    # Bearer tokens
    r"(?:bearer\s+)([a-zA-Z0-9._-]{20,})",
]

# Email patterns (for mass exposure detection)
EMAIL_PATTERNS = [
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
]

# Compile patterns
_ssn_patterns = [re.compile(p, re.IGNORECASE) for p in SSN_PATTERNS]
_cc_patterns = [re.compile(p) for p in CREDIT_CARD_PATTERNS]
_api_patterns = [re.compile(p, re.IGNORECASE) for p in API_KEY_PATTERNS]
_email_patterns = [re.compile(p) for p in EMAIL_PATTERNS]


def _luhn_checksum(card_number: str) -> bool:
    """Validate credit card number using Luhn algorithm."""
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number.replace('-', '').replace(' ', ''))
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10 == 0


def _is_valid_ssn(ssn: str) -> bool:
    """Check if SSN is potentially valid (not obviously fake)."""
    digits = ssn.replace('-', '').replace(' ', '')
    if len(digits) != 9:
        return False
    # Check for obviously invalid SSNs
    if digits in ('000000000', '111111111', '123456789', '999999999'):
        return False
    # Area number (first 3 digits) can't be 000, 666, or 900-999
    area = int(digits[:3])
    if area == 0 or area == 666 or area >= 900:
        return False
    # Group number (middle 2 digits) can't be 00
    if int(digits[3:5]) == 0:
        return False
    # Serial number (last 4 digits) can't be 0000
    if int(digits[5:]) == 0:
        return False
    return True


def detect_ssn(text: str) -> DetectionResult:
    """Detect Social Security Numbers in text.

    Args:
        text: Text to scan (typically response body).

    Returns:
        DetectionResult if SSN detected.
    """
    for pattern in _ssn_patterns:
        matches = pattern.findall(text)
        for match in matches:
            if isinstance(match, tuple):
                ssn = ''.join(match)
            else:
                ssn = match
            if _is_valid_ssn(ssn):
                # Mask the SSN in the result
                masked = 'XXX-XX-' + ssn[-4:]
                return DetectionResult(
                    detected=True,
                    pattern_type='ssn_leak',
                    matched_pattern=masked,
                    is_outbound=True
                )
    return DetectionResult(detected=False, pattern_type=None, matched_pattern=None, is_outbound=True)


def detect_credit_card(text: str) -> DetectionResult:
    """Detect credit card numbers in text.

    Args:
        text: Text to scan (typically response body).

    Returns:
        DetectionResult if credit card detected.
    """
    for pattern in _cc_patterns:
        matches = pattern.findall(text)
        for match in matches:
            # Clean the number
            clean = match.replace('-', '').replace(' ', '')
            # Validate with Luhn
            if _luhn_checksum(clean):
                # Mask the card number
                masked = 'XXXX-XXXX-XXXX-' + clean[-4:]
                return DetectionResult(
                    detected=True,
                    pattern_type='cc_leak',
                    matched_pattern=masked,
                    is_outbound=True
                )
    return DetectionResult(detected=False, pattern_type=None, matched_pattern=None, is_outbound=True)


def detect_api_keys(text: str) -> DetectionResult:
    """Detect API keys and secrets in text.

    Args:
        text: Text to scan.

    Returns:
        DetectionResult if API key detected.
    """
    for pattern in _api_patterns:
        match = pattern.search(text)
        if match:
            # Mask the key
            key = match.group(1) if match.lastindex else match.group(0)
            masked = key[:8] + '...' + key[-4:] if len(key) > 12 else key[:4] + '...'
            return DetectionResult(
                detected=True,
                pattern_type='api_key_leak',
                matched_pattern=masked,
                is_outbound=True
            )
    return DetectionResult(detected=False, pattern_type=None, matched_pattern=None, is_outbound=True)


def detect_mass_email_exposure(text: str, threshold: int = 5) -> DetectionResult:
    """Detect mass email exposure in responses.

    Args:
        text: Text to scan.
        threshold: Minimum number of emails to trigger detection.

    Returns:
        DetectionResult if too many emails detected.
    """
    emails = _email_patterns[0].findall(text)
    unique_emails = set(emails)
    if len(unique_emails) >= threshold:
        return DetectionResult(
            detected=True,
            pattern_type='email_exposure',
            matched_pattern=f'{len(unique_emails)} emails found',
            is_outbound=True
        )
    return DetectionResult(detected=False, pattern_type=None, matched_pattern=None, is_outbound=True)


def scan_response(content: str) -> DetectionResult:
    """Scan response content for data leaks.

    Args:
        content: Response body content.

    Returns:
        DetectionResult if data leak detected.
    """
    # Check for SSN
    result = detect_ssn(content)
    if result.detected:
        return result

    # Check for credit cards
    result = detect_credit_card(content)
    if result.detected:
        return result

    # Check for API keys
    result = detect_api_keys(content)
    if result.detected:
        return result

    # Check for mass email exposure
    result = detect_mass_email_exposure(content)
    if result.detected:
        return result

    return DetectionResult(detected=False, pattern_type=None, matched_pattern=None, is_outbound=True)
