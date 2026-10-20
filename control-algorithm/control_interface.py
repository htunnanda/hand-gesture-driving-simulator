from dataclasses import dataclass
from enum import Enum

class Lane(Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"

class TrackingStatus(Enum):
    VALID = "VALID"
    LOST = "LOST"

class SwipeState(Enum):
    READY = "READY"
    SWIPE_DETECTED = "SWIPE_DETECTED"
    LANE_CHANGE = "LANE_CHANGE"
    WAIT_FOR_RESET = "WAIT_FOR_RESET"        

class GameState(Enum):
    CALIBRATING = "CALIBRATING"
    WAITING_FOR_FIST = "WAITING_FOR_FIST"
    PLAYING = "PLAYING"
    STOPPED = "STOPPED"
    GAME_OVER = "GAME_OVER"

@dataclass
class TrackingInput:
    detected: bool
    landmarks: list[list[float]]
    hand_x: float
    timestamp: float
    tracking_status: TrackingStatus

@dataclass
class InferenceInput:
    gesture: str
    confidence: float
    valid: bool
    timestamp: float

@dataclass
class ControlCommand:
    lane: Lane
    throttle: float
    stop: bool
    valid: bool
    timestamp: float
    
                    