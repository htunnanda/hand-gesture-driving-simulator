
from pathlib import Path
import cv2
import mediapipe as mp
import numpy as np

from preprocessing import preprocess_landmarks

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "ai-dataset" / "processed-dataset"
OUTPUT_PATH = Path(__file__).resolve().parent / "dataset_enhanced.npz"
SKIPPED_PATH = Path(__file__).resolve().parent / "skipped_images.txt"

GESTURES = ["fist", "left_dir", "palm", "right_dir"]

X = []
y = []
skipped_files = []

mp_hands = mp.solutions.hands


def detect_landmarks(image, hands):
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        return result.multi_hand_landmarks[0].landmark

    return None


def enhance_image(image):
    # Improve local contrast
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    l = clahe.apply(l)
    enhanced = cv2.merge((l, a, b))

    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def add_padding(image):
    h, w = image.shape[:2]
    pad = max(20, int(max(h, w) * 0.25))

    return cv2.copyMakeBorder(
        image,
        pad, pad, pad, pad,
        cv2.BORDER_CONSTANT,
        value=(0, 0, 0)
    )


def extract_with_retry(image, hands):
    # Attempt 1: Original image
    landmarks = detect_landmarks(image, hands)
    if landmarks is not None:
        return landmarks, "original"

    # Attempt 2: Enhanced image
    enhanced = enhance_image(image)
    landmarks = detect_landmarks(enhanced, hands)
    if landmarks is not None:
        return landmarks, "enhanced"

    # Attempt 3: Padding
    padded = add_padding(image)
    landmarks = detect_landmarks(padded, hands)
    if landmarks is not None:
        return landmarks, "padded"

    # Attempt 4: Enhanced + Padding
    enhanced_padded = add_padding(enhanced)
    landmarks = detect_landmarks(enhanced_padded, hands)
    if landmarks is not None:
        return landmarks, "enhanced_padded"

    return None, "failed"


with mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=1,
    min_detection_confidence=0.5
) as hands:

    for label, gesture in enumerate(GESTURES):
        folder = DATASET_DIR / gesture

        count = 0
        skipped = 0
        retry_success = 0

        if not folder.exists():
            raise FileNotFoundError(
                f"Dataset folder not found: {folder}"
            )

        for image_path in sorted(folder.iterdir()):
            if image_path.suffix.lower() not in [
                ".jpg", ".jpeg", ".png"
            ]:
                continue

            image = cv2.imread(str(image_path))

            if image is None:
                skipped += 1
                skipped_files.append(str(image_path))
                continue

            landmarks, method = extract_with_retry(
                image, hands
            )

            if landmarks is None:
                skipped += 1
                skipped_files.append(str(image_path))
                continue

            features = preprocess_landmarks(landmarks)

            X.append(features)
            y.append(label)
            count += 1

            if method != "original":
                retry_success += 1

        print(f"\nGesture: {gesture}")
        print(f"Extracted: {count}")
        print(f"Recovered by retry: {retry_success}")
        print(f"Skipped: {skipped}")


if not X:
    raise RuntimeError("No landmarks extracted.")

X = np.array(X, dtype=np.float32)
y = np.array(y, dtype=np.int64)

np.savez(
    OUTPUT_PATH,
    X=X,
    y=y,
    class_names=np.array(GESTURES)
)

SKIPPED_PATH.write_text(
    "\n".join(skipped_files),
    encoding="utf-8"
)

print("\n========== FINAL RESULT ==========")
print("Dataset saved:", OUTPUT_PATH)
print("Features shape:", X.shape)
print("Labels shape:", y.shape)
print("Total skipped:", len(skipped_files))
print("Skipped list:", SKIPPED_PATH)
