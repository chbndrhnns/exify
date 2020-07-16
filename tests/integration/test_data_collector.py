import pytest

from exify.analyzer.data_collector import DataCollector
from exify.models import FileMetadata
from exify.settings import get_settings


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
