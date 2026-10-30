import cv2
import mediapipe as mp
import time
from pathlib import Path

# Gesture labels
GESTURES = {
    ord("1"): "palm",
    ord("2"): "fist",
    ord("3"): "left",
    ord("4"): "right"
}

# Save images in ai-dataset
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_ROOT / "ai-dataset" / "dataset" / "raw"

print("Saving images to:", DATASET_DIR)

for gesture in GESTURES.values():
    (DATASET_DIR / gesture).mkdir(parents=True, exist_ok=True)

# MediaPipe Hand Detection
mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
)

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Cannot open webcam")

current_gesture = "palm"
padding = 30          # extra pixels around the hand
image_size = 224
saved_count = 0


def square_crop(frame, x_min, y_min, x_max, y_max, padding):
    """
    Return (crop, (sx1, sy1, sx2, sy2)) where crop is a SQUARE region
    centered on the hand box. Areas outside the frame are filled with black,
    so the hand is never stretched or cut off.
    """
    h, w = frame.shape[:2]

    cx = (x_min + x_max) // 2
    cy = (y_min + y_max) // 2
    side = max(x_max - x_min, y_max - y_min) + 2 * padding

    # Square box (may extend past the frame)
    sx1 = cx - side // 2
    sy1 = cy - side // 2
    sx2 = sx1 + side
    sy2 = sy1 + side

    # How far the square goes outside the frame
    pad_left = max(0, -sx1)
    pad_top = max(0, -sy1)
    pad_right = max(0, sx2 - w)
    pad_bottom = max(0, sy2 - h)

    # Crop the part that is inside the frame
    crop = frame[
        max(0, sy1):min(h, sy2),
        max(0, sx1):min(w, sx2)
    ]

    # Fill missing area with black so the crop stays exactly square
    if pad_left or pad_top or pad_right or pad_bottom:
        crop = cv2.copyMakeBorder(
            crop,
            pad_top, pad_bottom, pad_left, pad_right,
            cv2.BORDER_CONSTANT,
            value=(0, 0, 0)
        )

    return crop, (sx1, sy1, sx2, sy2)


while True:
    success, frame = cap.read()

    if not success:
        break

    # Mirror webcam for easier control
    frame = cv2.flip(frame, 1)
    height, width = frame.shape[:2]

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    display = frame.copy()
    cropped_hand = None

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]

        x_points = [int(lm.x * width) for lm in hand_landmarks.landmark]
        y_points = [int(lm.y * height) for lm in hand_landmarks.landmark]

        x_min, x_max = min(x_points), max(x_points)
        y_min, y_max = min(y_points), max(y_points)

        if x_max > x_min and y_max > y_min:
            # Square crop (aspect ratio preserved)
            cropped_hand, (sx1, sy1, sx2, sy2) = square_crop(
                frame, x_min, y_min, x_max, y_max, padding
            )

            # Draw the square box on the display
            cv2.rectangle(
                display,
                (sx1, sy1),
                (sx2, sy2),
                (0, 255, 0),
                2
            )

            # Preview exactly what will be saved
            if cropped_hand.size > 0:
                preview = cv2.resize(
                    cropped_hand,
                    (image_size, image_size),
                    interpolation=cv2.INTER_AREA
                )
                cv2.imshow("Hand Crop Preview", preview)

    # Display instructions
    cv2.putText(display, f"Gesture: {current_gesture}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(display, "1:Palm 2:Fist 3:Left 4:Right", (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(display, "S: Save Crop | Q: Quit", (20, 105),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    cv2.imshow("Hand Gesture Dataset Collection", display)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    if key in GESTURES:
        current_gesture = GESTURES[key]
        print("Selected:", current_gesture)

    if key == ord("s"):
        if cropped_hand is not None and cropped_hand.size > 0:
            saved_image = cv2.resize(
                cropped_hand,
                (image_size, image_size),
                interpolation=cv2.INTER_AREA
            )

            filename = DATASET_DIR / current_gesture / f"{time.time_ns()}.jpg"

            cv2.imwrite(str(filename), saved_image)
            saved_count += 1

            print(f"Saved [{saved_count}]: {filename}")
        else:
            print("No hand detected. Image not saved.")

cap.release()
hands.close()
cv2.destroyAllWindows()

print("Total images saved:", saved_count)