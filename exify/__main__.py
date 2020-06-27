import asyncio
import re
from collections import defaultdict
from datetime import datetime
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Dict, MutableMapping

import aiofiles
from exif import Image
from loguru import logger

from exify.models import ExifySettings, TimestampData, ExifTimestampAttribute


class NoExifDataFoundError(Exception):
    """NoExifDataFoundError"""


async def _find_exif_timestamps(img: Image) -> MutableMapping[str, datetime]:
    exif_timestamp_format = '%Y:%m:%d %H:%M:%S'

    if img.has_exif:
        found = defaultdict(datetime)
        for attr in ExifTimestampAttribute.list():
            if raw := getattr(img, attr, None):
                found[attr] = datetime.strptime(raw, exif_timestamp_format)
        return found


class WhatsappFileAnalyzer:
    FILENAME_PATTERN = r'\d{8}'
    FILENAME_DATE_FORMAT = '%Y%m%d'

    def __init__(self, f: Path, *, settings=None):
        self._settings = settings or get_settings()

        if not f.is_absolute():
            f = self._settings.base_dir / f
        self._target = f

    async def _get_timestamp_from_filename(self) -> datetime:
        pattern = re.compile(self.FILENAME_PATTERN)
        matcher = pattern.search(self._target.stem)
        result = matcher.group(0)
        parsed = datetime.strptime(result, self.FILENAME_DATE_FORMAT)

        self._log_timestamp_results(timestamp=parsed, src='file name')
        return parsed

    def _log_timestamp_results(self, timestamp, *, src, type_='created'):
        logger.debug(f'{self._target}: {type_} ({src}): {timestamp}')

    async def _get_timestamp_from_file_system(self, attr: Enum) -> datetime:
        result = getattr(self._target.lstat(), attr)
        parsed = datetime.fromtimestamp(result)

        self._log_timestamp_results(timestamp=parsed, src='file system', type_=attr.name)
        return parsed

    async def _get_timestamp_from_exif(self, attr: Enum) -> datetime:
        async with aiofiles.open(self._target, mode='rb') as f:
            error_msg = f'No EXIF timestamps found in {self._target}'
            img = Image(await f.read())

            if found := await _find_exif_timestamps(img):
                self._log_timestamp_results(timestamp=found, src='EXIF', type_=attr.name)
                return found
            logger.warning(error_msg)
            raise NoExifDataFoundError(error_msg)

    async def analyze_timestamp(self) -> Dict[Path, TimestampData]:
        logger.info(f'Analyzing {self._target}')

        data = await self.gather_timestamp_data()

        return data

    async def gather_timestamp_data(self):
        try:
            exif_data = await self._get_timestamp_from_exif(ExifTimestampAttribute.datetime)
        except NoExifDataFoundError:
            exif_data = None
        data = TimestampData(
            file_name=await self._get_timestamp_from_filename(),
            file_created=await self._get_timestamp_from_file_system(self._settings.file_attribute.created),
            file_modified=await self._get_timestamp_from_file_system(self._settings.file_attribute.modified),
            exif_created=exif_data,
        )
        return data


async def run(settings: ExifySettings):
    src = settings.base_dir
    logger.info(f'Running on {src}...')

    if files := [x for x in src.iterdir() if x.is_file()]:
        results = {f: await WhatsappFileAnalyzer(f, settings=settings).analyze_timestamp() for f in files}

        for filename, result in results.items():
            logger.info(f'{filename}: {result}')
            break


@lru_cache
def get_settings():
    settings = ExifySettings()
    return settings


if __name__ == '__main__':
    settings = get_settings()
    asyncio.run(run(settings=settings))
