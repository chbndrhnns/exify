from pathlib import Path

import aiofiles
from exif import Image


class ExifAdapter:
    def __init__(self):
        ...

    @staticmethod
    async def get_exif_data(filename: Path) -> Image:
        async with aiofiles.open(filename, mode='rb') as f:
            return Image(await f.read())
