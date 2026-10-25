
from pathlib import Path
from collections import deque, Counter

import cv2
import joblib
import mediapipe as mp
import numpy as np

from preprocessing import preprocess_landmarks

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "gesture_model.pkl"

CLASS_NAMES = ["fist", "left_dir", "palm", "right_dir"]

# Load trained model
model = joblib.load(MODEL_PATH)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

history = deque(maxlen=5)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Cannot open webcam")

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
) as hands:

    while True:
        success, frame = cap.read()

        if not success:
            break

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        gesture = "No Hand"
        confidence = 0.0

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]

            features = preprocess_landmarks(
                hand.landmark
            ).reshape(1, 63)

            prediction = int(model.predict(features)[0])

            probabilities = model.predict_proba(features)[0]
            confidence = float(
                np.max(probabilities)
            )

            if confidence >= 0.7:
                history.append(CLASS_NAMES[prediction])

            if history:
                gesture = Counter(history).most_common(1)[0][0]

            mp_draw.draw_landmarks(
                frame,
                hand,
                mp_hands.HAND_CONNECTIONS
            )
        else:
            history.clear()

        cv2.putText(
            frame,
            f"Gesture: {gesture}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Confidence: {confidence:.2f}",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2
        )

        cv2.imshow("Hand Gesture Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
