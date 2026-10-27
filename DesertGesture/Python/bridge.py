"""Local gesture transport. Camera worker cannot stall the heartbeat sender."""
import argparse
from collections import deque
import json
import socket
import threading
import time
import uuid
from pathlib import Path

LABELS = {0: 'FIST', 1: 'LEFT', 2: 'PALM', 3: 'RIGHT'}
ALIASES = {'LEFT_DIR': 'LEFT', 'RIGHT_DIR': 'RIGHT', 'OPEN_PALM': 'PALM'}


def normalize(label):
    text = str(label).upper()
    text = LABELS.get(int(text), 'UNKNOWN') if text.isdigit() else ALIASES.get(text, text)
    return text if text in (*LABELS.values(), 'UNKNOWN') else 'UNKNOWN'


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = dict(gesture='UNKNOWN', confidence=0.0, camera='STARTING',
                         model='STARTING', detail='Initializing', frame_time=0.0)

    def update(self, **values):
        with self.lock:
            self.data.update(values)

    def snapshot(self):
        with self.lock:
            data = self.data.copy()
        if time.monotonic() - data.pop('frame_time') > .7:
            data.update(gesture='UNKNOWN', confidence=0.0)
            if data['camera'] == 'ONLINE':
                data.update(camera='STALE', detail='Camera frames stopped')
        return data


class Stabilizer:
    """Require three consecutive predictions; loss of hand clears immediately."""
    def __init__(self):
        self.history = deque(maxlen=3)

    def accept(self, label, confidence):
        label = normalize(label)
        if confidence < .7 or label == 'UNKNOWN':
            self.history.clear()
            return 'UNKNOWN'
        self.history.append(label)
        return label if len(self.history) == 3 and len(set(self.history)) == 1 else 'UNKNOWN'


def camera_worker(args, state, stop):
    cap = hands = None
    cv2 = None
    try:
        import cv2
        import mediapipe as mp
        import joblib
        from machine_learning.preprocessing import preprocess_landmarks
        if not hasattr(mp, 'solutions'):
            raise RuntimeError('Use mediapipe==0.10.21 from requirements.txt')
        model = joblib.load(args.model)
        if getattr(model, 'n_features_in_', None) != 63:
            raise ValueError('Expected the original 63-feature model')
        if {normalize(x) for x in model.classes_} != set(LABELS.values()):
            raise ValueError('Unexpected model classes; check LABELS mapping')
        # Run actual prediction before marking the model available.
        import numpy as np
        model.predict(np.zeros((1, 63), dtype=np.float32))
        state.update(model='ONLINE', detail='Opening webcam')
        cap = cv2.VideoCapture(args.camera)
        if not cap.isOpened():
            raise RuntimeError(f'Cannot open camera {args.camera}; close other camera apps')
        hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=.6,
                                       min_tracking_confidence=.5)
        stable = Stabilizer()
        while not stop.is_set():
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError('Webcam stopped returning frames')
            frame = cv2.flip(frame, 1)
            result = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            label, confidence = 'UNKNOWN', 0.0
            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                features = preprocess_landmarks(hand.landmark).reshape(1, 63)
                probabilities = model.predict_proba(features)[0]
                index = int(np.argmax(probabilities))
                label, confidence = normalize(model.classes_[index]), float(probabilities[index])
                if args.preview:
                    mp.solutions.drawing_utils.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
            label = stable.accept(label, confidence)
            state.update(gesture=label, confidence=confidence, camera='ONLINE',
                         detail='Tracking' if label != 'UNKNOWN' else 'Show a clear hand gesture',
                         frame_time=time.monotonic())
            if args.preview:
                cv2.putText(frame, f'{label}  {confidence:.0%}', (20, 35),
                            cv2.FONT_HERSHEY_SIMPLEX, .8, (80, 255, 220), 2)
                cv2.imshow('Desert Signal - Camera (Q closes bridge)', frame)
                if cv2.waitKey(1) & 255 == ord('q'):
                    stop.set()
    except Exception as exc:
        state.update(gesture='UNKNOWN', confidence=0.0, camera='OFFLINE',
                     model='ERROR' if state.snapshot()['model'] != 'ONLINE' else 'ONLINE', detail=str(exc))
        print(f'[gesture] {exc}', flush=True)
    finally:
        if hands is not None:
            hands.close()
        if cap is not None:
            cap.release()
        if cv2 is not None and args.preview:
            cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, default=Path(__file__).parent / 'machine_learning/models/gesture_model.pkl')
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--port', type=int, default=5055)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--demo', action='store_true', help='Synthetic gesture cycle; no camera or ML dependencies')
    parser.add_argument('--seconds', type=float, default=0, help='Exit after N seconds; 0 runs until Ctrl+C')
    args = parser.parse_args()
    state, stop = State(), threading.Event()
    worker = None
    if not args.demo:
        worker = threading.Thread(target=camera_worker, args=(args, state, stop), daemon=True)
        worker.start()
    session, seq, start = uuid.uuid4().hex, 0, time.monotonic()
    print(f'UDP 127.0.0.1:{args.port} | {"SIMULATED" if args.demo else "WEBCAM"} | Ctrl+C to stop', flush=True)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            while not stop.is_set():
                elapsed = time.monotonic() - start
                if args.seconds and elapsed >= args.seconds:
                    break
                if args.demo:
                    gesture = ('UNKNOWN', 'LEFT', 'UNKNOWN', 'RIGHT', 'PALM', 'FIST')[int(elapsed / 1.5) % 6]
                    state.update(gesture=gesture, confidence=1.0, camera='SIMULATED', model='SIMULATED',
                                 detail='Synthetic transport demo', frame_time=time.monotonic())
                data = dict(v=1, session=session, seq=seq, **state.snapshot())
                sock.sendto(json.dumps(data, allow_nan=False).encode(), ('127.0.0.1', args.port))
                seq += 1
                stop.wait(.05)
        except KeyboardInterrupt:
            pass
        finally:
            stop.set()
            data = dict(v=1, session=session, seq=seq, gesture='UNKNOWN', confidence=0.0,
                        camera='OFFLINE', model='OFFLINE', detail='Bridge stopped')
            sock.sendto(json.dumps(data).encode(), ('127.0.0.1', args.port))
            if worker:
                worker.join(timeout=2)


if __name__ == '__main__':
    main()
