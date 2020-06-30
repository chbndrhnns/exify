from pathlib import Path

import pytest
from pydantic.main import BaseModel

from exify.models import FileItem
from tests.conftest import TESTS_ROOT

EXAMPLES_DIR = Path('data')


class Examples(BaseModel):
    no_exif: Path = EXAMPLES_DIR / 'IMG-20140430-WA0004.jpg'


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
    return Examples()
