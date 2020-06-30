from datetime import datetime, date
from typing import Optional

from loguru import logger

from exify.settings import get_settings
from exify.constants import EXIF_TIMESTAMP_FORMAT, DEFAULT_EXIF_TIMESTAMP_ATTRIBUTE
from exify.adapter.piexif_adapter import PiexifAdapter
from exify.models import FileItem, ExifTimestampAttribute


class WhatsappTimestampWriter:

    def __init__(self, item: FileItem, *, settings=None, adapter: Optional[PiexifAdapter] = None):
        self._item: FileItem = item
        self._settings = settings or get_settings()
        self._adapter = adapter or PiexifAdapter(file_name=self._item.file)

    async def write_exif_data(self):
        logger.info(f'{self._item.file}: Updating EXIF data...')
        if not any([self._item.timestamps.exif.values()]):
            await self.generate_exif_timestamp()

        updated = {
            DEFAULT_EXIF_TIMESTAMP_ATTRIBUTE.value:
                _format_datetime_for_exif(self._item.timestamps.exif[DEFAULT_EXIF_TIMESTAMP_ATTRIBUTE])
        }

        await self._adapter.update_exif_data(updated)

    async def generate_exif_timestamp(self) -> None:
        ts = self._item.timestamps.file_name
        ts = ts.replace(hour=10, minute=30)
        self._item.timestamps.exif[DEFAULT_EXIF_TIMESTAMP_ATTRIBUTE] = ts
        logger.debug(f'Setting {ExifTimestampAttribute.datetime} to "{ts}"')


def _format_datetime_for_exif(timestamp: datetime) -> str:
    return datetime.strftime(timestamp, EXIF_TIMESTAMP_FORMAT)
