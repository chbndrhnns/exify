from pathlib import Path
from typing import Optional

import aiofiles
from exif import Image

from exify.adapter._base import BaseAdapter


class ExifAdapter(BaseAdapter):
    def __init__(self, file_name: Path):
        super().__init__(file_name)
        self._image: Optional[Image] = None

    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, val):
        self._file_name = val

    async def read_image(self) -> Image:
        if not self.file_name:
            raise ValueError('filename needs to be set first')

        if not self._image:
            async with aiofiles.open(self.file_name, mode='rb') as f:
                self._image = Image(await f.read())
        return self._image

    async def get_exif_data(self):
        image = await self.read_image()
        if image.has_exif:
            return self._image

    async def update_exif_data(self, data):
        for attr, val in data.items():
            setattr(self.image, attr, val)

    async def write_file(self) -> None:
        if self.image:
            async with aiofiles.open(self.file_name, mode='wb') as f:
                await f.write(self.image)

        raise ValueError('No image available for writing')
