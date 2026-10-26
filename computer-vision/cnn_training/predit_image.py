
from collections import deque
from pathlib import Path

import cv2
import mediapipe as mp
import torch
import torch.nn.functional as F
from PIL import Image
from rembg import new_session, remove
from torchvision import transforms

from model_training import GestureCNN

# Model location
MODEL_PATH = (
    Path(__file__).resolve().parent
    / "output"
    / "gesture_cnn.pth"
)

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

# Load trained model
checkpoint = torch.load(
    MODEL_PATH,
    map_location=device,
    weights_only=True
)

class_to_idx = checkpoint["class_to_idx"]
idx_to_class = {
    index: name
    for name, index in class_to_idx.items()
}

model = GestureCNN(
    num_classes=len(class_to_idx)
).to(device)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model.eval()

image_size = checkpoint.get(
    "image_size", [64, 64]
)

transform = transforms.Compose([
    transforms.Resize(tuple(image_size)),
    transforms.ToTensor(),
])

# Gesture -> Driving command
COMMANDS = {
    "fist": "STOP",
    "palm": "FORWARD",
    "left_dir": "LEFT",
    "right_dir": "RIGHT",
}
if set(class_to_idx) != set(COMMANDS):
    raise ValueError(
        f"Model classes {sorted(class_to_idx)} do not match "
        f"the supported gestures {sorted(COMMANDS)}"
    )

rembg_session = new_session("u2netp")


def prepare_hand_image(rgb_frame, hand_landmarks, session):
    """Match the segmented, centered hand preprocessing used for training."""
    height, width = rgb_frame.shape[:2]
    points = [
        (int(point.x * width), int(point.y * height))
        for point in hand_landmarks.landmark
    ]
    x_values, y_values = zip(*points)
    hand_width = max(x_values) - min(x_values)
    hand_height = max(y_values) - min(y_values)
    crop_padding = int(max(hand_width, hand_height) * 0.2)

    x1 = max(0, min(x_values) - crop_padding)
    y1 = max(0, min(y_values) - crop_padding)
    x2 = min(width, max(x_values) + crop_padding)
    y2 = min(height, max(y_values) + crop_padding)
    if x2 <= x1 or y2 <= y1:
        return None

    hand_crop = Image.fromarray(rgb_frame[y1:y2, x1:x2])
    segmented = remove(hand_crop, session=session).convert("RGBA")
    bbox = segmented.getchannel("A").getbbox()
    if bbox is None:
        return None

    segmented = segmented.crop(bbox)
    target_size = 64
    image_padding = 4
    segmented.thumbnail(
        (target_size - image_padding * 2, target_size - image_padding * 2),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGB", (target_size, target_size), (0, 0, 0))
    offset = (
        (target_size - segmented.width) // 2,
        (target_size - segmented.height) // 2,
    )
    canvas.paste(segmented, offset, segmented.getchannel("A"))
    return canvas


mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    cap.release()
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    hands.close()
    cap.release()
    raise RuntimeError("Cannot open webcam")

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

print("Webcam prediction started")
print("Press Q to quit")
prediction_history = deque(maxlen=5)

try:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Cannot read webcam frame")
            break

        frame = cv2.flip(frame, 1)

        # Center region for hand
        height, width = frame.shape[:2]
        box_size = int(min(height, width) * 0.65)

        x1 = (width - box_size) // 2
        y1 = (height - box_size) // 2
        x2 = x1 + box_size
        y2 = y1 + box_size

        crop = frame[y1:y2, x1:x2]
        crop = cv2.resize(crop, (200, 200), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

        results = hands.process(rgb)

        if not results.multi_hand_landmarks:
            prediction_history.clear()
            cv2.putText(
                frame,
                "NO HAND - STOP",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )
            cv2.imshow("CNN Gesture Prediction", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            continue

        landmarks = results.multi_hand_landmarks[0]
        image = prepare_hand_image(rgb, landmarks, rembg_session)
        if image is None:
            prediction_history.clear()
            cv2.putText(
                frame,
                "HAND SEGMENTATION FAILED - STOP",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 0, 255),
                2,
            )
            cv2.imshow("CNN Gesture Prediction", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        tensor = transform(image).unsqueeze(0).to(device)

        with torch.inference_mode():
            logits = model(tensor)
            probabilities = F.softmax(logits, dim=1)[0].cpu()
            prediction_history.append(probabilities)
            probabilities = torch.stack(tuple(prediction_history)).mean(dim=0)
            confidence, predicted = probabilities.max(dim=0)

            label = idx_to_class[predicted.item()]
            score = confidence.item()

            # Low confidence -> STOP
            if score < 0.80:
                command = "STOP"
                display_label = "UNCERTAIN"
            else:
                command = COMMANDS.get(label, "STOP")
                display_label = label

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.putText(
            frame,
            f"Gesture: {display_label}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

        cv2.putText(
            frame,
            f"Confidence: {score:.1%}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"Command: {command}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )

        cv2.imshow("CNN Gesture Prediction", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    cap.release()
    hands.close()
    cv2.destroyAllWindows()
