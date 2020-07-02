from abc import ABCMeta
from typing import Optional

from exify.models import FileItem
from exify.settings import get_settings


class BaseAnalyzer(metaclass=ABCMeta):

    def __init__(self, item: FileItem, *, settings=None, adapter: Optional[str] = None):
        self._settings = settings or get_settings()

        if not isinstance(item, FileItem):
            raise ValueError('item must be of type FileItem')
        self._item: FileItem = item

    @property
    def item(self):
        return self._item
