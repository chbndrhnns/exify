import asyncio
import re
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Dict, MutableMapping, Optional

import aiofiles
from exif import Image
from loguru import logger

from exify.models import ExifySettings, TimestampData, ExifTimestampAttribute
from exify.utils import utcnow

ACCEPTABLE_TIME_DELTA = timedelta(days=30)


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
        self._timestamp_data: Optional[TimestampData] = None

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
        self._timestamp_data = TimestampData(
            file=self._target,
            file_name=await self._get_timestamp_from_filename(),
            file_created=await self._get_timestamp_from_file_system(self._settings.file_attribute.created),
            file_modified=await self._get_timestamp_from_file_system(self._settings.file_attribute.modified),
            exif=exif_data,
        )
        return self._timestamp_data

    async def deviation_is_ok(self, max_deviation: timedelta = ACCEPTABLE_TIME_DELTA):
        flattened = {
            **self._timestamp_data.dict(exclude={'exif', 'file'}),
            **self._timestamp_data.exif
        }
        ordered = OrderedDict(sorted(flattened.items(), key=lambda t: t[0]))
        vals = list(ordered.values())
        oldest = vals[-1]
        youngest = vals[0]

        return oldest - youngest < max_deviation


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
    return ExifySettings()


if __name__ == '__main__':
    settings = get_settings()
    asyncio.run(run(settings=settings))
