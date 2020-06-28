import asyncio
import re
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from operator import itemgetter
from typing import MutableMapping, List, Optional

import aiofiles
from exif import Image
from loguru import logger

from exify.adapter.exif_adapter import ExifAdapter
from exify.models import ExifySettings, FileItem, ExifTimestampAttribute, Timestamps

EXIF_TIMESTAMP_FORMAT = '%Y:%m:%d %H:%M:%S'

ACCEPTABLE_TIME_DELTA = timedelta(days=30)


class NoExifDataFoundError(Exception):
    """NoExifDataFoundError"""


async def _find_exif_timestamps(img: Image) -> MutableMapping[str, datetime]:
    if img.has_exif:
        found = defaultdict(datetime)
        for attr in ExifTimestampAttribute.list():
            if raw := getattr(img, attr, None):
                found[attr] = datetime.strptime(raw, EXIF_TIMESTAMP_FORMAT)
        return found


class WhatsappTimestampWriter:

    def __init__(self, item: FileItem, *, settings=None, adapter: Optional[ExifAdapter] = None):
        self._item: FileItem = item
        self._settings = settings or get_settings()
        self._adapter = adapter or ExifAdapter()

    async def write_exif_data(self):
        pass

    async def generate_exif_timestamp(self) -> str:
        ts = self._item.timestamps.file_name
        attr = ExifTimestampAttribute.datetime
        self._item.timestamps.exif[attr] = ts
        logger.debug(f'Setting {attr.datetime} to "{ts}"')


class WhatsappFileAnalyzer:
    FILENAME_PATTERN = r'\d{8}'
    FILENAME_DATE_FORMAT = '%Y%m%d'

    def __init__(self, item: FileItem, *, settings=None, adapter: Optional[ExifAdapter] = None):
        self._settings = settings or get_settings()
        self._adapter = adapter or ExifAdapter()

        if not isinstance(item, FileItem):
            raise ValueError('item must be of type FileItem')
        self._item: FileItem = item

    @property
    def item(self):
        return self._item

    async def analyze_timestamp(self) -> FileItem:
        logger.info(f'[ ] Analyzing {self._item.file}')

        await self.gather_timestamp_data()
        if self.deviation_is_ok():
            self.item.results.deviation_ok = True

        logger.info(f'[X] Analyzing {self._item.file}')

    async def gather_timestamp_data(self):
        try:
            exif_data = await self._get_timestamp_from_exif()
        except NoExifDataFoundError:
            exif_data = {}
        self._item.timestamps = Timestamps(
            file_name=await self._get_timestamp_from_filename(),
            file_created=await self._get_timestamp_from_file_system(self._settings.file_attribute.created),
            file_modified=await self._get_timestamp_from_file_system(self._settings.file_attribute.modified),
            exif=exif_data,
        )

    def deviation_is_ok(self, max_deviation: timedelta = ACCEPTABLE_TIME_DELTA):
        flattened = {
            **self.item.timestamps.dict(exclude={'exif'}),
            **self.item.timestamps.exif
        }
        ordered = OrderedDict(sorted(flattened.items(), key=itemgetter(1)))
        timestamps = list(ordered.values())
        oldest = timestamps[-1]
        youngest = timestamps[0]

        return oldest - youngest < max_deviation

    async def _get_timestamp_from_filename(self) -> datetime:
        pattern = re.compile(self.FILENAME_PATTERN)
        matcher = pattern.search(self._item.file.stem)
        result = matcher.group(0)
        parsed = datetime.strptime(result, self.FILENAME_DATE_FORMAT)

        self._log_timestamp_results(timestamp=parsed, src='name')
        return parsed

    def _log_timestamp_results(self, timestamp, *, src, type_='created'):
        logger.debug(f'{self._item.file}: {src}({type_}): {timestamp}')

    async def _get_timestamp_from_file_system(self, attr: Enum) -> datetime:
        result = getattr(self._item.file.lstat(), attr)
        parsed = datetime.fromtimestamp(result)

        self._log_timestamp_results(timestamp=parsed, src='fs', type_=attr.name)
        return parsed

    async def _get_timestamp_from_exif(self) -> MutableMapping[str, datetime]:
        error_msg = f'No EXIF timestamps found in {self._item.file}'
        image = await self._adapter.get_exif_data(self._item.file)

        if found := await _find_exif_timestamps(image):
            [
                self._log_timestamp_results(timestamp=f"{val}", src='EXIF', type_=attr)
                for attr, val in found.items()
            ]
            return found
        logger.warning(error_msg)
        raise NoExifDataFoundError(error_msg)


def _expand_to_absolute_path(file):
    if not file.is_absolute():
        file = get_settings().base_dir / file
    return file.absolute()


async def run(settings: ExifySettings):
    src = settings.base_dir
    logger.info(f'Running on {src}...')

    if files := [x for x in src.iterdir() if x.is_file()]:
        results = await analyze_files(files, settings)
        await analyze_results(results)


async def analyze_results(items: List[FileItem]):
    ok = []
    not_ok = []
    for item in items.values():
        if any([res for res in item.results]):
            not_ok.append(item)
        else:
            ok.append(item)

    logger.info(f'OK: {len(ok)}')
    logger.info(f'NOT OK: {len(not_ok)}')


async def analyze_files(files, settings):
    results = defaultdict(FileItem)
    for filename in files:
        filename = _expand_to_absolute_path(filename)
        item = FileItem(
            file=filename
        )
        results[filename] = item

        await WhatsappFileAnalyzer(item, settings=settings).analyze_timestamp()
        logger.info(f'{filename}: {item.results}')
    return results


@lru_cache
def get_settings():
    return ExifySettings()


if __name__ == '__main__':
    settings = get_settings()
    asyncio.run(run(settings=settings))
