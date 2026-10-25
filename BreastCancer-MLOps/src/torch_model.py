"""A small PyTorch MLP that behaves like a scikit-learn classifier,
so it can sit in the same Pipeline / comparison as the other models."""
import numpy as np
import torch
from torch import nn
from sklearn.base import BaseEstimator, ClassifierMixin


class TorchMLPClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self, hidden1=64, hidden2=32, epochs=100, lr=1e-3,
                 batch_size=32, random_state=42):
        self.hidden1 = hidden1
        self.hidden2 = hidden2
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.random_state = random_state

    def _build(self, n_features):
        return nn.Sequential(
            nn.Linear(n_features, self.hidden1), nn.ReLU(),
            nn.Linear(self.hidden1, self.hidden2), nn.ReLU(),
            nn.Linear(self.hidden2, 1),
        )

    def fit(self, X, y):
        torch.manual_seed(self.random_state)
        X = torch.tensor(np.asarray(X), dtype=torch.float32)
        self.classes_ = np.unique(np.asarray(y))
        y01 = (np.asarray(y) == self.classes_[1]).astype(np.float32)
        y01 = torch.tensor(y01).unsqueeze(1)

        self.net_ = self._build(X.shape[1])
        optimizer = torch.optim.Adam(self.net_.parameters(), lr=self.lr)
        loss_fn = nn.BCEWithLogitsLoss()

        self.net_.train()
        for _ in range(self.epochs):
            perm = torch.randperm(X.shape[0])
            for i in range(0, X.shape[0], self.batch_size):
                idx = perm[i:i + self.batch_size]
                optimizer.zero_grad()
                loss = loss_fn(self.net_(X[idx]), y01[idx])
                loss.backward()
                optimizer.step()
        return self

    def predict_proba(self, X):
        X = torch.tensor(np.asarray(X), dtype=torch.float32)
        self.net_.eval()
        with torch.no_grad():
            p1 = torch.sigmoid(self.net_(X)).numpy().ravel()
        return np.column_stack([1 - p1, p1])

    def predict(self, X):
        p1 = self.predict_proba(X)[:, 1]
        return self.classes_[(p1 >= 0.5).astype(int)]
