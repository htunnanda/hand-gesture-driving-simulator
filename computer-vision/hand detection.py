import cv2
from matplotlib import text
import mediapipe as mp 
import numpy as np 
import time
# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5
)
#open the webcam
cap = cv2.VideoCapture(0)
def prepare_fist_ready_data(hand_image,hand_landmarks):
    if hand_image is None or hand_image.size == 0:
        return None, None
    # extract 21 hand landmarks
    coordinates = np.array(
        [[point.x, point.y, point.z] for point in hand_landmarks.landmark],
        dtype=np.float32,
    )
    if coordinates.shape != (21, 3):
        return None, None
    #prepare the data for fist ready detection
    fist_ready_data = {"image": hand_image.copy(),"coordinates": coordinates}
    return fist_ready_data, coordinates
previous_time = time.perf_counter()

while True:
    success, frame = cap.read()

    if not success:
        print("Failed to capture camera frame")
        break

    # flip the frame horizontally for a later selfie-view display
    frame = cv2.flip(frame, 1)

    # Convert the image from BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect hands in the image
    start_time = time.perf_counter()
    results = hands.process(rgb_frame)

    processing_time = (time.perf_counter() - start_time)*1000
    

    

      
    fist_ready_data = None
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
            )
            

            # get hand bounding box
            height, width, _ = frame.shape
            x_values = [int(point.x * width) for point in hand_landmarks.landmark]
            y_values = [int(point.y * height) for point in hand_landmarks.landmark]
            x_min, x_max = min(x_values), max(x_values)
            y_min, y_max = min(y_values), max(y_values)
            x_min = max(0, x_min - 30)
            y_min = max(0, y_min - 30)
            x_max = min(width, x_max + 30)
            y_max = min(height, y_max + 30)

            # crop the hand image
            hand_image = frame[y_min:y_max, x_min:x_max]

            if hand_image.size > 0:
                print("Hand detected")
                cv2.imshow("Hand calibration", hand_image)
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                cv2.putText(frame, "Hand Detected", (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            else:
                #clear the old hand image if no hand is detected
                print("No hand detected")
            fist_ready_data = prepare_fist_ready_data(hand_image, hand_landmarks)
    if fist_ready_data is not None:
        print("Fist ready data prepared")
    else:
        blank_image = frame.copy()
        blank_image[:] = 0
        cv2.imshow("Hand calibration", blank_image) 

        #calculate and display FPS
    current_time = time.perf_counter()

    elapsed_time = current_time - previous_time
    fps = 1 / elapsed_time if elapsed_time > 0 else 0
    previous_time = current_time
    #display FPS on the frame
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    #display processing time on the frame
    cv2.putText(frame, f"Processing time: {processing_time:.1f} ms", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Display the webcam frame
    cv2.imshow("Hand calibration camera", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release the webcam and close windows
cap.release()
hands.close()
cv2.destroyAllWindows()
