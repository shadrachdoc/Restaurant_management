"""
Customer Identification Utility
Logic for identifying and matching customers across orders for preference tracking
"""
import re
from typing import Optional
from uuid import UUID
from ..models import Order
from shared.utils.logger import setup_logger

logger = setup_logger("customer-identification")


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number by removing all non-digit characters

    Args:
        phone: Raw phone number string

    Returns:
        Normalized phone number with only digits
    """
    return re.sub(r'\D', '', phone)


def normalize_email(email: str) -> str:
    """
    Normalize email address

    Args:
        email: Raw email address

    Returns:
        Lowercase, trimmed email address
    """
    return email.lower().strip()


def identify_customer(order: Order) -> Optional[str]:
    """
    Identify customer across orders for preference tracking.
    Returns a unique customer identifier that can be used to track preferences.

    Priority order:
    1. Registered customer (has customer_id) - most reliable
    2. Guest with email - reliable for online orders
    3. Guest with phone only - less reliable but still usable
    4. No identifier - cannot track preferences

    Args:
        order: Order model instance

    Returns:
        Customer identifier string or None if cannot identify
        Format:
        - "customer:{uuid}" for registered customers
        - "email:{normalized_email}" for guests with email
        - "phone:{normalized_phone}" for guests with phone only
    """
    # 1. Registered customer (has customer_id) - MOST RELIABLE
    if order.customer_id:
        return f"customer:{str(order.customer_id)}"

    # 2. Guest with email - RELIABLE
    # Email is more stable than phone for guest tracking
    if order.customer_email:
        normalized = normalize_email(order.customer_email)
        if normalized:  # Ensure it's not empty after normalization
            return f"email:{normalized}"

    # 3. Guest with phone only - LESS RELIABLE
    # Phone numbers can change, but still useful for tracking
    if order.customer_phone:
        normalized = normalize_phone(order.customer_phone)
        if normalized:  # Ensure it's not empty after normalization
            return f"phone:{normalized}"

    # 4. No identifier - CANNOT TRACK
    # This might be walk-in customers who don't provide any info
    logger.warning(f"Order {order.id} has no customer identifier for preference tracking")
    return None


def extract_identifier_type(identifier: str) -> tuple[str, str]:
    """
    Extract the type and value from a customer identifier

    Args:
        identifier: Customer identifier string (e.g., "customer:uuid", "email:test@example.com")

    Returns:
        Tuple of (type, value) where type is 'customer', 'email', or 'phone'

    Examples:
        >>> extract_identifier_type("customer:123e4567-e89b-12d3-a456-426614174000")
        ('customer', '123e4567-e89b-12d3-a456-426614174000')

        >>> extract_identifier_type("email:john@example.com")
        ('email', 'john@example.com')

        >>> extract_identifier_type("phone:1234567890")
        ('phone', '1234567890')
    """
    parts = identifier.split(':', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    else:
        # Fallback for invalid format
        logger.warning(f"Invalid identifier format: {identifier}")
        return 'unknown', identifier


def can_merge_identifiers(identifier1: str, identifier2: str) -> bool:
    """
    Determine if two customer identifiers represent the same customer.
    This is useful when a guest user later registers an account.

    Merge scenarios:
    1. Same email (email:X and email:X) - YES
    2. Same customer_id (customer:X and customer:X) - YES
    3. Customer ID matches email (customer:X and email:Y where user X has email Y) - REQUIRES DB LOOKUP
    4. Phone matches email - MAYBE (requires confirmation)
    5. Different types with no overlap - NO

    Args:
        identifier1: First customer identifier
        identifier2: Second customer identifier

    Returns:
        True if identifiers can be merged, False otherwise

    Note:
        This is a simple string comparison. For advanced merging
        (e.g., customer:X and email:Y), you'll need to query the database.
    """
    type1, value1 = extract_identifier_type(identifier1)
    type2, value2 = extract_identifier_type(identifier2)

    # Same type and value - definitely the same customer
    if type1 == type2 and value1 == value2:
        return True

    # Different types - cannot determine without DB lookup
    # In a production system, you might want to:
    # 1. Check if customer_id has the email in user database
    # 2. Check if phone belongs to customer with email
    # For now, we'll be conservative and return False
    return False


def get_customer_query_conditions(identifier: str) -> dict:
    """
    Generate query conditions for finding customer preferences

    Args:
        identifier: Customer identifier string

    Returns:
        Dictionary with query conditions for SQLAlchemy

    Example:
        >>> get_customer_query_conditions("email:john@example.com")
        {'customer_identifier': 'email:john@example.com'}
    """
    return {
        'customer_identifier': identifier
    }


def is_registered_customer(identifier: str) -> bool:
    """
    Check if identifier represents a registered customer

    Args:
        identifier: Customer identifier string

    Returns:
        True if customer is registered (has customer_id), False otherwise
    """
    return identifier.startswith('customer:')


def is_guest_customer(identifier: str) -> bool:
    """
    Check if identifier represents a guest customer

    Args:
        identifier: Customer identifier string

    Returns:
        True if customer is guest (email or phone), False otherwise
    """
    return identifier.startswith('email:') or identifier.startswith('phone:')


def format_customer_display_name(identifier: str) -> str:
    """
    Format customer identifier for display purposes

    Args:
        identifier: Customer identifier string

    Returns:
        Human-readable display name

    Examples:
        >>> format_customer_display_name("customer:123e4567-e89b-12d3-a456-426614174000")
        'Registered Customer'

        >>> format_customer_display_name("email:john@example.com")
        'john@example.com'

        >>> format_customer_display_name("phone:1234567890")
        '***-***-7890'
    """
    id_type, value = extract_identifier_type(identifier)

    if id_type == 'customer':
        return 'Registered Customer'
    elif id_type == 'email':
        return value
    elif id_type == 'phone':
        # Mask phone number for privacy (show last 4 digits)
        if len(value) >= 4:
            return f"***-***-{value[-4:]}"
        return '***-***-****'
    else:
        return 'Unknown Customer'
