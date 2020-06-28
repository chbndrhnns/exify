from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pydantic import BaseModel

from exify.__main__ import WhatsappFileAnalyzer, _expand_to_absolute_path
from exify.models import FileItem, ExifTimestampAttribute, Timestamps, AnalysisResults
from exify.utils import datetime_from_timestamp, utcnow

EXAMPLES_DIR = Path('data')


class Examples(BaseModel):
    no_exif: Path = EXAMPLES_DIR / 'IMG-20140430-WA0004.jpg'


class FakeItem(FileItem):
    file: Path = Path()


@pytest.fixture
def examples():
    return Examples()


@pytest.mark.asyncio
class TestAnalyze:
    async def test_no_exif_found(self, examples):
        # arrange
        item = FileItem(
            file=_expand_to_absolute_path(examples.no_exif)
        )
        analyzer = WhatsappFileAnalyzer(item)

        # act
        await analyzer.analyze_timestamp()

        # assert
        assert not analyzer._item.timestamps.exif


@pytest.mark.asyncio
class TestCheckDeviations:
    @pytest.fixture
    def acceptable_deviations(self):
        return FileItem(
            file=Path('some-file.jpg'),
            timestamps=Timestamps(
                file_name=utcnow(),
                file_created=utcnow(),
                file_modified=utcnow(),
                exif={
                    ExifTimestampAttribute.datetime: utcnow()
                }
            ),
            results=AnalysisResults()
        )

    @pytest.fixture
    def too_much_deviations(self):
        return FileItem(
            file=Path('some-file.jpg'),
            timestamps=Timestamps(
                file_name=utcnow() + timedelta(minutes=1),
                file_created=utcnow(),
                file_modified=utcnow(),
                exif={
                    ExifTimestampAttribute.datetime: utcnow()
                }),
        results = AnalysisResults()
        )

    async def test_deviation_ok(self, acceptable_deviations):
        # arrange
        analyzer = WhatsappFileAnalyzer(acceptable_deviations)

        # act
        assert analyzer.deviation_is_ok()

    async def test_deviation_not_ok(self, too_much_deviations):
        # arrange
        analyzer = WhatsappFileAnalyzer(too_much_deviations)

        # act
        assert not analyzer.deviation_is_ok(max_deviation=timedelta(seconds=2))
