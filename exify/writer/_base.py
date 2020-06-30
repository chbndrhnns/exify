from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Optional

from exify.models import FileItem
from exify.settings import get_settings


class BaseWriter(metaclass=ABCMeta):

    def __init__(self, item: FileItem, *, settings=None, adapter: Optional = None):
        self._item: FileItem = item
        self._settings = settings or get_settings()
        self._generated_timestamp: Optional[datetime] = None

    @property
    def item(self):
        return self._item

    @property
    def generated_timestamp(self):
        if self._generated_timestamp:
            return self._generated_timestamp
        else:
            raise ValueError('Call generate_timestamp() first')

    @abstractmethod
    async def write(self):
        pass

    @abstractmethod
    async def generate_timestamp(self):
        pass
