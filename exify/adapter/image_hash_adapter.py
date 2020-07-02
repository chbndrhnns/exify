from pathlib import Path

from exify.adapter._base import BaseAdapter


class ImageHashAdapter(BaseAdapter):
    def __init__(self, file_name: Path):
        ...
