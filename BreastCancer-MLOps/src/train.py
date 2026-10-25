"""Train all models, compare them, and save the best one.
Run from the project root:  python -m src.train
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_validate

from src.data import load_data, split_data
from src.models import get_models
from src.evaluate import evaluate, malignant_recall, malignant_auc

OUT_DIR = Path("models")


def main():
    X, y = load_data()
    X_train, X_test, y_train, y_test = split_data(X, y)
    print(f"Dataset: {X.shape}, train={len(X_train)}, test={len(X_test)}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    rows, fitted = [], {}

    for name, model in get_models().items():
        print(f"Training {name} ...")
        scoring = {"recall": malignant_recall}
        if hasattr(model, "predict_proba"):
            scoring["roc_auc"] = malignant_auc
        cv_res = cross_validate(model, X_train, y_train, cv=cv, scoring=scoring)

        model.fit(X_train, y_train)
        fitted[name] = model
        row = {"model": name, **evaluate(model, X_test, y_test)}
        row["cv_recall"] = cv_res["test_recall"].mean()
        row["cv_auc"] = cv_res["test_roc_auc"].mean() if "test_roc_auc" in cv_res else np.nan
        rows.append(row)

    results = pd.DataFrame(rows).round(4)
    # Pick the winner using cross-validation on the training data, not the test set
    results = results.sort_values(["cv_recall", "cv_auc"], ascending=False, na_position="last")
    print("\n", results.to_string(index=False))

    OUT_DIR.mkdir(exist_ok=True)
    results.to_csv(OUT_DIR / "results.csv", index=False)

    # The API needs probabilities, so models without predict_proba (hard voting) cannot be served
    servable = results[results["cv_auc"].notna()]
    best_name = servable.iloc[0]["model"]
    joblib.dump(fitted[best_name], OUT_DIR / "best_model.joblib")
    (OUT_DIR / "metadata.json").write_text(json.dumps(
        {"best_model": best_name, "features": list(X.columns)}, indent=2))
    print(f"\nBest servable model by CV recall: {best_name} -> saved to {OUT_DIR}/best_model.joblib")


if __name__ == "__main__":
    main()
