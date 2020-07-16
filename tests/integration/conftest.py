from pathlib import Path
from typing import List

import pytest
from pydantic.main import BaseModel

from exify.models import FileItem
from tests.conftest import TESTS_ROOT

EXAMPLES_DIR = TESTS_ROOT / 'data'
WHATSAPP_DIR = TESTS_ROOT / EXAMPLES_DIR / 'whatsapp'
MACOS_SCREENSHOTS_DIR = TESTS_ROOT / EXAMPLES_DIR / 'screenshots-macos'


class WhatsappExamples(BaseModel):
    no_exif: Path = WHATSAPP_DIR / 'IMG-20140430-WA0004.jpg'


class ScreenshotExamples(BaseModel):
    timestamp_in_filename: List[Path] = [
        MACOS_SCREENSHOTS_DIR / 'Bildschirmfoto 2020-07-16 um 19.25.40.png',
        MACOS_SCREENSHOTS_DIR / 'Screenshot 2020-07-16 19.25.40.png'
    ]
    modified: List[Path] = [
        MACOS_SCREENSHOTS_DIR / 'IMG_4134.png',
    ]


class FakeItem(FileItem):
    file: Path = Path()


@pytest.fixture(scope='session')
def monkeypatch_session():
    from _pytest.monkeypatch import MonkeyPatch
    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(scope='session', autouse=True)
def env(monkeypatch_session):
    monkeypatch_session.setenv('BASE_DIR', str(TESTS_ROOT))


@pytest.fixture
def examples():
    return WhatsappExamples()
