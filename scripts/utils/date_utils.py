"""Date formatting and manipulation utilities."""

from datetime import datetime, timedelta
from dateutil import parser as date_parser


def format_time_ago(date_input):
    """
    Convert date to human-readable format like "2d ago", "1w ago", "3mo ago".

    Args:
        date_input: datetime object, string (ISO format), or None

    Returns:
        str: Human-readable time ago string
    """
    if date_input is None:
        return "Unknown"

    # Parse date if it's a string
    if isinstance(date_input, str):
        try:
            date_obj = date_parser.parse(date_input)
        except (ValueError, TypeError):
            return "Unknown"
    else:
        date_obj = date_input

    # Calculate time difference
    now = datetime.now(date_obj.tzinfo) if date_obj.tzinfo else datetime.now()
    delta = now - date_obj

    # Format based on time difference
    if delta.days == 0:
        hours = delta.seconds // 3600
        if hours == 0:
            minutes = delta.seconds // 60
            return f"{minutes}m ago" if minutes > 0 else "Just now"
        return f"{hours}h ago"
    elif delta.days == 1:
        return "1d ago"
    elif delta.days < 7:
        return f"{delta.days}d ago"
    elif delta.days < 30:
        weeks = delta.days // 7
        return f"{weeks}w ago"
    elif delta.days < 365:
        months = delta.days // 30
        return f"{months}mo ago"
    else:
        years = delta.days // 365
        return f"{years}y ago"


def get_date_n_months_ago(n):
    """
    Calculate date N months ago from now.

    Args:
        n: Number of months to go back

    Returns:
        datetime: Date N months ago
    """
    today = datetime.now()
    # Approximate: assume 30 days per month
    return today - timedelta(days=n * 30)


def calculate_age_days(created_date):
    """
    Calculate repository age in days from creation date.

    Args:
        created_date: datetime object or ISO string

    Returns:
        int: Age in days
    """
    if created_date is None:
        return 0

    # Parse date if it's a string
    if isinstance(created_date, str):
        try:
            created_obj = date_parser.parse(created_date)
        except (ValueError, TypeError):
            return 0
    else:
        created_obj = created_date

    # Calculate days between creation and now
    now = datetime.now(created_obj.tzinfo) if created_obj.tzinfo else datetime.now()
    delta = now - created_obj
    return delta.days


def parse_date(date_input):
    """
    Parse various date formats to datetime object.

    Args:
        date_input: String or datetime object

    Returns:
        datetime: Parsed datetime object or None if parsing fails
    """
    if date_input is None:
        return None

    if isinstance(date_input, datetime):
        return date_input

    try:
        return date_parser.parse(date_input)
    except (ValueError, TypeError):
        return None


def format_date_iso(date_obj):
    """
    Format datetime object to ISO string (YYYY-MM-DD).

    Args:
        date_obj: datetime object

    Returns:
        str: ISO formatted date string
    """
    if date_obj is None:
        return ""

    if isinstance(date_obj, str):
        date_obj = parse_date(date_obj)

    if date_obj:
        return date_obj.strftime("%Y-%m-%d")

    return ""
