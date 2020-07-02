import asyncio
from abc import ABCMeta
from typing import Optional, List, Type

from exify.models import FileItem
from exify.settings import get_settings


class SingleFileAnalyzer(metaclass=ABCMeta):

    def __init__(self, item: FileItem, *, settings=None, tasks=None):
        self._settings = settings or get_settings()
        self._tasks = tasks or []

        if not isinstance(item, FileItem):
            raise ValueError('item must be of type FileItem')
        self._item: FileItem = item

    @classmethod
    async def create(
            cls,
            item: FileItem,
            *,
            settings=None,
            tasks: List = None,
    ):
        return cls(item=item, settings=settings, tasks=tasks)

    @property
    def item(self) -> FileItem:
        return self._item

    async def run(self) -> None:
        await asyncio.gather(*[await t() for t in self._tasks])


class MultipleFilesAnalyzer(metaclass=ABCMeta):

    def __init__(self, items: List[FileItem], *, settings=None, adapter: Optional[Type] = None):
        self._settings = settings or get_settings()

        if items and not isinstance(items[0], FileItem):
            raise ValueError('item must be of type FileItem')
        self._items: List[FileItem] = items

    @property
    def items(self) -> List[FileItem]:
        return self._items
