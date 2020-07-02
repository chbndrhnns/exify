from abc import ABCMeta
from pathlib import Path


class BaseAdapter(metaclass=ABCMeta):
    def __init__(self, file_name: Path = None):
        self._file_name = file_name
