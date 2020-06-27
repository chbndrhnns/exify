from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pydantic import BaseModel

from exify.__main__ import WhatsappFileAnalyzer
from exify.models import TimestampData, ExifTimestampAttribute
from exify.utils import datetime_from_timestamp, utcnow

EXAMPLES_DIR = Path('data')


class Examples(BaseModel):
    no_exif: Path = EXAMPLES_DIR / 'IMG-20140430-WA0004.jpg'


@pytest.fixture
def examples():
    return Examples()


@pytest.mark.asyncio
class TestAnalyze:
    async def test_no_exif_found(self, examples):
        # arrange
        analyzer = WhatsappFileAnalyzer(examples.no_exif)

        # act
        result = await analyzer.analyze_timestamp()

        # assert
        assert not result.exif


@pytest.mark.asyncio
class TestCheckDeviations:
    @pytest.fixture
    def acceptable_deviations(self):
        return TimestampData(
            file=Path('some-file.jpg'),
            file_name=utcnow(),
            file_created=utcnow(),
            file_modified=utcnow(),
            exif={
                ExifTimestampAttribute.datetime: utcnow()
            }
        )

    @pytest.fixture
    def too_much_deviations(self):
        return TimestampData(
            file=Path('some-file.jpg'),
            file_name=utcnow() + timedelta(minutes=1),
            file_created=utcnow(),
            file_modified=utcnow(),
            exif={
                ExifTimestampAttribute.datetime: utcnow()
            }
        )

    async def test_deviation_ok(self, acceptable_deviations):
        # arrange
        analyzer = WhatsappFileAnalyzer(Path())
        analyzer._timestamp_data = acceptable_deviations

        # act
        assert await analyzer.deviation_is_ok()

    async def test_deviation_not_ok(self, too_much_deviations):
        # arrange
        analyzer = WhatsappFileAnalyzer(Path())
        analyzer._timestamp_data = too_much_deviations

        # act
        assert not await analyzer.deviation_is_ok(max_deviation=timedelta(seconds=2))
