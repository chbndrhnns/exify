from datetime import timedelta
from pathlib import Path

import pytest

from exify.__main__ import expand_to_absolute_path
from exify.analyzer.timestamp_analyzer import TimestampAnalyzer
from exify.models import FileItem, ExifTimestampAttribute, Timestamps, AnalysisResults
from exify.utils import utcnow


@pytest.mark.asyncio
class TestAnalyze:
    async def test_no_exif_found(self, examples):
        # arrange
        item = FileItem(
            file=expand_to_absolute_path(examples.no_exif)
        )
        analyzer = TimestampAnalyzer(item)

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
            results=AnalysisResults()
        )

    async def test_deviation_ok(self, acceptable_deviations):
        # arrange
        analyzer = TimestampAnalyzer(acceptable_deviations)

        # act
        assert analyzer.deviation_is_ok()

    async def test_deviation_not_ok(self, too_much_deviations):
        # arrange
        analyzer = TimestampAnalyzer(too_much_deviations)

        # act
        assert not analyzer.deviation_is_ok(max_deviation=timedelta(seconds=2))


