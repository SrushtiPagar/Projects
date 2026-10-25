"""FastAPI prediction service with optional Redis caching and PostgreSQL logging.

Run from the project root:
    uvicorn src.api:app --reload

Optional environment variables:
    ONNX_MODEL_PATH  e.g. models/model.onnx  (serve the ONNX model with ONNX Runtime
                     instead of the scikit-learn pickle)
Redis and PostgreSQL are optional. Set these environment variables to enable them:
    REDIS_URL     e.g. redis://localhost:6379/0
    DATABASE_URL  e.g. postgresql+psycopg2://cancer:cancer@localhost:5432/cancerdb
If a service is unset or unreachable, the API still works without it.
"""
import hashlib
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import redis
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.data import MALIGNANT_LABEL

log = logging.getLogger("cancer-api")
Base = declarative_base()
CACHE_TTL_SECONDS = 3600


# ---------- database table ----------
class PredictionLog(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    model_name = Column(String(100))
    features = Column(JSON)
    malignant_probability = Column(Float)
    prediction = Column(String(20))
    cached = Column(Boolean)
    latency_ms = Column(Float)


# ---------- request schemas ----------
class PredictRequest(BaseModel):
    features: dict[str, float]


class BatchRequest(BaseModel):
    rows: list[dict[str, float]]


# ---------- helpers ----------
def _connect_redis(url: str):
    client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
    client.ping()
    return client


def _malignant_probs(model, X: pd.DataFrame):
    idx = list(model.classes_).index(MALIGNANT_LABEL)
    return model.predict_proba(X)[:, idx]


def _label(p: float) -> str:
    return "Malignant" if p >= 0.5 else "Benign"


def _cache_key(model_name: str, values: dict) -> str:
    raw = json.dumps([model_name, values], sort_keys=True)
    return "pred:" + hashlib.sha256(raw.encode()).hexdigest()


def _check_features(state, row: dict) -> dict:
    missing = [f for f in state.features if f not in row]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing features: {missing}")
    return {f: row[f] for f in state.features}


def _save_log(state, values, result, cached, latency_ms):
    if state.db is None:
        return
    try:
        with state.db() as session:
            session.add(PredictionLog(
                model_name=state.model_name, features=values,
                malignant_probability=result["malignant_probability"],
                prediction=result["prediction"], cached=cached, latency_ms=latency_ms))
            session.commit()
    except Exception as exc:  # logging must never break a prediction
        log.warning("Could not write prediction log: %s", exc)


def _retry(fn, what: str):
    """Call fn() until it works. Containers often start before Postgres/Redis are ready."""
    attempts = int(os.getenv("STARTUP_RETRIES", "10"))
    delay = float(os.getenv("STARTUP_RETRY_DELAY", "2"))
    for i in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            if i == attempts:
                log.warning("%s unavailable after %d attempts, running without it: %s",
                            what, attempts, exc)
                return None
            log.info("%s not ready (attempt %d/%d): %s", what, i, attempts, exc)
            time.sleep(delay)


def _init_db(url: str):
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


# ---------- app ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = Path(os.getenv("MODEL_PATH", "models/best_model.joblib"))
    meta_path = Path(os.getenv("META_PATH", "models/metadata.json"))
    meta = json.loads(meta_path.read_text())
    onnx_path = os.getenv("ONNX_MODEL_PATH")
    if onnx_path:
        # ONNX Runtime backend: no scikit-learn / xgboost / torch needed to run the model
        from src.onnx_utils import OnnxScorer
        app.state.model = OnnxScorer(onnx_path)
        app.state.backend = "onnxruntime"
    else:
        app.state.model = joblib.load(model_path)
        app.state.backend = "sklearn"
    app.state.model_name = meta["best_model"]
    app.state.features = meta["features"]

    app.state.redis = None
    if os.getenv("REDIS_URL"):
        url = os.environ["REDIS_URL"]
        app.state.redis = _retry(lambda: _connect_redis(url), "Redis")

    app.state.db = None
    if os.getenv("DATABASE_URL"):
        url = os.environ["DATABASE_URL"]
        app.state.db = _retry(lambda: _init_db(url), "Database")
    yield


app = FastAPI(title="Breast Cancer Detection API", version="1.0", lifespan=lifespan)


@app.get("/health")
def health(request: Request):
    state = request.app.state
    redis_ok = False
    if state.redis is not None:
        try:
            redis_ok = bool(state.redis.ping())
        except redis.RedisError:
            pass
    return {"status": "ok", "model": state.model_name, "backend": state.backend,
            "redis": redis_ok, "database": state.db is not None}


@app.get("/features")
def features(request: Request):
    return {"features": request.app.state.features}


@app.post("/predict")
def predict(req: PredictRequest, request: Request):
    start = time.perf_counter()
    state = request.app.state
    values = _check_features(state, req.features)

    key = _cache_key(f"{state.model_name}|{state.backend}", values)
    result, cached = None, False

    if state.redis is not None:
        try:
            hit = state.redis.get(key)
            if hit:
                result, cached = json.loads(hit), True
        except redis.RedisError as exc:
            log.warning("Redis read failed: %s", exc)

    if result is None:
        X = pd.DataFrame([values], columns=state.features)
        p = float(_malignant_probs(state.model, X)[0])
        result = {"malignant_probability": p, "prediction": _label(p)}
        if state.redis is not None:
            try:
                state.redis.set(key, json.dumps(result), ex=CACHE_TTL_SECONDS)
            except redis.RedisError as exc:
                log.warning("Redis write failed: %s", exc)

    latency_ms = round((time.perf_counter() - start) * 1000, 3)
    _save_log(state, values, result, cached, latency_ms)
    return {**result, "model": state.model_name, "backend": state.backend,
            "cached": cached, "latency_ms": latency_ms}


@app.post("/predict/batch")
def predict_batch(req: BatchRequest, request: Request):
    """Scores many rows at once. Not cached or logged."""
    state = request.app.state
    rows = [_check_features(state, r) for r in req.rows]
    if not rows:
        return {"model": state.model_name, "results": []}
    X = pd.DataFrame(rows, columns=state.features)
    probs = _malignant_probs(state.model, X)
    return {"model": state.model_name,
            "results": [{"malignant_probability": float(p), "prediction": _label(float(p))}
                        for p in probs]}


@app.get("/predictions")
def recent_predictions(request: Request, limit: int = 10):
    state = request.app.state
    if state.db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    with state.db() as session:
        rows = (session.query(PredictionLog)
                .order_by(PredictionLog.id.desc()).limit(min(limit, 100)).all())
        return [{"id": r.id, "created_at": r.created_at.isoformat(), "model": r.model_name,
                 "prediction": r.prediction, "malignant_probability": r.malignant_probability,
                 "cached": r.cached, "latency_ms": r.latency_ms} for r in rows]
