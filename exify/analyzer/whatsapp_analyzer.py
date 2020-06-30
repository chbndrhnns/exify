import re
from collections import OrderedDict, defaultdict
from datetime import timedelta, datetime
from enum import Enum
from operator import itemgetter
from typing import Optional, MutableMapping

from loguru import logger

from exify.errors import NoExifDataFoundError
from exify.settings import get_settings
from exify.constants import EXIF_TIMESTAMP_FORMAT, ACCEPTABLE_TIME_DELTA
from exify.adapter.piexif_adapter import PiexifAdapter
from exify.models import FileItem, Timestamps, ExifTimestampAttribute


class WhatsappFileAnalyzer:
    FILENAME_PATTERN = r'\d{8}'
    FILENAME_DATE_FORMAT = '%Y%m%d'

    def __init__(self, item: FileItem, *, settings=None, adapter: Optional[PiexifAdapter] = None):
        self._settings = settings or get_settings()

        if not isinstance(item, FileItem):
            raise ValueError('item must be of type FileItem')
        self._item: FileItem = item
        self._adapter = adapter or PiexifAdapter(file_name=self._item.file)

    @property
    def item(self):
        return self._item

    @property
    def authoritative_timestamp_attribute(self):
        return self.item.timestamps.file_name

    async def analyze_timestamp(self) -> None:
        logger.debug(f'[ ] Analyzing {self._item.file}')

        await self.gather_timestamp_data()
        if self.deviation_is_ok():
            self.item.results.deviation_ok = True
        if self.item.timestamps.exif:
            self.item.results.exif_timestamp_exists = True

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
        exif_data = await self._adapter.get_exif_data()

        if timestamps_found := await _find_exif_timestamps(exif_data):
            [
                self._log_timestamp_results(timestamp=f"{val}", src='EXIF', type_=attr)
                for attr, val in timestamps_found.items()
            ]
            return timestamps_found
        logger.info(error_msg)
        raise NoExifDataFoundError(error_msg)


async def _find_exif_timestamps(exif_data: MutableMapping) -> MutableMapping[str, datetime]:
    found = defaultdict(datetime)
    for attr in ExifTimestampAttribute.list():
        if raw := exif_data.get(attr):
            found[attr] = datetime.strptime(raw, EXIF_TIMESTAMP_FORMAT)
    return found
