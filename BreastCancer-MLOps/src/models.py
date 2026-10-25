"""All models in one place. Each is a Pipeline (scaler + model), so the scaler is
fitted on training data only and saved together with the model."""
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import (RandomForestClassifier, BaggingClassifier,
                              AdaBoostClassifier, VotingClassifier)
from xgboost import XGBClassifier

from src.torch_model import TorchMLPClassifier

SEED = 42


def _pipe(model):
    return Pipeline([("scaler", StandardScaler()), ("model", model)])


def _voting_members():
    return [
        ("logistic", LogisticRegression(max_iter=1000)),
        ("decision_tree", DecisionTreeClassifier(random_state=SEED)),
        ("knn", KNeighborsClassifier(n_neighbors=5)),
    ]


def get_models():
    return {
        # --- your original 7 approaches ---
        "DecisionTree": _pipe(DecisionTreeClassifier(random_state=SEED)),
        "Logistic": _pipe(LogisticRegression(max_iter=1000)),
        "RandomForest": _pipe(RandomForestClassifier(n_estimators=100, random_state=SEED)),
        "Bagging": _pipe(BaggingClassifier(
            estimator=DecisionTreeClassifier(random_state=SEED),
            n_estimators=10, random_state=SEED)),
        "AdaBoost": _pipe(AdaBoostClassifier(n_estimators=50, learning_rate=1.0, random_state=SEED)),
        "Voting_Hard": _pipe(VotingClassifier(_voting_members(), voting="hard")),
        "Voting_Soft": _pipe(VotingClassifier(_voting_members(), voting="soft")),
        # --- new: closes the XGBoost and PyTorch gaps ---
        "XGBoost": _pipe(XGBClassifier(
            n_estimators=200, max_depth=3, learning_rate=0.1,
            eval_metric="logloss", random_state=SEED)),
        "PyTorch_MLP": _pipe(TorchMLPClassifier(epochs=100, random_state=SEED)),
        "Voting_Soft_XGB": _pipe(VotingClassifier(
            _voting_members() + [("xgboost", XGBClassifier(
                n_estimators=200, max_depth=3, learning_rate=0.1,
                eval_metric="logloss", random_state=SEED))],
            voting="soft")),
    }
