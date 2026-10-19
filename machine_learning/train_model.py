
from pathlib import Path
import numpy as np
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset.npz"
MODEL_PATH = BASE_DIR / "models" / "gesture_model.pkl"


def train_model():
    if not DATASET_PATH.exists():
        print("Dataset not found.")
        print("Training pipeline is ready.")
        print("Collect dataset before training.")
        return

    data = np.load(DATASET_PATH, allow_pickle=False)
    X = data["X"]
    y = data["y"]

    if X.ndim != 2 or X.shape[1] != 63:
        raise ValueError("Expected X shape: (samples, 63)")

    if len(X) != len(y):
        raise ValueError("X and y must have equal lengths.")

    if len(np.unique(y)) < 2:
        raise ValueError("At least 2 gesture classes required.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2,
        random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"Accuracy: {accuracy:.2%}")
    print(f"Model saved: {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
