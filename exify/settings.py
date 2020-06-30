import platform
from functools import lru_cache
from pathlib import Path
from typing import Union

from pydantic import BaseSettings, Field, root_validator

from exify import PROJECT_ROOT
from exify.models import MacFileAttribute, WindowsFileAttribute, LinuxFileAttribute, FileAttributeMap


@lru_cache
def get_settings():
    return ExifySettings()


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