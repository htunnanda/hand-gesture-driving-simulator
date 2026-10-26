
import cv2
import json
import time
import threading
import numpy as np
import tensorflow as tf
import mediapipe as mp

from pathlib import Path
from PIL import Image
from rembg import remove, new_session

# =====================================
# CONFIGURATION
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

IMAGE_SIZE = 64
CONFIDENCE_THRESHOLD = 0.70

# Run expensive prediction less frequently
PREDICTION_INTERVAL = 0.3

# =====================================
# LOAD MODELS
# =====================================

print("Loading CNN model...")

model = tf.keras.models.load_model(
    MODEL_DIR / "best_gesture_cnn.keras"
)

with open(MODEL_DIR / "class_names.json", encoding="utf-8") as f:
    classes = json.load(f)

print("Loading background removal model...")
session = new_session("u2net")

print("Loading MediaPipe hand detector...")

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path=str(MODEL_DIR / "hand_landmarker.task")
    ),
    running_mode=VisionRunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.6,
    min_tracking_confidence=0.5
)

detector = HandLandmarker.create_from_options(options)

# =====================================
# SHARED PREDICTION STATE
# =====================================

prediction_lock = threading.Lock()

latest_gesture = "No hand"
latest_confidence = 0.0

worker_busy = False

# =====================================
# PREPROCESSING
# =====================================

def preprocess_hand(roi):

    image = Image.fromarray(
        cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
    )

    hand = remove(
        image,
        session=session
    ).convert("RGBA")

    bbox = hand.getchannel("A").getbbox()

    if bbox is None:
        return None

    hand = hand.crop(bbox)

    hand.thumbnail(
        (56, 56),
        Image.Resampling.LANCZOS
    )

    canvas = Image.new(
        "RGB",
        (IMAGE_SIZE, IMAGE_SIZE),
        (0, 0, 0)
    )

    x = (IMAGE_SIZE - hand.width) // 2
    y = (IMAGE_SIZE - hand.height) // 2

    canvas.paste(
        hand,
        (x, y),
        hand.getchannel("A")
    )

    return np.array(canvas, dtype=np.float32)

# =====================================
# BACKGROUND PREDICTION WORKER
# =====================================

def prediction_worker(roi):

    global latest_gesture
    global latest_confidence
    global worker_busy

    try:
        processed = preprocess_hand(roi)

        if processed is None:
            return

        input_image = np.expand_dims(
            processed,
            axis=0
        )

        predictions = model(
            input_image,
            training=False
        ).numpy()[0]

        index = int(np.argmax(predictions))
        confidence = float(predictions[index])

        gesture = (
            classes[index]
            if confidence >= CONFIDENCE_THRESHOLD
            else "Unknown"
        )

        with prediction_lock:
            latest_gesture = gesture
            latest_confidence = confidence

    except Exception as e:
        print("Prediction error:", e)

    finally:
        with prediction_lock:
            worker_busy = False

# =====================================
# WEBCAM
# =====================================

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    raise RuntimeError("Cannot open webcam")

print("Real-time recognition started. Press Q to quit.")

last_prediction_time = 0
start_time = time.perf_counter()
frame_count = 0
fps = 0.0
last_seen = 0.0

try:
    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame = cv2.flip(frame, 1)

        height, width = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=np.ascontiguousarray(rgb)
        )

        timestamp_ms = int(time.monotonic() * 1000)

        result = detector.detect_for_video(
            mp_image,
            timestamp_ms
        )

        if result.hand_landmarks:

            last_seen = time.monotonic()

            landmarks = result.hand_landmarks[0]

            xs = [int(lm.x * width) for lm in landmarks]
            ys = [int(lm.y * height) for lm in landmarks]

            padding = 30

            x1 = max(0, min(xs) - padding)
            y1 = max(0, min(ys) - padding)
            x2 = min(width, max(xs) + padding)
            y2 = min(height, max(ys) + padding)

            # Auto-following hand rectangle
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            now = time.monotonic()

            with prediction_lock:
                can_predict = not worker_busy

                if (
                    can_predict
                    and now - last_prediction_time >= PREDICTION_INTERVAL
                    and x2 > x1
                    and y2 > y1
                ):
                    worker_busy = True
                    launch_worker = True
                else:
                    launch_worker = False

            if launch_worker:

                roi = frame[y1:y2, x1:x2].copy()

                threading.Thread(
                    target=prediction_worker,
                    args=(roi,),
                    daemon=True
                ).start()

                last_prediction_time = now

        else:
            # Clear stale prediction when hand disappears
            if time.monotonic() - last_seen > 0.5:
                with prediction_lock:
                    latest_gesture = "No hand"
                    latest_confidence = 0.0

        with prediction_lock:
            gesture = latest_gesture
            confidence = latest_confidence

        cv2.putText(
            frame,
            f"Gesture: {gesture} ({confidence:.2f})",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        # FPS counter
        frame_count += 1
        elapsed = time.perf_counter() - start_time

        if elapsed >= 1.0:
            fps = frame_count / elapsed
            frame_count = 0
            start_time = time.perf_counter()

        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )

        cv2.imshow(
            "Hand Gesture Recognition",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    detector.close()
    cv2.destroyAllWindows()