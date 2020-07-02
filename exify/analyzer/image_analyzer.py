"""WhatsApp image analyzer"""
import re
from collections import OrderedDict, defaultdict
from datetime import timedelta, datetime
from enum import Enum
from operator import itemgetter
from typing import Optional, MutableMapping, List

from loguru import logger

from exify.analyzer._base import SingleFileAnalyzer
from exify.errors import NoExifDataFoundError
from exify.constants import EXIF_TIMESTAMP_FORMAT, ACCEPTABLE_TIME_DELTA
from exify.adapter.piexif_adapter import PiexifAdapter
from exify.models import FileItem, Timestamps, ExifTimestampAttribute


class WhatsappImageAnalyzer(SingleFileAnalyzer):
    FILENAME_PATTERN = r'\d{8}'
    FILENAME_DATE_FORMAT = '%Y%m%d'

    @classmethod
    async def create(
            cls,
            item: FileItem,
            *,
            settings=None,
            tasks: List = None,
            adapter: Optional[PiexifAdapter] = None
    ):
        instance = await super().create(item, tasks=tasks, settings=settings)
        instance._adapter = adapter or PiexifAdapter(file_name=instance.item.file)
        instance._tasks = tasks or [
            await instance.get_size(),
            await instance.get_dimensions(),
            await instance.get_timestamp(),
        ]
        return instance

    @property
    def authoritative_timestamp_attribute(self):
        return self.item.timestamps.file_name

    async def get_size(self):
        self.item.size = self.item.file.stat().st_size

    async def get_timestamp(self) -> None:
        logger.debug(f'[ ] Analyzing {self._item.file}')

        await self.gather_timestamp_data()
        if self.deviation_is_ok():
            self.item.results.deviation_ok = True
        if self.item.timestamps.exif:
            self.item.results.exif_timestamp_exists = True

    async def get_dimensions(self) -> None:
        data = await self._adapter.get_exif_data()
        self.item.dimensions.width = data['ImageWidth']
        self.item.dimensions.height = data['ImageLength']

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
