from datetime import datetime

from loguru import logger

from exify.constants import EXIF_TIMESTAMP_FORMAT
from exify.models import FileItem


def create_timestamp_from_exif_attribute(item: FileItem) -> datetime:
    ts = item.timestamps.file_name
    ts = ts.replace(hour=10, minute=30)
    return ts


def _format_datetime_for_exif(timestamp: datetime) -> str:
    return datetime.strftime(timestamp, EXIF_TIMESTAMP_FORMAT)
