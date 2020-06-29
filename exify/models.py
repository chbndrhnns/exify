import platform
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Union, Optional, MutableMapping, List

from pydantic import BaseModel, BaseSettings, Field, root_validator, Extra

from exify import PROJECT_ROOT


class ExifyBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid


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


class ExifySettings(BaseSettings):
    base_dir: Path = Field(..., env='BASE_DIR')
    system: str = platform.system()
    file_attribute = Union[MacFileAttribute, WindowsFileAttribute, LinuxFileAttribute]

    @root_validator
    def set_file_attribute(cls, values):
        values['file_attribute'] = getattr(FileAttributeMap, values['system'])
        return values

    @root_validator
    def make_base_dir_absolute(cls, values):
        base_dir = values.get('base_dir')
        if not Path(base_dir).is_absolute():
            values['base_dir'] = (PROJECT_ROOT / base_dir).expanduser().absolute()
        return values

    class Config:
        env_file = PROJECT_ROOT / '.env'


class Timestamps(ExifyBaseModel):
    file_name: Optional[datetime]
    file_created: Optional[datetime]
    file_modified: Optional[datetime]
    exif: Optional[MutableMapping[Union[ExifTimestampAttribute, ExifTimezoneAttribute], datetime]] = {

    }


class AnalysisResults(ExifyBaseModel):
    deviation_ok: bool = False


class FileItem(ExifyBaseModel):
    file: Path
    timestamps: Timestamps = Timestamps()
    results: AnalysisResults = AnalysisResults()
