import functools
from collections import Callable
from pathlib import Path

import aiofiles
import imagehash
from PIL import Image

from exify.adapter._base import BaseAdapter
from exify.utils import call_blocking


class ImageHashAdapter(BaseAdapter):
    def __init__(self, file_name: Path, hash_func: Callable = imagehash.phash):
        super().__init__(file_name)
        self._algorithm: Callable = hash_func

    async def calculate_hash(self):
        image = Image.open(self._file_name)
        return await call_blocking(functools.partial(self._algorithm, image))
