from typing import Optional

from loguru import logger

from exify.constants import DEFAULT_EXIF_TIMESTAMP_ATTRIBUTE
from exify.adapter.piexif_adapter import PiexifAdapter
from exify.models import FileItem
from exify.writer._base import BaseWriter
from exify.writer.utils import create_timestamp_from_exif_attribute, _format_datetime_for_exif


class ExifTimestampWriter(BaseWriter):

    def __init__(self, item: FileItem, *, settings=None, adapter: Optional[PiexifAdapter] = None):
        super().__init__(item, settings=settings, adapter=adapter)
        self._adapter = adapter or PiexifAdapter(file_name=self._item.file)

    async def write(self):
        logger.debug(f'{self._item.file}: Updating EXIF data...')
        if not any([self._item.timestamps.exif.values()]):
            await self.generate_timestamp()

        updated = {
            DEFAULT_EXIF_TIMESTAMP_ATTRIBUTE.value:
                _format_datetime_for_exif(self._item.timestamps.exif[DEFAULT_EXIF_TIMESTAMP_ATTRIBUTE])
        }

        await self._adapter.update_exif_data(updated)

    async def generate_timestamp(self) -> None:
        self._generated_timestamp = create_timestamp_from_exif_attribute(self._item)
        self.item.timestamps.exif[DEFAULT_EXIF_TIMESTAMP_ATTRIBUTE] = self.generated_timestamp
        logger.debug(f'Using timestamp: "{self.generated_timestamp}"')
