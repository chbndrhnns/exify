import re

import pytest

from exify.analyzer.file_finder import find_files
from exify.settings import get_settings


@pytest.fixture
def start_dir():
    return get_settings().base_dir


@pytest.mark.asyncio
class TestFindFiles:
    async def test_returns_whatsapp_files(self, start_dir):
        whatsapp_pattern = re.compile(r'IMG-\d{8}-WA(.*)')

        results = await find_files(start_dir, pattern=whatsapp_pattern)
        assert results

    async def test_returns_images_without_pattern(self, start_dir):
        results = await find_files(start_dir=start_dir)
        assert all([item for item in results if item.suffix in ('.jpg', '.jpeg')]), 'Return files without jpg extension'
