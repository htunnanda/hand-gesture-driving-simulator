
from types import SimpleNamespace
from preprocessing import preprocess_landmarks

# Create 21 sample landmarks
landmarks = [
    SimpleNamespace(
        x=i * 0.01,
        y=i * 0.02,
        z=i * 0.005
    )
    for i in range(21)
]

result = preprocess_landmarks(landmarks)

print("Output shape:", result.shape)
print("Preprocessing successful!")
