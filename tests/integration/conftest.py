import pytest

from tests.conftest import TESTS_ROOT


@pytest.fixture(scope='session')
def monkeypatch_session():
    from _pytest.monkeypatch import MonkeyPatch
    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(scope='session', autouse=True)
def env(monkeypatch_session):
    monkeypatch_session.setenv('BASE_DIR', str(TESTS_ROOT))
