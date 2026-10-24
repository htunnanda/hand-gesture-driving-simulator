
from pathlib import Path
import numpy as np
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "dataset_enhanced.npz"
MODEL_PATH = BASE_DIR / "models" / "gesture_model.pkl"


def train_model():

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    # Load dataset
    data = np.load(DATASET_PATH, allow_pickle=False)

    X = data["X"]
    y = data["y"]
    class_names = data["class_names"]

    print("Dataset shape:", X.shape)
    print("Classes:", class_names)

    # Validate dataset
    if X.ndim != 2 or X.shape[1] != 63:
        raise ValueError("Expected X shape (samples, 63)")

    if len(X) != len(y):
        raise ValueError("X and y lengths do not match")

    if not np.isfinite(X).all():
        raise ValueError("Dataset contains NaN or Inf")

    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print("Training samples:", len(X_train))
    print("Testing samples:", len(X_test))

    # Create Random Forest model
    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )

    # Train
    print("\nTraining model...")
    model.fit(X_train, y_train)

    # Evaluate
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    labels = np.arange(len(class_names))

    print("\n========== MODEL RESULTS ==========")
    print(f"Accuracy: {accuracy:.2%}")

    print("\nClassification Report:")
    print(classification_report(
        y_test,
        predictions,
        labels=labels,
        target_names=class_names,
        zero_division=0
    ))

    print("\nConfusion Matrix:")
    print(confusion_matrix(
        y_test,
        predictions,
        labels=labels
    ))

    # Save model
    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(model, MODEL_PATH)

    print("\nModel saved:", MODEL_PATH)


if __name__ == "__main__":
    train_model()
