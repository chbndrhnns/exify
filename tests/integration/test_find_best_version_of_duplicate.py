from pathlib import Path
from typing import List

import pytest

from exify.analyzer.image_analyzer import WhatsappImageAnalyzer
from exify.models import FileItem


def find_better_version(files: List[Path]):
    if not files:
        raise ValueError('No files given')

    sizes = {
        item.file: item.file.stat().st_size
        for item in files
    }
    sorted_desc = [
        file
        for (file, size) in sorted(sizes.items(), key=lambda x: x[1], reverse=True)
    ]
    return sorted_desc[0]


@pytest.fixture(scope='module')
def three_duplicates():
    return [
        FileItem(
            file=Path('/Users/jo/dev/exify/tests/data/duplicates/set1/IMG-20140831-WA0002.jpg')
        ),
        FileItem(
            file=Path('/Users/jo/dev/exify/tests/data/duplicates/set1/IMG-20140831-WA0001.jpg')
        ),
        FileItem(
            file=Path('/Users/jo/dev/exify/tests/data/duplicates/set1/IMG-20140901-WA0000.jpg')
        )

    ]


@pytest.fixture(scope='module')
def two_duplicates_same_size():
    return [
        FileItem(
            file=Path('/Users/jo/dev/exify/tests/data/duplicates/set1/IMG-20140831-WA0002.jpg')
        ),
        FileItem(
            file=Path('/Users/jo/dev/exify/tests/data/duplicates/set1/IMG-20140901-WA0000.jpg')
        )
    ]


@pytest.mark.asyncio
class TestSelectFileByExifDimensions:
    async def test_image_with_biggest_dimensions_is_selected(self, three_duplicates):
        analyzers = [await WhatsappImageAnalyzer.create(item) for item in three_duplicates]
        [await a.get_dimensions() for a in analyzers]

        assert all([instance.item.dimensions for instance in analyzers])


@pytest.mark.asyncio
class TestSelectBestFileBySize:

    def test_bigger_file_is_selected(self, three_duplicates):
        result = find_better_version(three_duplicates)

        assert 'WA0001.jpg' in str(result)

    def test_some_file_is_selected_if_same_size(self, two_duplicates_same_size):
        result = find_better_version(two_duplicates_same_size)

        assert 'WA0002.jpg' in str(result)

    def test_no_input(self):
        with pytest.raises(ValueError, match='files'):
            find_better_version(files=[])
