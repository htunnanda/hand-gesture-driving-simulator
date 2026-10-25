
import cv2
import time
from pathlib import Path

GESTURES = {
    ord("1"): "palm",
    ord("2"): "fist",
    ord("3"): "left",
    ord("4"): "right"
}

BASE = Path("dataset/raw")

for gesture in GESTURES.values():
    (BASE / gesture).mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Webcam not found")

current = "palm"

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    if not ret:
        break

    display = frame.copy()

    cv2.putText(
        display,
        f"Gesture: {current}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        display,
        "1:Palm 2:Fist 3:Left 4:Right S:Save Q:Quit",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    cv2.imshow("Dataset Collection", display)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    if key in GESTURES:
        current = GESTURES[key]

    if key == ord("s"):
        filename = BASE / current / f"{time.time_ns()}.jpg"
        cv2.imwrite(str(filename), frame)
        print(f"Saved: {filename}")

cap.release()
cv2.destroyAllWindows()