import os
import time
from typing import Optional

from loguru import logger

from exify.models import FileItem, WindowsFileAttribute
from exify.writer._base import BaseWriter
from exify.writer.utils import create_timestamp_from_exif_attribute

try:
    import win32file, win32con

except ImportError:
    pass


class FileTimestampWriter(BaseWriter):
    def __init__(self, item: FileItem, *, settings=None, adapter: Optional = None):
        super().__init__(item, settings=settings, adapter=adapter)

    async def generate_timestamp(self):
        self._generated_timestamp = create_timestamp_from_exif_attribute(self._item)
        self.item.timestamps.file_modified = self.generated_timestamp
        logger.debug(f'Using timestamp: "{self.generated_timestamp}"')

    async def write(self):
        await self.generate_timestamp()
        logger.debug(f'{self._item.file}: Updating file metadata...')
        self._set_metadata()

    def _set_metadata(self):
        ts = self.item.timestamps.file_modified

        raw_ts = time.mktime(ts.utctimetuple())
        logger.debug(f'Setting file timestamp to "{raw_ts}"')

        if self._settings.file_attribute == WindowsFileAttribute:
            handle = win32file.CreateFile(
                self.item.file,
                win32file.GENERIC_WRITE,
                0,
                None,
                win32con.OPEN_EXISTING,
                0,
                None
            )
            win32file.SetFileTime(handle, *(ts,) * 3)
            handle.close()
        else:
            os.utime(
                self.item.file,
                (raw_ts,) * 2
            )
