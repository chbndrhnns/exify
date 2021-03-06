import pytest
from loguru import logger

from exify.__main__ import expand_to_absolute_path
from exify.analyzer.image_analyzer import WhatsappImageAnalyzer
from exify.models import FileItem
from exify.writer.file_metadata_writer import FileTimestampWriter
from tests import assertions
from tests.integration.conftest import WhatsappExamples


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
    async def analyzer(self, item):
        analyzer = await WhatsappImageAnalyzer.create(item)
        await analyzer.get_timestamp()
        return analyzer

    async def test_generate_exif_data(self, analyzer: WhatsappImageAnalyzer):
        # arrange
        writer = FileTimestampWriter(analyzer.item)
        assert not writer._item.timestamps.exif

        # act
        await writer.generate_timestamp()

        # assert
        await assertions.generated_timestamp_matches_file_name_timestamp(analyzer, writer)

    async def test_write_file_date(self, analyzer: WhatsappImageAnalyzer):
        # arrange
        writer = FileTimestampWriter(analyzer._item, adapter=analyzer._adapter)

        # act
        await writer.write()

        # assert
        await assertions.file_timestamp_matches_generated_timestamp(analyzer, writer)

