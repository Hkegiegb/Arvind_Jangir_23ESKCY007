import importlib
import sys


def test_config_uses_mongomock_when_uri_missing(monkeypatch):
    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.delenv("MONGODB_DB", raising=False)
    sys.modules.pop("config", None)

    config = importlib.import_module("config")

    assert config.batches is not None
    assert config.batches.count_documents({}) == 0
