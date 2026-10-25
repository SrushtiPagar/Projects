"""Streamlit UI for the breast cancer detection project.
Run from the project root:  streamlit run app.py
"""
import json
import os
from pathlib import Path

import joblib
import pandas as pd
import requests
import streamlit as st

from src.data import DATA_PATH, TARGET, MALIGNANT_LABEL

MODEL_PATH = Path("models/best_model.joblib")
META_PATH = Path("models/metadata.json")
RESULTS_PATH = Path("models/results.csv")
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Breast Cancer Detection", page_icon="🩺", layout="wide")


# ---------- loading ----------
@st.cache_resource
def load_model():
    model = joblib.load(MODEL_PATH)
    meta = json.loads(META_PATH.read_text())
    return model, meta


@st.cache_data
def load_reference_data():
    return pd.read_csv(DATA_PATH)


def malignant_probability(model, X: pd.DataFrame):
    idx = list(model.classes_).index(MALIGNANT_LABEL)
    return model.predict_proba(X)[:, idx]


@st.cache_data(ttl=5)
def api_status():
    """Returns the /health payload if the API is reachable, else None."""
    try:
        r = requests.get(f"{API_URL}/health", timeout=1.5)
        return r.json() if r.ok else None
    except requests.RequestException:
        return None


def predict_one(values: dict, api_ok: bool) -> dict:
    if api_ok:
        r = requests.post(f"{API_URL}/predict", json={"features": values}, timeout=10)
        r.raise_for_status()
        return r.json()
    X = pd.DataFrame([values], columns=features)
    p = float(malignant_probability(model, X)[0])
    return {"malignant_probability": p, "prediction": "Malignant" if p >= 0.5 else "Benign",
            "model": meta["best_model"], "cached": None, "latency_ms": None}


def predict_many(batch: pd.DataFrame, api_ok: bool) -> list:
    if api_ok:
        rows = batch[features].to_dict(orient="records")
        r = requests.post(f"{API_URL}/predict/batch", json={"rows": rows}, timeout=60)
        r.raise_for_status()
        return [x["malignant_probability"] for x in r.json()["results"]]
    return list(malignant_probability(model, batch[features]))


def group_features(features):
    """Group the 30 inputs into mean / error / worst so the form stays readable."""
    groups = {"Mean values": [], "Error values": [], "Worst values": [], "Other": []}
    for f in features:
        if f.startswith("mean "):
            groups["Mean values"].append(f)
        elif f.endswith(" error"):
            groups["Error values"].append(f)
        elif f.startswith("worst "):
            groups["Worst values"].append(f)
        else:
            groups["Other"].append(f)
    return {k: v for k, v in groups.items() if v}


# ---------- guard: model must exist ----------
if not MODEL_PATH.exists() or not META_PATH.exists():
    st.error("No trained model found. Run `python -m src.train` first, then refresh this page.")
    st.stop()
if not Path(DATA_PATH).exists():
    st.error(f"Dataset not found at `{DATA_PATH}`. Put your CSV there.")
    st.stop()

model, meta = load_model()
ref = load_reference_data()
features = meta["features"]

status = api_status()
api_ok = status is not None

st.title("🩺 Breast Cancer Detection")
st.caption(f"Model: **{meta['best_model']}** (selected by cross-validated recall). "
           "Educational project, not a medical device.")
if api_ok:
    st.success(f"Backend: FastAPI at {API_URL} | Redis cache: "
               f"{'on' if status['redis'] else 'off'} | PostgreSQL log: "
               f"{'on' if status['database'] else 'off'}")
else:
    st.info("Backend: local model (API not running). Start it with "
            "`uvicorn src.api:app` to use the API.")

tab_predict, tab_batch, tab_compare = st.tabs(["Single prediction", "Batch (CSV)", "Model comparison"])

# ---------- tab 1: single prediction ----------
with tab_predict:
    medians = ref[features].median()

    # Widget values live in session_state so the sample buttons can fill the form
    for f in features:
        st.session_state.setdefault(f, float(medians[f]))

    def fill_from_sample(label):
        rows = ref[ref[TARGET] == label]
        sample = rows.sample(1).iloc[0]
        for f in features:
            st.session_state[f] = float(sample[f])

    def reset_to_median():
        for f in features:
            st.session_state[f] = float(medians[f])

    c1, c2, c3 = st.columns(3)
    c1.button("Load a random malignant sample", on_click=fill_from_sample, args=(MALIGNANT_LABEL,))
    c2.button("Load a random benign sample", on_click=fill_from_sample, args=(1 - MALIGNANT_LABEL,))
    c3.button("Reset to median values", on_click=reset_to_median)

    for title, cols in group_features(features).items():
        with st.expander(title, expanded=(title == "Mean values")):
            grid = st.columns(3)
            for i, f in enumerate(cols):
                grid[i % 3].number_input(
                    f, min_value=float(ref[f].min()), max_value=float(ref[f].max()),
                    format="%.5f", key=f)

    if st.button("Predict", type="primary"):
        values = {f: float(st.session_state[f]) for f in features}
        try:
            res = predict_one(values, api_ok)
        except requests.RequestException as exc:
            st.error(f"API request failed: {exc}")
            st.stop()
        p_mal = res["malignant_probability"]
        label = res["prediction"]

        m1, m2, m3 = st.columns(3)
        m1.metric("Prediction", label)
        m2.metric("Probability of malignant", f"{p_mal:.1%}")
        if res["latency_ms"] is not None:
            m3.metric("Latency", f"{res['latency_ms']} ms",
                      "from Redis cache" if res["cached"] else "computed by model",
                      delta_color="off")
        st.progress(min(max(p_mal, 0.0), 1.0))
        if label == "Malignant":
            st.warning("The model predicts malignant. In a real setting this needs clinical follow-up.")
        else:
            st.success("The model predicts benign.")

# ---------- tab 2: batch ----------
with tab_batch:
    st.write("Upload a CSV with the same feature columns as the training data "
             "(a `target` column is ignored if present).")
    up = st.file_uploader("CSV file", type="csv")
    if up is not None:
        batch = pd.read_csv(up)
        missing = [f for f in features if f not in batch.columns]
        if missing:
            st.error(f"Missing columns: {missing[:5]}{' ...' if len(missing) > 5 else ''}")
        else:
            out = batch.copy()
            out["malignant_probability"] = pd.Series(predict_many(batch, api_ok)).round(4).values
            out["prediction"] = ["Malignant" if p >= 0.5 else "Benign"
                                 for p in out["malignant_probability"]]
            st.dataframe(out, width="stretch")
            st.download_button("Download predictions", out.to_csv(index=False).encode(),
                               "predictions.csv", "text/csv")

# ---------- tab 3: comparison ----------
with tab_compare:
    if RESULTS_PATH.exists():
        res = pd.read_csv(RESULTS_PATH)
        st.dataframe(res, width="stretch", hide_index=True)
        st.subheader("Cross-validated recall (malignant class)")
        st.bar_chart(res.set_index("model")["cv_recall"])
    else:
        st.info("Run `python -m src.train` to generate the comparison table.")
