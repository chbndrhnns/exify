from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Union, Optional, MutableMapping, List

from pydantic import BaseModel, Extra

from exify.errors import ExifyError


class ExifyBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True


class ExifTimezoneAttribute(str, Enum):
    offset = 'OffsetTime'
    offset_original = 'OffsetTimeOriginal'
    offset_digitized = 'OffsetTimeDigitized'

    @staticmethod
    def list() -> List:
        return list(map(lambda a: a.value, ExifTimezoneAttribute))


class ExifTimestampAttribute(str, Enum):
    """Map internal attribute names to EXIF attribute names"""
    datetime = 'DateTime'
    original = 'DateTimeOriginal'
    digitized = 'DateTimeDigitized'
    gps_timestamp = 'GPSTimeStamp'

    @staticmethod
    def list() -> List:
        return list(map(lambda a: a.value, ExifTimestampAttribute))


class WindowsFileAttribute(str, Enum):
    created = 'st_ctime'
    modified = 'st_mtime'


class MacFileAttribute(str, Enum):
    created = 'st_birthtime'
    modified = 'st_mtime'


class LinuxFileAttribute(str, Enum):
    created = 'st_mtime'
    modified = 'st_mtime'


class FileAttributeMap(ExifyBaseModel):
    Darwin: Enum = MacFileAttribute
    Linux: Enum = LinuxFileAttribute
    Windows: Enum = WindowsFileAttribute


class Timestamps(ExifyBaseModel):
    file_name: Optional[datetime]
    file_created: Optional[datetime]
    file_modified: Optional[datetime]
    exif: Optional[MutableMapping[Union[ExifTimestampAttribute, ExifTimezoneAttribute], datetime]] = {

    }


class AnalysisResults(ExifyBaseModel):
    deviation_ok: bool = False
    exif_timestamp_exists: bool = False


class FileItem(ExifyBaseModel):
    file: Path
    timestamps: Timestamps = Timestamps()
    results: AnalysisResults = AnalysisResults()
    errors: List[ExifyError] = []
