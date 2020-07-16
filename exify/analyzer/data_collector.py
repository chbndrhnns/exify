import functools
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, MutableMapping

from PIL import Image
from loguru import logger

from exify.adapter.exif_adapter import ExifAdapter
from exify.adapter.image_hash_adapter import ImageHashAdapter
from exify.analyzer.file_finder import find_files
from exify.models import FileMetadata, Dimensions
from exify.settings import ExifySettings, get_settings
from exify.utils import call_blocking

WHATSAPP_FILENAME_PATTERN = r'\d{8}'
WHATSAPP_FILENAME_DATE_FORMAT = '%Y%m%d'


class DataCollector:
    def __init__(self, *, settings: ExifySettings = None):
        self._settings = settings or get_settings()
        self._items: MutableMapping[Path, FileMetadata] = defaultdict(FileMetadata)

    @property
    def files(self) -> List[Path]:
        return list(self._items.keys())

    @property
    def items(self) -> MutableMapping[Path, FileMetadata]:
        return self._items

    async def run(self):
        files = await find_files(self._settings.base_dir)

        for file in files:
            metadata = FileMetadata(image=file)
            metadata.timestamp_name = await timestamp_from_filename(file)
            metadata.timestamp_created = await timestamp_from_file_system(file, self._settings.file_attribute.created)
            metadata.timestamp_modified = await timestamp_from_file_system(file, self._settings.file_attribute.modified)
            metadata.size = await file_size(file)
            metadata.image_hash = await generate_hash(file)
            metadata.dimensions = await dimensions(file)

            self._items.update(
                {item: metadata for item in files}
            )


def log_timestamp(image: Path, *, loc: str, what: datetime = 'timestamp', ):
    logger.debug(f'{image}: Found timestamp in {loc}: {what}')


async def timestamp_from_filename(image: Path) -> datetime:
    pattern = re.compile(WHATSAPP_FILENAME_PATTERN)
    matcher = pattern.search(image.stem)
    result = matcher.group(0)
    parsed = datetime.strptime(result, WHATSAPP_FILENAME_DATE_FORMAT)

    log_timestamp(image, loc='file name', what=parsed)
    return parsed


async def timestamp_from_file_system(image: Path, attr) -> datetime:
    result = getattr(image.lstat(), attr)
    parsed = datetime.fromtimestamp(result)

    log_timestamp(image, loc=attr, what=parsed)
    return parsed


async def file_size(image: Path) -> int:
    return image.stat().st_size


async def generate_hash(image: Path) -> str:
    adapter = ImageHashAdapter(image)
    hash_val = await adapter.calculate_hash()
    logger.debug(f'{image}: Created hash: {hash_val}')
    return hash_val


async def dimensions(image: Path) -> Dimensions:
    adapter = ExifAdapter(image)
    data = await adapter.get_exif_data()
    try:
        result = Dimensions(
            width=data['ImageWidth'],
            height=data['ImageLength']
        )
    except AttributeError:
        img = Image.open(image)
        result = await call_blocking(functools.partial(get_dimensions, img))

    logger.debug(f'{image}: Dimensions: {result}')
    return result


def get_dimensions(image):
    width, height = image.size
    return Dimensions(
        width=width,
        height=height
    )
