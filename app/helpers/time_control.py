from datetime import datetime, timezone


def utc_now():
    """
    Returns current time in UTC (timezone-aware).
    """
    return datetime.now(timezone.utc)


