from pathlib import Path

import pytest
from pydantic import BaseModel

from exify.__main__ import WhatsappFileAnalyzer

EXAMPLES_DIR = Path('data')


class Examples(BaseModel):
    no_exif: Path = EXAMPLES_DIR / 'IMG-20140430-WA0004.jpg'


@pytest.fixture
def examples():
    return Examples()


@pytest.mark.asyncio
class TestAnalyzer:
    async def test_no_exif_found(self, examples):
        # arrange
        analyzer = WhatsappFileAnalyzer(examples.no_exif)

        # act
        result = await analyzer.analyze_timestamp()

        # assert
        assert not result.exif_created
