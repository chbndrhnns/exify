from pathlib import Path

import pytest
from pydantic.main import BaseModel

from exify.__main__ import expand_to_absolute_path
from exify.analyzer.duplicate_finder import DuplicateFinder
from exify.models import FileItem
from tests.integration.conftest import WHATSAPP_DIR, EXAMPLES_DIR

DUPLICATES_DIR = EXAMPLES_DIR / 'duplicates'


class NoDuplicatesExample(BaseModel):
    first: Path = WHATSAPP_DIR / 'IMG-20140430-WA0004.jpg'
    second: Path = WHATSAPP_DIR / 'IMG-20140510-WA0000.jpg'


class DuplicatesExample(BaseModel):
    first: Path = DUPLICATES_DIR / 'set1' / 'IMG-20140831-WA0001.jpg'
    second: Path = DUPLICATES_DIR / 'set1' / 'IMG-20140831-WA0002.jpg'
    third: Path = DUPLICATES_DIR / 'set1' / 'IMG-20140901-WA0000.jpg'


@pytest.mark.asyncio
class TestDuplicateFinder:
    async def test_no_duplicates(self, examples):
        # arrange
        items = [
            FileItem(
                file=expand_to_absolute_path(NoDuplicatesExample().first)
            ),
            FileItem(
                file=expand_to_absolute_path(NoDuplicatesExample().second)
            )
        ]

        finder = DuplicateFinder(items=items)

        # act
        await finder.run()

        # assert
        assert len(finder._images_by_hash) == len(items)

    async def test_duplicates(self):
        # arrange
        items = [
            FileItem(
                file=expand_to_absolute_path(DuplicatesExample().first)
            ),
            FileItem(
                file=expand_to_absolute_path(DuplicatesExample().second)
            ),
            FileItem(
                file=expand_to_absolute_path(DuplicatesExample().third)
            )

        ]
        finder = DuplicateFinder(items=items)

        # act
        await finder.run()

        # assert
        assert len(finder._images_by_hash) == 1

    async def test_no_files(self):
        # arrange
        items = []
        finder = DuplicateFinder(items=items)

        # act
        await finder.run()

        # assert
        assert not finder._images_by_hash

    async def test_mixture_of_files(self):
        # arrange
        items = [
            FileItem(
                file=expand_to_absolute_path(DuplicatesExample().first)
            ),
            FileItem(
                file=expand_to_absolute_path(DuplicatesExample().second)
            ),
            FileItem(
                file=expand_to_absolute_path(NoDuplicatesExample().first)
            ),
        ]
        finder = DuplicateFinder(items=items)

        # act
        await finder.run()

        # assert
        assert len(finder._images_by_hash) == 2
