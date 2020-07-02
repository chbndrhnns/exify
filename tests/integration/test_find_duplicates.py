from pathlib import Path

import pytest
from pydantic.main import BaseModel

from exify.__main__ import expand_to_absolute_path
from exify.analyzer.timestamp_analyzer import TimestampAnalyzer
from exify.models import FileItem
from tests.integration.conftest import WHATSAPP_DIR


class NoDuplicatesExample(BaseModel):
    first: Path = WHATSAPP_DIR / 'IMG-20140430-WA0004.jpg'
    second: Path = WHATSAPP_DIR / 'IMG-20140510-WA0000.jpg'


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
        analyzers = [
            TimestampAnalyzer(item).analyze_timestamp()
            for item in items
        ]

        # act


        # a
