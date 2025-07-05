import os
import pickle
import tempfile
import contextlib
import pytest
from server.app import app as flask_app
from rtree import index

# creates a temp CWD with a minimal runs.pkl and yields
@pytest.fixture(scope="session", autouse=True)
def temp_dataset(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp("rheat")
    pkl = tmpdir / "runs.pkl"
    sample = {1: {"bbox": (-1, -1, 1, 1), "geoms": {}, "metadata": {}}}
    pkl.write_bytes(pickle.dumps(sample))

    orig = os.getcwd()
    os.chdir(tmpdir)

    # reconfigure the app to use this temporary dataset
    flask_app.RUNS_PKL_PATH = str(pkl)
    flask_app.runs = sample
    flask_app.idx = index.Index()
    for rid, run in sample.items():
        flask_app.idx.insert(rid, run["bbox"])

    yield

    os.chdir(orig)

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c
