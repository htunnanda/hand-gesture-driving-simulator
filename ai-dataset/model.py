
from pathlib import Path
import json
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from tensorflow.keras import layers, models

# =====================================
# 1. CONFIGURATION
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "ai-dataset" / "processed-dataset"
MODEL_DIR = BASE_DIR / "models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

CLASSES = ["fist", "left_dir", "palm", "right_dir"]

IMAGE_SIZE = 64
BATCH_SIZE = 32
EPOCHS = 30
SEED = 42

tf.keras.utils.set_random_seed(SEED)

# =====================================
# 2. LOAD DATASET
# =====================================

def load_dataset():

    images = []
    labels = []

    for idx, gesture in enumerate(CLASSES):

        folder = DATASET_DIR / gesture

        if not folder.exists():
            raise FileNotFoundError(
                f"Folder not found: {folder}"
            )

        count = 0

        for image_path in sorted(folder.iterdir()):

            if image_path.suffix.lower() not in {
                ".jpg", ".jpeg", ".png", ".bmp"
            }:
                continue

            try:
                image = tf.keras.utils.load_img(
                    image_path,
                    target_size=(IMAGE_SIZE, IMAGE_SIZE),
                    color_mode="rgb"
                )

                image = tf.keras.utils.img_to_array(image)

                images.append(image)
                labels.append(idx)
                count += 1

            except Exception as e:
                print(f"Skipped {image_path.name}: {e}")

        print(f"{gesture}: {count} images")

    X = np.array(images, dtype=np.float32)
    y = np.array(labels, dtype=np.int32)

    if len(X) == 0:
        raise ValueError("No images found!")

    return X, y

X, y = load_dataset()

print("\nDataset shape:", X.shape)
print("Labels shape:", y.shape)

# =====================================
# 3. TRAIN / VALIDATION / TEST SPLIT
# =====================================

# 70% Train, 30% temporary
X_train, X_temp, y_train, y_temp = train_test_split(
    X,
    y,
    test_size=0.30,
    random_state=SEED,
    stratify=y
)

# 15% Validation, 15% Test
X_val, X_test, y_val, y_test = train_test_split(
    X_temp,
    y_temp,
    test_size=0.50,
    random_state=SEED,
    stratify=y_temp
)

print("\nTrain:", len(X_train))
print("Validation:", len(X_val))
print("Test:", len(X_test))

# =====================================
# 4. DATA AUGMENTATION
# =====================================

data_augmentation = tf.keras.Sequential([
    layers.RandomRotation(0.04),
    layers.RandomTranslation(0.05, 0.05),
    layers.RandomZoom(0.10),
], name="data_augmentation")

# No horizontal flip:
# left_dir and right_dir must remain distinct.

# =====================================
# 5. CNN MODEL
# =====================================

model = models.Sequential([

    layers.Input(shape=(64, 64, 3)),

    # Training-only augmentation
    data_augmentation,

    # Normalize pixels to 0-1
    layers.Rescaling(1.0 / 255),

    # CNN Block 1
    layers.Conv2D(
        32, (3, 3),
        activation="relu",
        padding="same"
    ),
    layers.MaxPooling2D((2, 2)),

    # CNN Block 2
    layers.Conv2D(
        64, (3, 3),
        activation="relu",
        padding="same"
    ),
    layers.MaxPooling2D((2, 2)),

    # CNN Block 3
    layers.Conv2D(
        128, (3, 3),
        activation="relu",
        padding="same"
    ),
    layers.MaxPooling2D((2, 2)),

    # Classification layers
    layers.Flatten(),

    layers.Dense(128, activation="relu"),
    layers.Dropout(0.4),

    layers.Dense(
        len(CLASSES),
        activation="softmax"
    )
])

# =====================================
# 6. COMPILE MODEL
# =====================================

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.001
    ),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# =====================================
# 7. CALLBACKS
# =====================================

callbacks = [

    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=6,
        restore_best_weights=True
    ),

    tf.keras.callbacks.ModelCheckpoint(
        str(MODEL_DIR / "best_gesture_cnn.keras"),
        monitor="val_loss",
        save_best_only=True
    ),

    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=3,
        min_lr=0.00001
    )
]

# =====================================
# 8. TRAIN MODEL
# =====================================

history = model.fit(
    X_train,
    y_train,
    validation_data=(X_val, y_val),
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    callbacks=callbacks
)

# =====================================
# 9. EVALUATE MODEL
# =====================================

test_loss, test_accuracy = model.evaluate(
    X_test,
    y_test,
    verbose=0
)

print("\n==============================")
print("MODEL EVALUATION")
print("==============================")

print(f"Test Loss: {test_loss:.4f}")
print(f"Test Accuracy: {test_accuracy * 100:.2f}%")

predictions = model.predict(X_test, verbose=0)
predicted_labels = np.argmax(predictions, axis=1)

print("\nClassification Report:")

print(classification_report(
    y_test,
    predicted_labels,
    labels=list(range(len(CLASSES))),
    target_names=CLASSES,
    zero_division=0
))

print("\nConfusion Matrix:")
print(confusion_matrix(
    y_test,
    predicted_labels,
    labels=list(range(len(CLASSES)))
))

# =====================================
# 10. SAVE MODEL AND CLASS LABELS
# =====================================

model.save(MODEL_DIR / "gesture_cnn.keras")

with open(
    MODEL_DIR / "class_names.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(CLASSES, f, indent=4)

print("\nModel saved successfully!")

# =====================================
# 11. TRAINING GRAPHS
# =====================================

plt.figure(figsize=(8, 5))

plt.plot(
    history.history["accuracy"],
    label="Training Accuracy"
)

plt.plot(
    history.history["val_accuracy"],
    label="Validation Accuracy"
)

plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.title("CNN Training Accuracy")
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(MODEL_DIR / "training_accuracy.png")
plt.show()

plt.figure(figsize=(8, 5))

plt.plot(
    history.history["loss"],
    label="Training Loss"
)

plt.plot(
    history.history["val_loss"],
    label="Validation Loss"
)

plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("CNN Training Loss")
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig(MODEL_DIR / "training_loss.png")
plt.show()