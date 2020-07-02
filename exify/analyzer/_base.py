from abc import ABCMeta
from typing import Optional, List

from exify.models import FileItem
from exify.settings import get_settings


class SingleFileAnalyzer(metaclass=ABCMeta):

    def __init__(self, item: FileItem, *, settings=None, adapter: Optional[str] = None):
        self._settings = settings or get_settings()

        if not isinstance(item, FileItem):
            raise ValueError('item must be of type FileItem')
        self._item: FileItem = item

    @property
    def item(self) -> FileItem:
        return self._item


class MultipleFilesAnalyzer(metaclass=ABCMeta):

    def __init__(self, items: List[FileItem], *, settings=None, adapter: Optional[str] = None):
        self._settings = settings or get_settings()

        if items and not isinstance(items[0], FileItem):
            raise ValueError('item must be of type FileItem')
        self._items: List[FileItem] = items

    @property
    def items(self) -> List[FileItem]:
        return self._items
