import re
from functools import partial
from pathlib import Path
from typing import List

from exify.utils import call_blocking


async def find_files(start_dir: Path, *, pattern: re.Pattern = None) -> List[Path]:
    """Find files"""
    if pattern:
        is_match = lambda x: re.compile(r'(.*?)').search(x.name)
    else:
        is_match = lambda x: x.suffix.lower() in ('.jpg', '.jpeg')

    results = await call_blocking(partial(start_dir.rglob, '*'))
    return [x.expanduser().absolute() for x in results if x.is_file() and is_match(x)]
