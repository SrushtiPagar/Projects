"""Metrics that matter for cancer detection: recall on the MALIGNANT class first."""
import numpy as np
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, confusion_matrix)
from src.data import MALIGNANT_LABEL


def malignant_recall(estimator, X, y):
    """Scorer usable in cross_validate."""
    return recall_score(y, estimator.predict(X), pos_label=MALIGNANT_LABEL)


def malignant_auc(estimator, X, y):
    """Scorer usable in cross_validate (needs predict_proba)."""
    idx = list(estimator.classes_).index(MALIGNANT_LABEL)
    proba = estimator.predict_proba(X)[:, idx]
    return roc_auc_score((np.asarray(y) == MALIGNANT_LABEL).astype(int), proba)


def evaluate(model, X_test, y_test):
    y_pred = model.predict(X_test)
    result = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, pos_label=MALIGNANT_LABEL),
        "recall": recall_score(y_test, y_pred, pos_label=MALIGNANT_LABEL),
        "f1": f1_score(y_test, y_pred, pos_label=MALIGNANT_LABEL),
        "roc_auc": malignant_auc(model, X_test, y_test) if hasattr(model, "predict_proba") else np.nan,
    }
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[1 - MALIGNANT_LABEL, MALIGNANT_LABEL]).ravel()
    result["missed_malignant"] = int(fn)   # the dangerous mistake
    result["false_alarms"] = int(fp)
    return result
