"""
Helper utility functions.
"""

import re
import uuid
import html
from typing import Optional


def generate_session_id(prefix: str = "sess") -> str:
    """Generate a unique session ID."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def format_currency(amount: float, currency: str = "INR") -> str:
    """Format amount as currency string."""
    if currency == "INR":
        return f"₹{amount:,.2f}"
    elif currency == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f} {currency}"


def sanitize_input(text: str, max_length: int = 4000) -> str:
    """
    Sanitize user input.
    
    - Strips whitespace
    - Escapes HTML
    - Truncates to max length
    """
    if not text:
        return ""
    
    # Strip and escape
    text = text.strip()
    text = html.escape(text)
    
    # Truncate
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def extract_order_id(message: str) -> Optional[str]:
    """
    Extract order ID from a message.
    
    Supports formats:
    - ORD-2024-001234
    - ORD2024001234
    - Order #123456
    - #123456
    """
    if not message:
        return None
    
    patterns = [
        r'(ORD[-_]?\d{4}[-_]?\d{4,})',  # ORD-2024-001234
        r'order\s*#?\s*(\d{6,})',        # Order #123456
        r'#(\d{6,})',                     # #123456
        r'(\d{10,})'                      # Plain number (10+ digits)
    ]
    
    message_upper = message.upper()
    
    for pattern in patterns:
        match = re.search(pattern, message_upper, re.IGNORECASE)
        if match:
            order_id = match.group(1) if match.lastindex else match.group(0)
            # Normalize format
            if not order_id.startswith('ORD'):
                order_id = f"ORD-{order_id}"
            return order_id.replace('_', '-')
    
    return None


def calculate_response_time(start_time, end_time) -> float:
    """Calculate response time in seconds."""
    if not start_time or not end_time:
        return 0.0
    return (end_time - start_time).total_seconds()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length with suffix."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def is_valid_phone(phone: str) -> bool:
    """Validate phone number format."""
    if not phone:
        return False
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    # Check if it's numeric and reasonable length
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15


def mask_phone(phone: str) -> str:
    """Mask phone number for privacy."""
    if not phone or len(phone) < 6:
        return phone
    return phone[:3] + '*' * (len(phone) - 6) + phone[-3:]


def mask_email(email: str) -> str:
    """Mask email for privacy."""
    if not email or '@' not in email:
        return email
    
    local, domain = email.rsplit('@', 1)
    if len(local) <= 2:
        masked_local = '*' * len(local)
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"
