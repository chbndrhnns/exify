from datetime import timedelta
from pathlib import Path

import pytest
from loguru import logger

from exify.__main__ import expand_to_absolute_path
from exify.writer.whatsapp_exif_writer import WhatsappExifWriter
from exify.constants import DEFAULT_EXIF_TIMESTAMP_ATTRIBUTE
from exify.analyzer.whatsapp_analyzer import WhatsappFileAnalyzer
from exify.models import FileItem, ExifTimestampAttribute, Timestamps, AnalysisResults
from exify.utils import utcnow
from tests import assertions
from tests.assertions import generated_timestamp_matches_file_name_timestamp
from tests.integration.conftest import WhatsappExamples


@pytest.mark.asyncio
class TestAnalyze:
    async def test_no_exif_found(self, examples):
        # arrange
        item = FileItem(
            file=expand_to_absolute_path(examples.no_exif)
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
            results=AnalysisResults()
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


@pytest.mark.asyncio
class TestGenerateExifData:
    @pytest.fixture
    def test_file(self):
        return expand_to_absolute_path(WhatsappExamples().no_exif)

    @pytest.fixture
    def test_path(self, tmp_path):
        logger.info(f'Creating temporary directory: {tmp_path}')
        yield tmp_path
        logger.info(f'Deleting temporary directory: {tmp_path}')

    @pytest.fixture(autouse=True)
    def duplicate_test_file(self, test_path, test_file):
        dest = test_path / test_file.name
        logger.info(f'Creating test file: {dest}')
        dest.write_bytes(test_file.read_bytes())

    @pytest.fixture
    def item(self, test_path, test_file):
        return FileItem(
            file=test_path / test_file.name
        )

    @pytest.fixture
    async def analyzer(self, item) -> WhatsappFileAnalyzer:
        analyzer = WhatsappFileAnalyzer(item)
        await analyzer.analyze_timestamp()
        return analyzer

    async def test_generate_exif_data(self, analyzer: WhatsappFileAnalyzer):
        # arrange
        writer = WhatsappExifWriter(analyzer._item)
        assert not writer._item.timestamps.exif

        # act
        await writer.generate_timestamp()

        # assert
        await assertions.generated_timestamp_matches_file_name_timestamp(analyzer, writer)

    async def test_write_exif_data(self, analyzer: WhatsappFileAnalyzer):
        # arrange
        writer = WhatsappExifWriter(analyzer._item, adapter=analyzer._adapter)

        # act
        await writer.write()

        # assert
        await assertions.file_timestamp_matches_generated_timestamp(analyzer, writer)
