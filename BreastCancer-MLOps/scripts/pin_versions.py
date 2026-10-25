"""Writes requirements-docker.txt with the exact library versions installed on YOUR machine.
Your trained model (best_model.joblib) must be loaded by the same scikit-learn/xgboost
versions that created it, so the Docker image has to use the same versions.

Run from the project root, inside your activated venv:   python scripts/pin_versions.py
"""
import sys
from importlib.metadata import PackageNotFoundError, version

PACKAGES = ["pandas", "numpy", "scikit-learn", "xgboost", "joblib", "streamlit",
            "requests", "fastapi", "uvicorn", "redis", "sqlalchemy", "psycopg2-binary",
            "onnxruntime"]

lines = []
for name in PACKAGES:
    try:
        lines.append(f"{name}=={version(name)}")
    except PackageNotFoundError:
        print(f"WARNING: {name} is not installed here; leaving it unpinned")
        lines.append(name)

with open("requirements-docker.txt", "w") as f:
    f.write("\n".join(lines) + "\n")

print("Wrote requirements-docker.txt")
print(f"Your Python is {sys.version_info.major}.{sys.version_info.minor}. "
      f"If it is not 3.11, build with:  docker compose build --build-arg PYTHON_VERSION="
      f"{sys.version_info.major}.{sys.version_info.minor}")
