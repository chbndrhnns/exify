from typing import Type

from loguru import logger

from exify.adapter.image_hash_adapter import ImageHashAdapter
from exify.analyzer._base import MultipleFilesAnalyzer


class DuplicateFinder(MultipleFilesAnalyzer):
    def __init__(self, items, *, settings=None, adapter: Type[ImageHashAdapter] = ImageHashAdapter):
        super().__init__(items, settings=settings, adapter=adapter)
        self._adapter = adapter

        self._duplicates = {}
        self._images_by_hash = {}

    async def run(self):
        """Run the search for duplicates"""

        for img in sorted([item.file for item in self.items]):
            hash = await self._adapter(file_name=img).calculate_hash()

            if hash in self._images_by_hash:
                logger.info(f'{img} already exists as {self._images_by_hash[hash]}')
            self._images_by_hash[hash] = self._images_by_hash.get(hash, []) + [img]
