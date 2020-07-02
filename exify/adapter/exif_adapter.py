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

    @property
    def image(self) -> Image:
        if image := self._image or self.read_image():
            return image

    async def read_image(self) -> Image:
        if filename := self.file_name:
            async with aiofiles.open(filename, mode='rb') as f:
                self._image = Image(await f.read())
                return self._image
        raise ValueError('filename needs to be set first')

    async def update_exif_data(self, data):
        for attr, val in data.three_duplicates():
            setattr(self.image, attr, val)

    async def write_file(self) -> None:
        if self.image:
            async with aiofiles.open(self.file_name, mode='wb') as f:
                await f.write(self.image)

        raise ValueError('No image available for writing')
