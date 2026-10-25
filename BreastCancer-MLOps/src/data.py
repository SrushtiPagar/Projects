"""Data loading and splitting (replaces Steps 1-3 repeated in all 7 scripts)."""
import pandas as pd
from sklearn.model_selection import train_test_split

DATA_PATH = "data/breast_cancer.csv"
TARGET = "target"

# In scikit-learn's built-in breast cancer dataset: 0 = malignant, 1 = benign.
# Check your CSV. If your encoding is the other way round, change this value.
MALIGNANT_LABEL = 0


def load_data(path: str = DATA_PATH):
    df = pd.read_csv(path)
    X = df.drop(TARGET, axis=1)
    y = df[TARGET]
    return X, y


def split_data(X, y, test_size: float = 0.2, seed: int = 42):
    # stratify keeps the malignant/benign ratio the same in train and test
    return train_test_split(X, y, test_size=test_size, random_state=seed, stratify=y)
