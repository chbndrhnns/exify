import asyncio
import re
from collections import defaultdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict

from exif import Image
from loguru import logger

from exify.models import ExifySettings, TimestampData, ExifTimestampAttribute


class NoExifDataFoundError(Exception):
    """NoExifDataFoundError"""


async def _find_exif_timestamps(img: Image):
    exif_timestamp_format = '%Y:%m:%d %H:%M:%S'

    found = defaultdict(datetime)
    for attr in ExifTimestampAttribute.list():
        if raw := getattr(img, attr, None):
            found[attr] = datetime.strptime(raw, exif_timestamp_format)
    return found


class WhatsappFileAnalyzer:
    FILENAME_PATTERN = r'\d{8}'
    FILENAME_DATE_FORMAT = '%Y%m%d'

    def __init__(self, f: Path, *, settings=None):
        self._settings = settings or ExifySettings()
        self._target = f

    async def _get_timestamp_from_filename(self) -> datetime:
        pattern = re.compile(self.FILENAME_PATTERN)
        matcher = pattern.search(self._target.stem)
        result = matcher.group(0)
        parsed = datetime.strptime(result, self.FILENAME_DATE_FORMAT)

        return parsed

    async def _get_timestamp_from_file(self, attr: Enum) -> datetime:
        result = getattr(self._target.lstat(), attr)
        parsed = datetime.fromtimestamp(result)

        return parsed

    async def _get_timestamp_from_exif(self, attr: Enum) -> datetime:
        with open(self._target, 'rb') as f:
            img = Image(f)

            if not img.has_exif:
                raise NoExifDataFoundError(f'No EXIF data found in {self._target}')
            found = await _find_exif_timestamps(img)

            logger.info(found)

            return found

    async def analyze_timestamp(self) -> Dict[Path, TimestampData]:
        logger.info(f'Analyzing {self._target}')

        data = TimestampData(
            file_name=await self._get_timestamp_from_filename(),
            file_created=await self._get_timestamp_from_file(settings.file_attribute.created),
            file_modified=await self._get_timestamp_from_file(settings.file_attribute.modified),
            exif_created=await self._get_timestamp_from_exif(ExifTimestampAttribute.datetime),
        )
        return data


async def run(settings: ExifySettings):
    src = settings.base_dir
    logger.info(f'Running on {src}...')

    files = [x for x in src.iterdir() if x.is_file()]

    results = {f: await WhatsappFileAnalyzer(f, settings=settings).analyze_timestamp() for f in files}

    for filename, result in results.items():
        logger.info(f'{filename}: {result}')
        break


if __name__ == '__main__':
    settings = ExifySettings()
    asyncio.run(run(settings=settings))
