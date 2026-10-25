"""API tests. They train a tiny model on scikit-learn's built-in data, so they do not
need your CSV or your trained model. Redis is faked and the database is SQLite.
Run:  pytest -q
"""
import json

import fakeredis
import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import src.api as api


@pytest.fixture(scope="module")
def dataset():
    return load_breast_cancer(as_frame=True).frame


@pytest.fixture()
def client(tmp_path, monkeypatch, dataset):
    X, y = dataset.drop("target", axis=1), dataset["target"]
    model = Pipeline([("scaler", StandardScaler()),
                      ("model", LogisticRegression(max_iter=1000))]).fit(X, y)
    joblib.dump(model, tmp_path / "model.joblib")
    (tmp_path / "meta.json").write_text(
        json.dumps({"best_model": "Logistic", "features": list(X.columns)}))

    monkeypatch.setenv("MODEL_PATH", str(tmp_path / "model.joblib"))
    monkeypatch.setenv("META_PATH", str(tmp_path / "meta.json"))
    monkeypatch.setenv("REDIS_URL", "redis://fake")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(api, "_connect_redis", lambda url: fake)

    with TestClient(api.app) as c:
        yield c


def _row(dataset, label):
    return dataset[dataset["target"] == label].iloc[0].drop("target").to_dict()


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["redis"] is True and body["database"] is True


def test_predict_malignant_and_benign(client, dataset):
    mal = client.post("/predict", json={"features": _row(dataset, 0)}).json()
    ben = client.post("/predict", json={"features": _row(dataset, 1)}).json()
    assert mal["prediction"] == "Malignant" and ben["prediction"] == "Benign"


def test_second_identical_request_is_cached(client, dataset):
    payload = {"features": _row(dataset, 0)}
    first = client.post("/predict", json=payload).json()
    second = client.post("/predict", json=payload).json()
    assert first["cached"] is False and second["cached"] is True
    assert first["malignant_probability"] == second["malignant_probability"]


def test_missing_features_returns_422(client):
    r = client.post("/predict", json={"features": {"mean radius": 14.0}})
    assert r.status_code == 422


def test_predictions_are_logged(client, dataset):
    client.post("/predict", json={"features": _row(dataset, 0)})
    client.post("/predict", json={"features": _row(dataset, 0)})
    logs = client.get("/predictions").json()
    assert len(logs) == 2 and logs[0]["cached"] is True and logs[1]["cached"] is False


def test_batch(client, dataset):
    rows = [_row(dataset, 0), _row(dataset, 1)]
    out = client.post("/predict/batch", json={"rows": rows}).json()
    assert [r["prediction"] for r in out["results"]] == ["Malignant", "Benign"]
