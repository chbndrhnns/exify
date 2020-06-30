import asyncio
from datetime import datetime


def datetime_from_timestamp(ts):
    """Generate a datetime object from a timestamp"""
    if isinstance(ts, float):
        return datetime.fromtimestamp(ts / 1e3)
    return datetime.fromtimestamp(ts)


def utcnow() -> datetime:
    """Returns the current time (UTC)"""
    return datetime.utcnow()


async def call_blocking(fn, *, loop=None):
    loop = loop or asyncio.get_event_loop()
    return await loop.run_in_executor(None, fn)
