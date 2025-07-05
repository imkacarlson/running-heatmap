import io
import textwrap
import json

def tiny_gpx():
    return textwrap.dedent("""\
        <gpx><trk><trkseg>
          <trkpt lat="0.0" lon="0.0"/><trkpt lat="0.01" lon="0.01"/>
        </trkseg></trk></gpx>""").encode()

def test_upload_and_lasso_roundtrip(client):
    # upload
    data = {"files": (io.BytesIO(tiny_gpx()), "f.gpx")}
    r = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert r.status_code == 200
    new_id = r.get_json()["added"][0]

    # lasso polygon around the two pts
    poly = [[-0.1,-0.1],[0.1,-0.1],[0.1,0.1],[-0.1,0.1],[-0.1,-0.1]]
    r = client.post("/api/runs_in_area", json={"polygon": poly})
    ids = [f["id"] for f in r.get_json()["runs"]]
    assert new_id in ids
