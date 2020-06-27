from datetime import datetime


def datetime_from_timestamp(ts):
    """Generate a datetime object from a timestamp"""
    if isinstance(ts, float):
        return datetime.fromtimestamp(ts / 1e3)
    return datetime.fromtimestamp(ts)


def utcnow() -> datetime:
    """Returns the current time (UTC)"""
    return datetime.utcnow()
