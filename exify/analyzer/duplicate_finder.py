from typing import Optional

from loguru import logger

from exify.adapter.image_hash_adapter import ImageHashAdapter
from exify.analyzer._base import BaseAnalyzer
from exify.models import FileItem


class DuplicateFinder(BaseAnalyzer):
    def __init__(self, item: FileItem, *, settings=None, adapter: Optional[ImageHashAdapter] = None):
        super().__init__(item, settings=settings, adapter=adapter)
        self._adapter = adapter or ImageHashAdapter(file_name=self._item.file)

