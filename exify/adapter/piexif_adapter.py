import asyncio
from collections import defaultdict
from pathlib import Path
from typing import Optional, Dict

import piexif

TIMESTAMP_TYPE = bytes

ATTRIBUTE_TO_TAG_MAP = {
    'DateTime': {'block': '0th', 'attribute': piexif.ImageIFD.DateTime},
    'DateTimeOriginal': {'block': 'Exif', 'attribute': piexif.ExifIFD.DateTimeOriginal},
    'DateTimeDigitized': {'block': 'Exif', 'attribute': piexif.ExifIFD.DateTimeDigitized},
    'GPSTimestamp': {'block': 'GPS', 'attribute': piexif.GPSIFD.GPSTimeStamp},
    'OffsetTime': {'block': 'Exif', 'attribute': piexif.ExifIFD.OffsetTime},
    'OffsetTimeOriginal': {'block': 'Exif', 'attribute': piexif.ExifIFD.OffsetTimeOriginal},
    'OffsetTimeDigitized': {'block': 'Exif', 'attribute': piexif.ExifIFD.OffsetTimeDigitized},
}


class PiexifAdapter:
    def __init__(self, file_name: Path = None):
        self._file_name: Path = file_name
        self._raw: Optional[Dict] = {}
        self._loop = asyncio.get_event_loop()

    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, val):
        self._file_name = val

    def _load_image(self):
        return piexif.load(str(self._file_name))

    def _write_image(self, exif_bytes):
        piexif.insert(exif_bytes, str(self.file_name))

    async def get_exif_data(self):
        if filename := self.file_name:
            self._raw = await self._loop.run_in_executor(None, self._load_image)

            decoded = defaultdict(str)
            for ifd in ("0th", "Exif", "GPS", "1st"):
                for tag in self._raw[ifd]:
                    raw = self._raw[ifd][tag]
                    if isinstance(raw, bytes):
                        raw = raw.decode('ascii')
                    decoded[piexif.TAGS[ifd][tag]["name"]] = raw
            return decoded
        raise ValueError('file_name has not been set')

    async def update_exif_data(self, data):
        if filename := self._file_name:
            for attr, val in data.items():
                config = ATTRIBUTE_TO_TAG_MAP.get(attr)
                raw_block = config['block']
                raw_attr = config['attribute']

                self._raw[raw_block].update(
                    {
                        raw_attr: str(val).encode('ascii')
                    }
                )
            exif_bytes = piexif.dump(self._raw)
            await self._loop.run_in_executor(None, self._write_image, exif_bytes)
        else:
            raise ValueError('file_name has not been set')
