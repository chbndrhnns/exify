from collections import defaultdict
from functools import partial
from pathlib import Path
from typing import Optional, Dict

import piexif

from exify.adapter._base import BaseAdapter
from exify.utils import call_blocking

TIMESTAMP_TYPE = bytes

ATTRIBUTE_TO_TAG_MAP = {
    'DateTime': {'block': '0th', 'attribute': piexif.ImageIFD.DateTime},
    'DateTimeOriginal': {'block': 'Exif', 'attribute': piexif.ExifIFD.DateTimeOriginal},
    'DateTimeDigitized': {'block': 'Exif', 'attribute': piexif.ExifIFD.DateTimeDigitized},
    'GPSTimestamp': {'block': 'GPS', 'attribute': piexif.GPSIFD.GPSTimeStamp},
    'OffsetTime': {'block': 'Exif', 'attribute': piexif.ExifIFD.OffsetTime},
    'OffsetTimeOriginal': {'block': 'Exif', 'attribute': piexif.ExifIFD.OffsetTimeOriginal},
    'OffsetTimeDigitized': {'block': 'Exif', 'attribute': piexif.ExifIFD.OffsetTimeDigitized},
    'ImageWidth': {'block': 'Image', 'attribute': piexif.ImageIFD.ImageWidth},
    'ImageLength': {'block': 'Image', 'attribute': piexif.ImageIFD.ImageLength},
}


class PiexifAdapter(BaseAdapter):
    def __init__(self, file_name: Path = None):
        super().__init__(file_name)
        self._raw: Optional[Dict] = defaultdict(None)
        self._data = defaultdict(str)

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
        if self._data:
            return self._data

        look_for = ATTRIBUTE_TO_TAG_MAP.keys()
        if filename := self.file_name:
            self._raw = await call_blocking(partial(self._load_image))

            for ifd in ("0th", "Exif", "GPS", "1st"):
                for tag in self._raw[ifd]:
                    tag_name = piexif.TAGS[ifd][tag]["name"]
                    if tag_name in look_for:
                        raw = self._raw[ifd][tag]
                        if isinstance(raw, bytes):
                            raw = raw.decode('ascii')
                        self._data[tag_name] = raw
            return self._data
        raise ValueError('file_name has not been set')

    async def update_exif_data(self, data):
        if filename := self._file_name:
            for attr, val in data.items():
                config = ATTRIBUTE_TO_TAG_MAP.get(attr)
                raw_block = config['block']
                raw_attr = config['attribute']

                if not self._raw.get(raw_block):
                    self._raw[raw_block] = defaultdict(None)
                self._raw[raw_block][raw_attr] = str(val).encode('ascii')

            exif_bytes = piexif.dump(self._raw)
            await call_blocking(partial(self._write_image, exif_bytes))
        else:
            raise ValueError('file_name has not been set')
