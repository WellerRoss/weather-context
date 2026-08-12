import pytest


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    # Settings() re-reads env vars on every construction (pydantic-settings), so
    # just pointing DATA_DIR at a tmp dir is enough to isolate each test's cache.
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "weather-context-data"))
