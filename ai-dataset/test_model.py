from pathlib import Path
import tensorflow as tf
import json

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Model directory
MODEL_DIR = BASE_DIR / "models"

# Load trained CNN model
model = tf.keras.models.load_model(
    MODEL_DIR / "best_gesture_cnn.keras"
)

# Load gesture class names
with open(
    MODEL_DIR / "class_names.json",
    "r",
    encoding="utf-8"
) as f:
    classes = json.load(f)

print("\n==============================")
print("CNN MODEL LOADING TEST")
print("==============================")

print("Model loaded successfully!")
print("Gesture classes:", classes)
print("Input shape:", model.input_shape)
print("Output shape:", model.output_shape)

model.summary()