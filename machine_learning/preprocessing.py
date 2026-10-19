
import numpy as np


def preprocess_landmarks(landmarks):
    """
    Convert 21 hand landmarks into 63 normalized features.

    Input: 21 landmarks with x, y, z coordinates.
    Output: NumPy array of shape (63,).
    """
    if len(landmarks) != 21:
        raise ValueError("Exactly 21 landmarks are required.")

    points = np.array(
        [[p.x, p.y, p.z] for p in landmarks],
        dtype=np.float32
    )

    # Move wrist landmark to origin
    points = points - points[0]

    # Normalize by maximum distance from wrist
    scale = np.max(np.linalg.norm(points, axis=1))

    if scale > 0:
        points = points / scale

    return points.flatten()
