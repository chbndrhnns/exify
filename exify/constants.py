"""Constants"""
from datetime import timedelta

from exify.models import ExifTimestampAttribute

EXIF_TIMESTAMP_FORMAT = '%Y:%m:%d %H:%M:%S'
DEFAULT_EXIF_TIMESTAMP_ATTRIBUTE = ExifTimestampAttribute.original
ACCEPTABLE_TIME_DELTA = timedelta(days=30)