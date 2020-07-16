import pytest

from exify.analyzer.data_collector import DataCollector
from exify.models import FileMetadata
from exify.settings import get_settings
from tests.integration.conftest import ScreenshotExamples


def assert_all_data_extracted(metadata: FileMetadata):
    expected = len(metadata.__fields__)
    assert len(metadata.__dict__.values()) == expected


@pytest.fixture
def settings():
    return get_settings()


@pytest.mark.asyncio
class TestDataCollector:

    async def test_collects_data(self, settings):
        c = DataCollector(settings=settings)

        await c.run()

        assert c.items
        first = list(c.items.values())[0]
        assert_all_data_extracted(first)

    async def test_screenshot_with_file_name_timestamp(self, settings):
        c = DataCollector(settings=settings)
        files = ScreenshotExamples().dict()['timestamp_in_filename']

        await c.run(files)

        assert len(c.items) == 2
        assert all([item.timestamp_name for item in c.items.values()])

    async def test_screenshot_with_modified_timestamp(self, settings):
        c = DataCollector(settings=settings)
        files = ScreenshotExamples().dict()['modified']

        await c.run(files)

        assert len(c.items) == 1
        assert all([item.timestamp_modified for item in c.items.values()])
