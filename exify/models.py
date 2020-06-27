import platform
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Union, Optional, MutableMapping

from pydantic import BaseModel, BaseSettings, Field, root_validator


class ExifTimezoneAttribute(str, Enum):
    offset = 'offset_time'
    offset_original = 'offset_time_original'
    offset_digitized = 'offset_time_digitized'

    @staticmethod
    def list():
        return list(map(lambda a: a.value, ExifTimezoneAttribute))


class ExifTimestampAttribute(str, Enum):
    datetime = 'datetime'
    original = 'datetime_original'
    digitized = 'datetime_digitized'
    gps_timestamp = 'gps_timestamp'

    @staticmethod
    def list():
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


class FileAttributeMap(BaseModel):
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

    class Config:
        env_file = '.env'


class TimestampData(BaseModel):
    file: Path
    file_name: Optional[datetime]
    file_created: datetime
    file_modified: datetime
    exif: Optional[MutableMapping[Union[ExifTimestampAttribute, ExifTimezoneAttribute], datetime]]
