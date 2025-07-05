import os
import pickle
import tempfile
import contextlib
import pytest
from server.app import app as flask_app

# creates a temp CWD with a minimal runs.pkl and yields
@pytest.fixture(scope="session", autouse=True)
def temp_dataset(tmp_path_factory, monkeypatch):
    tmpdir = tmp_path_factory.mktemp("rheat")
    pkl = tmpdir / "runs.pkl"
    sample = {1: {"bbox": (-1, -1, 1, 1), "geoms": {}, "metadata": {}}}
    pkl.write_bytes(pickle.dumps(sample))
    monkeypatch.chdir(tmpdir)
    yield

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c
