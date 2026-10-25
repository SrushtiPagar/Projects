# Breast Cancer Detection: model comparison, API, UI, Docker, Kubernetes and ONNX

Architecture: Streamlit UI -> FastAPI -> model, with Redis (cache) and PostgreSQL (prediction log).

## 1. Train (compares 10 models, saves the best)

    pip install -r requirements.txt
    # put your breast_cancer.csv in data/
    python -m src.train

## 2. Run from your virtual environment (development)

    docker compose up -d postgres redis

API (new terminal, project root). Windows cmd:

    set DATABASE_URL=postgresql+psycopg2://cancer:cancer@localhost:5432/cancerdb
    set REDIS_URL=redis://localhost:6379/0
    uvicorn src.api:app --reload

Mac/Linux: use `export` instead of `set`. Docs: http://localhost:8000/docs

UI (another terminal):

    streamlit run app.py

## 3. Run everything in Docker

    python scripts/pin_versions.py      # pins the image to the library versions you trained with
    docker compose up --build

UI: http://localhost:8501   API docs: http://localhost:8000/docs

The model and dataset are copied into the image, so train first. If your Python is not 3.11, set
`PYTHON_VERSION` (the pin script prints the value). If the PyTorch model won the comparison, set
`INSTALL_TORCH=1` before building.

## 4. Run on Kubernetes (minikube)

    docker compose build                          # builds the image breast-cancer-app:1.0
    minikube start
    minikube image load breast-cancer-app:1.0     # for kind: kind load docker-image breast-cancer-app:1.0
    kubectl apply -f k8s/
    kubectl get pods -n cancer --watch            # wait until all pods are Running and Ready
    minikube service ui -n cancer                 # opens the UI in your browser
    kubectl port-forward -n cancer svc/api 8000:8000   # optional: reach the API at localhost:8000

Useful commands:

    kubectl logs -n cancer deploy/api
    kubectl scale -n cancer deploy/api --replicas=3
    kubectl delete -f k8s/                        # remove everything

## 5. ONNX export and benchmark

    python -m src.export_onnx        # writes models/model.onnx
    python -m src.benchmark_onnx     # compares native vs ONNX Runtime, writes models/benchmark.csv

It prints whether both give the same answers (max probability difference, % same class) and the
latency and throughput for batch sizes 1, 32 and 512 on one CPU thread.

Serve the ONNX model from the API (no scikit-learn, XGBoost or PyTorch needed to run it):

    set ONNX_MODEL_PATH=models/model.onnx      (Mac/Linux: export ONNX_MODEL_PATH=models/model.onnx)
    uvicorn src.api:app --reload               # /health now shows "backend": "onnxruntime"

In Docker: `set ONNX_MODEL_PATH=models/model.onnx` before `docker compose up --build`.

## 6. Tests

    pip install -r requirements-dev.txt
    pytest -q

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | /health | status, model name, Redis and database state |
| GET | /features | the 30 expected feature names |
| POST | /predict | one prediction (cached in Redis, logged in PostgreSQL) |
| POST | /predict/batch | many predictions at once |
| GET | /predictions?limit=10 | latest logged predictions |
