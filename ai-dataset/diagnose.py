from pathlib import Path
import tensorflow as tf
import numpy as np
import json

from sklearn.metrics import (
    classification_report,
    confusion_matrix
)

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models"

DATASET_DIR = BASE_DIR / "ai-dataset" / "processed-dataset"

model = tf.keras.models.load_model(
    MODEL_DIR / "best_gesture_cnn.keras"
)

with open(MODEL_DIR / "class_names.json") as f:
    classes = json.load(f)

X = []
y = []

for idx, gesture in enumerate(classes):

    folder = DATASET_DIR / gesture

    if not folder.exists():
        raise FileNotFoundError(folder)

    for image_path in sorted(folder.iterdir()):

        if image_path.suffix.lower() not in {
            ".jpg", ".jpeg", ".png"
        }:
            continue

        image = tf.keras.utils.load_img(
            image_path,
            target_size=(64, 64),
            color_mode="rgb"
        )

        image = tf.keras.utils.img_to_array(image)

        X.append(image)
        y.append(idx)

X = np.array(X, dtype=np.float32)
y = np.array(y)

predictions = model.predict(X, verbose=0)

predicted_labels = np.argmax(predictions, axis=1)

print("\nCLASSIFICATION REPORT")

print(classification_report(
    y,
    predicted_labels,
    target_names=classes,
    zero_division=0
))

print("\nCONFUSION MATRIX")

print(confusion_matrix(
    y,
    predicted_labels
))