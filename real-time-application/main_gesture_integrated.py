"""Three-lane city driving simulator with RandomForest hand-gesture control."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from enum import Enum, auto
import math
import sys
import random
import threading
import time
from queue import Empty, Queue
from pathlib import Path

import numpy as np
import pygame

# Use exactly the same preprocessing function as the trained RandomForest model.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ML_DIR = PROJECT_ROOT / "machine_learning"
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))
from preprocessing import preprocess_landmarks

CLASS_NAMES = ("fist", "left_dir", "palm", "right_dir")

WINDOW_SIZE = (800, 600)
MIN_WINDOW_SIZE = (400, 300)
TARGET_FPS = 60
ROAD_WIDTH = 480
MIN_SPEED = 0.0
MAX_SPEED = 100.0
SPEED_STEP = 10.0
ACCELERATION_RATE = 24.0
BRAKING_RATE = 20.0
CRUISE_SPEED = 20.0
BOOST_SPEED = 50.0
GESTURE_TIMEOUT_SECONDS = 0.7
LANE_RESPONSE = 12.0
MAX_STEERING_TILT_DEGREES = 8.0
PIXELS_PER_SPEED_UNIT = 3.0
LANE_DASH_HEIGHT = 30
LANE_DASH_GAP = 24
ROADSIDE_OBJECTS_PER_SIDE = 4
TRAFFIC_SPAWN_INTERVAL = 2.5
TRAFFIC_MIN_SPAWN_GAP = 100
TRAFFIC_CAR_WIDTH = 48
TRAFFIC_CAR_HEIGHT = 82
CONTROL_MAX_AGE_SECONDS = 1.0
ROAD_COLOR = (45, 48, 52)
GRASS_COLOR = (78, 88, 96)
GRASS_STRIPE_COLOR = (88, 98, 106)
ROAD_EDGE_COLOR = (230, 234, 236)
LANE_MARK_COLOR = (236, 239, 240)


class Lane(Enum):
    """The three lanes available on the road."""

    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


class GameState(Enum):
    """Explicit states for the driving session."""

    READY = auto()
    RUNNING = auto()
    STOPPED = auto()
    GAME_OVER = auto()
    PAUSED = auto()


# Backward-compatible name used by existing tests and integrations.
GameState.PLAYING = GameState.RUNNING
PLAYING = GameState.RUNNING


class InputMode(Enum):
    KEYBOARD = auto()
    HAND_GESTURE = auto()
    BOTH = auto()


@dataclass(frozen=True)
class GesturePrediction:
    label: str = "UNKNOWN"
    confidence: float = 0.0
    timestamp: float = 0.0


class GameStateManager:
    """Enforce the allowed game-state transitions."""

    _ALLOWED_TRANSITIONS = {
        GameState.READY: {GameState.RUNNING},
        GameState.RUNNING: {GameState.STOPPED, GameState.GAME_OVER, GameState.PAUSED},
        GameState.STOPPED: {GameState.RUNNING, GameState.GAME_OVER, GameState.PAUSED},
        GameState.PAUSED: {GameState.RUNNING, GameState.STOPPED, GameState.GAME_OVER},
        GameState.GAME_OVER: {GameState.READY},
    }

    def __init__(self) -> None:
        self.state = GameState.READY

    def transition_to(self, new_state: GameState) -> bool:
        """Change state only when the transition is valid."""
        if new_state not in self._ALLOWED_TRANSITIONS[self.state]:
            return False
        self.state = new_state
        return True


@dataclass(frozen=True)
class ControlInput:
    """Control command matching the Member 4 -> Member 5 interface."""

    timestamp: float
    lane: Lane | str | None = None
    throttle: float | None = None
    stop: bool | None = None
    valid: bool = True
    hand_lost: bool = False
    camera_error: bool = False


class Road:
    """Draw the road and manage bounded, speed-driven scrolling scenery."""

    def __init__(self, width: int = ROAD_WIDTH) -> None:
        self.width = width
        self.marking_offset = 0.0
        self.texture_offset = 0.0
        self.roadside_positions: list[tuple[bool, float]] = []

    def bounds(self, screen_width: int, screen_height: int) -> pygame.Rect:
        road_width = min(screen_width - 32, max(self.width, screen_width * 0.9))
        road_width = max(1, road_width)
        return pygame.Rect(
            (screen_width - road_width) // 2,
            0,
            road_width,
            screen_height,
        )

    def lane_center(self, lane: Lane, bounds: pygame.Rect) -> float:
        lane_centers = {
            Lane.LEFT: bounds.left + bounds.width / 6,
            Lane.CENTER: bounds.centerx,
            Lane.RIGHT: bounds.left + 5 * bounds.width / 6,
        }
        return lane_centers[lane]

    def update(self, dt: float, speed: float, screen_height: int) -> None:
        """Advance scrolling by elapsed time; zero speed leaves scenery fixed."""
        cycle = LANE_DASH_HEIGHT + LANE_DASH_GAP
        scroll_distance = speed * PIXELS_PER_SPEED_UNIT * dt
        self.marking_offset = (self.marking_offset + scroll_distance) % cycle
        self.texture_offset += scroll_distance

        if not self.roadside_positions:
            spacing = screen_height / ROADSIDE_OBJECTS_PER_SIDE
            self.roadside_positions = [
                (is_right, row * spacing)
                for row in range(ROADSIDE_OBJECTS_PER_SIDE)
                for is_right in (False, True)
            ]

        self.roadside_positions = [
            (is_right, (y + scroll_distance) % screen_height)
            for is_right, y in self.roadside_positions
        ]

    def draw(self, surface: pygame.Surface) -> pygame.Rect:
        screen_width, screen_height = surface.get_size()
        surface.fill(GRASS_COLOR)

        for x in range(0, screen_width, 48):
            pygame.draw.rect(
                surface,
                GRASS_STRIPE_COLOR,
                (x, 0, 20, screen_height),
            )

        bounds = self.bounds(screen_width, screen_height)
        pygame.draw.rect(surface, ROAD_COLOR, bounds)
        pygame.draw.line(
            surface,
            ROAD_EDGE_COLOR,
            (bounds.left, 0),
            (bounds.left, screen_height),
            6,
        )
        pygame.draw.line(
            surface,
            ROAD_EDGE_COLOR,
            (bounds.right, 0),
            (bounds.right, screen_height),
            6,
        )

        center_x = bounds.centerx
        cycle = LANE_DASH_HEIGHT + LANE_DASH_GAP
        y = -self.marking_offset
        while y < screen_height:
            pygame.draw.line(
                surface,
                LANE_MARK_COLOR,
                (center_x, round(y)),
                (center_x, round(y + LANE_DASH_HEIGHT)),
                4,
            )
            y += cycle

        for is_right, y in self.roadside_positions:
            x = bounds.right + 20 if is_right else bounds.left - 20
            pygame.draw.circle(surface, (104, 76, 48), (x, round(y)), 10)
            pygame.draw.circle(surface, (79, 133, 68), (x, round(y) - 4), 8)
        return bounds


class PlayerCar:
    """A rear-view player car with damped lane and steering motion."""

    WIDTH = 82
    HEIGHT = 100
    BOTTOM_MARGIN = 18

    def __init__(self, lane: Lane = Lane.LEFT) -> None:
        self.lane = lane
        self.target_lane = lane
        self.center_x = 0.0
        self._positioned = False
        self._start_lane = lane
        self._is_changing_lanes = False
        self.steering_tilt = 0.0

    @property
    def is_changing_lanes(self) -> bool:
        return self._is_changing_lanes

    def request_lane_change(self, lane: Lane) -> bool:
        """Request a lane one step away from the current target lane."""
        if not isinstance(lane, Lane):
            raise TypeError("lane must be a Lane value")
        if self._is_changing_lanes or lane is self.lane:
            return False

        self._start_lane = self.lane
        self.target_lane = lane
        self.lane = lane
        self._is_changing_lanes = True
        return True

    def move_left(self) -> bool:
        lanes = (Lane.LEFT, Lane.CENTER, Lane.RIGHT)
        index = lanes.index(self.target_lane)
        return index > 0 and self.request_lane_change(lanes[index - 1])

    def move_right(self) -> bool:
        lanes = (Lane.LEFT, Lane.CENTER, Lane.RIGHT)
        index = lanes.index(self.target_lane)
        return index < len(lanes) - 1 and self.request_lane_change(lanes[index + 1])

    def update(self, dt: float, road_bounds: pygame.Rect, road: Road) -> None:
        if not self._positioned:
            self.center_x = road.lane_center(self._start_lane, road_bounds)
            self._positioned = True

        if self._is_changing_lanes or abs(self.steering_tilt) > 0.05:
            target_x = road.lane_center(self.target_lane, road_bounds)
            distance = target_x - self.center_x
            blend = 1.0 - math.exp(-LANE_RESPONSE * max(0.0, dt))
            self.center_x += distance * blend

            desired_tilt = max(
                -MAX_STEERING_TILT_DEGREES,
                min(MAX_STEERING_TILT_DEGREES, distance * 0.025),
            )
            self.steering_tilt += (
                desired_tilt - self.steering_tilt
            ) * (1.0 - math.exp(-10.0 * max(0.0, dt)))

            if abs(distance) < 1.0:
                self.center_x = target_x
                self.lane = self.target_lane
                self._is_changing_lanes = False
            if not self._is_changing_lanes:
                self.steering_tilt *= math.exp(-12.0 * max(0.0, dt))
                if abs(self.steering_tilt) < 0.05:
                    self.steering_tilt = 0.0

        half_width = self.WIDTH / 2
        self.center_x = max(
            road_bounds.left + half_width,
            min(self.center_x, road_bounds.right - half_width),
        )

    def draw(self, surface: pygame.Surface, road_bounds: pygame.Rect) -> None:
        car_rect = self.rect(surface.get_height())
        car_rect.clamp_ip(road_bounds)
        pygame.draw.rect(surface, (190, 52, 48), car_rect, border_radius=9)
        pygame.draw.rect(
            surface,
            (125, 190, 205),
            (car_rect.left + 7, car_rect.top + 13, self.WIDTH - 14, 23),
            border_radius=5,
        )
        pygame.draw.rect(
            surface,
            (45, 48, 54),
            (car_rect.left + 7, car_rect.top + 43, self.WIDTH - 14, 20),
            border_radius=4,
        )
        pygame.draw.rect(
            surface,
            (245, 225, 160),
            (car_rect.left + 5, car_rect.bottom - 8, 8, 4),
            border_radius=2,
        )
        pygame.draw.rect(
            surface,
            (245, 225, 160),
            (car_rect.right - 13, car_rect.bottom - 8, 8, 4),
            border_radius=2,
        )

    def rect(self, screen_height: int) -> pygame.Rect:
        """Return the player's stable, road-positioned collision rectangle."""
        return pygame.Rect(
            round(self.center_x - self.WIDTH / 2),
            screen_height - self.HEIGHT - self.BOTTOM_MARGIN,
            self.WIDTH,
            self.HEIGHT,
        )


class TrafficCar:
    """A simple traffic car located in one lane at a vertical position."""

    WIDTH = TRAFFIC_CAR_WIDTH
    HEIGHT = TRAFFIC_CAR_HEIGHT
    COLORS = (
        (184, 48, 54),       # red
        (180, 184, 188),     # silver
        (232, 235, 238),     # white
        (35, 38, 42),        # black
        (54, 126, 78),       # green
        (123, 73, 154),      # purple
        (226, 190, 62),      # yellow
    )

    def __init__(self, lane: Lane, y: float, color: tuple[int, int, int]) -> None:
        self.lane = lane
        self.y = y
        self.color = color

    def rect(self, road: Road, road_bounds: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(
            round(road.lane_center(self.lane, road_bounds) - self.WIDTH / 2),
            round(self.y),
            self.WIDTH,
            self.HEIGHT,
        )

    def draw(
        self,
        surface: pygame.Surface,
        road: Road,
        road_bounds: pygame.Rect,
    ) -> None:
        car_rect = self.rect(road, road_bounds)
        pygame.draw.rect(surface, self.color, car_rect, border_radius=9)
        pygame.draw.rect(
            surface,
            (125, 190, 205),
            (car_rect.left + 7, car_rect.top + 13, self.WIDTH - 14, 23),
            border_radius=5,
        )
        pygame.draw.rect(
            surface,
            (45, 48, 54),
            (car_rect.left + 7, car_rect.top + 43, self.WIDTH - 14, 20),
            border_radius=4,
        )


class TrafficSpawner:
    """Generate and move traffic independently from collision detection."""

    def __init__(
        self,
        spawn_interval: float = TRAFFIC_SPAWN_INTERVAL,
        minimum_spawn_gap: float = TRAFFIC_MIN_SPAWN_GAP,
        traffic_speed_scale: float = 1.0,
        rng: random.Random | None = None,
    ) -> None:
        if spawn_interval <= 0:
            raise ValueError("spawn_interval must be greater than zero")
        if traffic_speed_scale <= 0:
            raise ValueError("traffic_speed_scale must be greater than zero")
        self.spawn_interval = spawn_interval
        self.minimum_spawn_gap = minimum_spawn_gap
        self.traffic_speed_scale = traffic_speed_scale
        self.rng = rng if rng is not None else random.Random()
        self.cars: list[TrafficCar] = []
        self._spawn_elapsed = 0.0
        self._next_lane = Lane.LEFT

    def spawn_car(self, lane: Lane, y: float) -> TrafficCar:
        """Add a car at a chosen position, useful for deterministic setup."""
        if not isinstance(lane, Lane):
            raise TypeError("lane must be a Lane value")
        car = TrafficCar(lane, y, self.rng.choice(TrafficCar.COLORS))
        self.cars.append(car)
        return car

    def _is_safe_spawn(
        self,
        lane: Lane,
        spawn_y: float,
        player_rect: pygame.Rect,
    ) -> bool:
        for car in self.cars:
            vertical_offset = car.y - spawn_y
            if car.lane is lane:
                if abs(vertical_offset) < car.HEIGHT + self.minimum_spawn_gap:
                    return False
            elif (
                -car.HEIGHT < vertical_offset < player_rect.height
            ):
                return False
        return True

    def _try_spawn(self, player_rect: pygame.Rect) -> bool:
        spawn_y = -TrafficCar.HEIGHT
        lanes = (Lane.LEFT, Lane.CENTER, Lane.RIGHT)
        start = lanes.index(self._next_lane)
        ordered = lanes[start:] + lanes[:start]
        for lane in ordered:
            if self._is_safe_spawn(lane, spawn_y, player_rect):
                self.spawn_car(lane, spawn_y)
                self._next_lane = lanes[(lanes.index(lane) + 1) % len(lanes)]
                return True
        return False

    def update(
        self,
        dt: float,
        speed: float,
        screen_height: int,
        player_rect: pygame.Rect,
    ) -> None:
        """Move traffic with forward speed, spawn safely, and remove offscreen cars."""
        movement = (
            speed * PIXELS_PER_SPEED_UNIT * self.traffic_speed_scale * dt
        )
        for car in self.cars:
            car.y += movement
        self.cars = [
            car for car in self.cars if car.y < screen_height
        ]

        if speed <= MIN_SPEED:
            return

        self._spawn_elapsed += dt
        while self._spawn_elapsed >= self.spawn_interval:
            if not self._try_spawn(player_rect):
                self._spawn_elapsed = self.spawn_interval
                break
            self._spawn_elapsed -= self.spawn_interval


def detect_collision(
    player_rect: pygame.Rect,
    traffic_cars: list[TrafficCar],
    road: Road,
    road_bounds: pygame.Rect,
    screen_size: tuple[int, int] | None = None,
) -> bool:
    """Return whether the player's rectangle intersects any traffic car."""
    return any(
        player_rect.colliderect(
            GameRenderer.traffic_rect(car, road, road_bounds, screen_size)
            if screen_size is not None
            else car.rect(road, road_bounds)
        )
        for car in traffic_cars
    )


class DrivingScene:
    """Manage game state and simulation, independently of UI rendering."""

    def __init__(self) -> None:
        self.road = Road()
        self.player = PlayerCar(Lane.CENTER)
        self.speed = MIN_SPEED
        self.target_speed = MIN_SPEED
        self.state_manager = GameStateManager()
        self.traffic = TrafficSpawner()
        self.control_warning: str | None = None
        self.renderer = GameRenderer()
        self.input_mode = InputMode.BOTH
        self.detected_gesture = "UNKNOWN"
        self.gesture_confidence = 0.0
        self.camera_status = "Disconnected"
        self.model_status = "Disconnected"
        self.survival_time = 0.0
        self.distance = 0.0
        self.score = 0

    @property
    def state(self) -> GameState:
        return self.state_manager.state

    def set_speed(self, speed: float) -> None:
        """Compatibility setter that synchronizes current and target speed."""
        self.target_speed = max(MIN_SPEED, min(float(speed), MAX_SPEED))
        self.speed = self.target_speed

    def set_target_speed(self, speed: float) -> None:
        """Set the desired speed; the scene approaches it smoothly in update()."""
        self.target_speed = max(MIN_SPEED, min(float(speed), MAX_SPEED))

    def update_speed(self, dt: float) -> None:
        """Move current speed toward target speed using elapsed time."""
        if self.speed < self.target_speed:
            self.speed = min(
                self.target_speed,
                self.speed + ACCELERATION_RATE * max(0.0, dt),
            )
        elif self.speed > self.target_speed:
            self.speed = max(
                self.target_speed,
                self.speed - BRAKING_RATE * max(0.0, dt),
            )

    def start_game(self) -> bool:
        """Start gameplay from the ready screen."""
        return self.state_manager.transition_to(GameState.PLAYING)

    def _reject_control(self, warning: str) -> bool:
        self.control_warning = warning
        if self.state is GameState.PLAYING:
            self.speed = MIN_SPEED
            self.state_manager.transition_to(GameState.STOPPED)
        return False

    def handle_control_input(
        self,
        control: ControlInput,
        now: float | None = None,
    ) -> bool:
        """Apply one validated external/mock control update.

        Returns False for invalid status or field values; UI warnings are
        retained on the scene for the renderer. Timestamps use monotonic
        seconds, as specified by the shared interface.
        """
        if any(
            not isinstance(value, bool)
            for value in (
                control.valid,
                control.hand_lost,
                control.camera_error,
            )
        ):
            return self._reject_control("Invalid control input")
        if control.camera_error:
            return self._reject_control("Camera error")
        if control.hand_lost:
            return self._reject_control("Hand tracking input lost")
        if not control.valid:
            return self._reject_control("Invalid control input")

        current_time = time.monotonic() if now is None else now
        if (
            not isinstance(control.timestamp, (int, float))
            or isinstance(control.timestamp, bool)
            or not math.isfinite(control.timestamp)
            or control.timestamp > current_time
            or current_time - control.timestamp > CONTROL_MAX_AGE_SECONDS
        ):
            return self._reject_control("Stale or invalid control input")

        lane = control.lane
        if isinstance(lane, str):
            try:
                lane = Lane[lane]
            except KeyError:
                return self._reject_control("Invalid control input")
        if (
            (lane is not None and not isinstance(lane, Lane))
            or (
                control.throttle is not None
                and (
                    not isinstance(control.throttle, (int, float))
                    or isinstance(control.throttle, bool)
                    or not math.isfinite(control.throttle)
                    or not 0.0 <= control.throttle <= 1.0
                )
            )
            or (control.stop is not None and not isinstance(control.stop, bool))
        ):
            return self._reject_control("Invalid control input")

        self.control_warning = None
        if control.stop is True and self.state is GameState.PLAYING:
            self.set_speed(MIN_SPEED)
            self.state_manager.transition_to(GameState.STOPPED)
            return True
        if control.stop is False and self.state is GameState.STOPPED:
            self.state_manager.transition_to(GameState.PLAYING)
        if self.state is GameState.PLAYING:
            if lane is not None:
                self.player.request_lane_change(lane)
            if control.throttle is not None:
                self.set_speed(control.throttle * MAX_SPEED)
        return True

    def restart(self) -> None:
        """Reset a finished session to the ready screen."""
        if self.state is not GameState.GAME_OVER:
            return
        self.road = Road()
        self.player = PlayerCar(Lane.CENTER)
        self.speed = MIN_SPEED
        self.target_speed = MIN_SPEED
        self.traffic = TrafficSpawner()
        self.control_warning = None
        self.state_manager.transition_to(GameState.READY)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if getattr(event, "repeat", False):
                return True
            if self.state is GameState.GAME_OVER:
                if event.key == pygame.K_r:
                    self.restart()
                return True
            if self.state is GameState.READY:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_w):
                    self.start_game()
                    if event.key == pygame.K_w:
                        self.set_speed(SPEED_STEP)
                    return True
                if event.key not in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d,
                                     pygame.K_UP, pygame.K_DOWN, pygame.K_s):
                    return True
            if event.key == pygame.K_p:
                if self.state is GameState.RUNNING:
                    self.state_manager.transition_to(GameState.PAUSED)
                elif self.state is GameState.PAUSED:
                    self.state_manager.transition_to(GameState.RUNNING)
                return True
            if event.key == pygame.K_SPACE:
                if self.state is GameState.PLAYING:
                    self.handle_control_input(
                        ControlInput(timestamp=time.monotonic(), stop=True)
                    )
                elif self.state is GameState.STOPPED:
                    self.handle_control_input(
                        ControlInput(timestamp=time.monotonic(), stop=False)
                    )
                return True
            if event.key in (pygame.K_LEFT, pygame.K_a):
                if self.state in (GameState.READY, GameState.RUNNING, GameState.STOPPED):
                    self.player.move_left()
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                if self.state in (GameState.READY, GameState.RUNNING, GameState.STOPPED):
                    self.player.move_right()
            elif event.key in (pygame.K_UP, pygame.K_w):
                if self.state is GameState.STOPPED:
                    self.state_manager.transition_to(GameState.RUNNING)
                    self.set_target_speed(self.target_speed if self.target_speed > MIN_SPEED else SPEED_STEP)
                elif self.state is GameState.RUNNING:
                    self.set_target_speed(self.target_speed + SPEED_STEP)
                elif self.state is GameState.READY:
                    self.start_game()
                    self.set_target_speed(SPEED_STEP)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                if self.state is GameState.STOPPED:
                    self.set_target_speed(MIN_SPEED)
                    self.speed = MIN_SPEED
                elif self.state in (GameState.RUNNING, GameState.READY):
                    new_target = max(MIN_SPEED, self.target_speed - SPEED_STEP)
                    if new_target <= MIN_SPEED:
                        self.set_speed(MIN_SPEED)
                        self.state_manager.transition_to(GameState.STOPPED)
                    else:
                        self.set_target_speed(new_target)
        return True

    def update(self, dt: float, screen_size: tuple[int, int]) -> None:
        if self.state is not GameState.PLAYING:
            return

        bounds = self.road.bounds(*screen_size)
        self.update_speed(dt)

        self.survival_time += dt
        self.distance += self.speed * dt / 3.6
        self.score = int(self.distance * 10)
        self.player.update(dt, bounds, self.road)
        self.road.update(dt, self.speed, screen_size[1])
        player_rect = self.player.rect(screen_size[1])
        self.traffic.update(dt, self.speed, screen_size[1], player_rect)
        if detect_collision(
            player_rect,
            self.traffic.cars,
            self.road,
            bounds,
            screen_size,
        ):
            self.state_manager.transition_to(GameState.GAME_OVER)
            self.speed = MIN_SPEED
            self.target_speed = MIN_SPEED

    def draw(self, surface: pygame.Surface) -> None:
        self.renderer.draw(surface, self)


class GestureInferenceAdapter:
    """Run camera and model inference off the Pygame update loop."""

    def __init__(
        self,
        model_path: Path,
        confidence_threshold: float = 0.70,
        camera_index: int = 0,
    ) -> None:
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.camera_index = camera_index
        self.predictions: Queue[GesturePrediction] = Queue(maxsize=1)
        self.status = "Disconnected"
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.history = deque(maxlen=5)

    def start(self) -> bool:
        try:
            import cv2
            import mediapipe as mp
            import joblib
        except Exception:
            self.status = "Missing OpenCV, MediaPipe, or joblib"
            return False

        if not self.model_path.is_file():
            self.status = "Model file unavailable"
            return False

        self.status = "Starting"
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(cv2, mp, joblib),
            daemon=True,
            name="gesture-inference",
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def latest(self) -> GesturePrediction | None:
        try:
            return self.predictions.get_nowait()
        except Empty:
            return None

    def _run(self, cv2, mp, joblib) -> None:
        try:
            model = joblib.load(self.model_path)
            model_classes = getattr(model, "classes_", None)
        except Exception as exc:
            self.status = f"Model load error: {exc}"
            return

        try:
            capture = cv2.VideoCapture(self.camera_index)
            if not capture.isOpened():
                self.status = "Camera unavailable"
                return
            self.status = "Model and camera connected"

            hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.5,
            )
            try:
                while not self._stop_event.is_set():
                    ok, frame = capture.read()
                    if not ok:
                        self.status = "Camera disconnected"
                        break
                    frame = cv2.flip(frame, 1)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    result = hands.process(rgb)
                    if not result.multi_hand_landmarks:
                        self.history.clear()
                        prediction = GesturePrediction("UNKNOWN", 0.0, time.monotonic())
                    else:
                        landmarks = result.multi_hand_landmarks[0].landmark
                        features = preprocess_landmarks(landmarks).reshape(1, 63)
                        raw_label = model.predict(features)[0]
                        if isinstance(raw_label, (int, np.integer)):
                            index = int(raw_label)
                            if not 0 <= index < len(CLASS_NAMES):
                                raise ValueError(f"Unexpected model class index: {index}")
                            label = CLASS_NAMES[index]
                        else:
                            label = str(raw_label)
                        probabilities = model.predict_proba(features)[0]
                        confidence = float(np.max(probabilities))
                        if confidence >= self.confidence_threshold:
                            self.history.append(label.upper())
                        else:
                            self.history.clear()
                        stable_label = (
                            Counter(self.history).most_common(1)[0][0]
                            if self.history else "UNKNOWN"
                        )
                        prediction = GesturePrediction(stable_label, confidence, time.monotonic())
                    try:
                        self.predictions.get_nowait()
                    except Empty:
                        pass
                    self.predictions.put_nowait(prediction)
            finally:
                hands.close()
                capture.release()
        except Exception as exc:
            self.status = f"Inference error: {exc}"


class GestureCommandMapper:
    """Maintain cruising speed, boost while palm is held, brake while fist is held."""

    LABEL_ALIASES = {
        "PALM": "PALM", "OPEN_PALM": "PALM",
        "FIST": "FIST", "LEFT": "LEFT", "LEFT_DIR": "LEFT",
        "RIGHT": "RIGHT", "RIGHT_DIR": "RIGHT",
        "UNKNOWN": "UNKNOWN", "NO_HAND": "UNKNOWN", "NONE": "UNKNOWN",
    }

    def __init__(self, confidence_threshold: float = 0.70) -> None:
        self.confidence_threshold = confidence_threshold
        self.last_steering_label: str | None = None
        self.active_label = "UNKNOWN"
        self.last_seen_at: float | None = None

    def map_prediction(self, scene: DrivingScene, prediction: GesturePrediction) -> bool:
        label = self.LABEL_ALIASES.get(str(prediction.label).upper(), "UNKNOWN")
        if prediction.confidence < self.confidence_threshold:
            label = "UNKNOWN"
        self.last_seen_at = time.monotonic()
        self.active_label = label

        if label == "PALM" and scene.state is GameState.READY:
            scene.start_game()
        elif label == "PALM" and scene.state is GameState.STOPPED:
            scene.state_manager.transition_to(GameState.RUNNING)

        if label not in ("LEFT", "RIGHT"):
            self.last_steering_label = None
            return label in ("PALM", "FIST")

        if label == self.last_steering_label:
            return False
        changed = False
        if scene.state is GameState.RUNNING:
            if label == "LEFT":
                changed = scene.player.move_left()
            else:
                changed = scene.player.move_right()
        self.last_steering_label = label
        return changed

    def update_speed_target(self, scene: DrivingScene) -> None:
        """Called every frame so removing the hand restores cruising speed."""
        if scene.state is not GameState.RUNNING:
            return
        if (self.last_seen_at is None or
                time.monotonic() - self.last_seen_at > GESTURE_TIMEOUT_SECONDS):
            self.active_label = "UNKNOWN"
            self.last_steering_label = None
        if self.active_label == "PALM":
            scene.set_target_speed(BOOST_SPEED)
        elif self.active_label == "FIST":
            scene.set_target_speed(MIN_SPEED)
        else:
            scene.set_target_speed(CRUISE_SPEED)

    def handle_tracking_timeout(self, scene: DrivingScene) -> None:
        """Compatibility wrapper for the existing game loop."""
        self.update_speed_target(scene)


class GameRenderer:
    """Draw a procedural pseudo-3D road, scenery, cars, and compact UI."""

    ROAD_TOP_WIDTH_RATIO = 0.035
    ROAD_BOTTOM_WIDTH_RATIO = 0.92
    HORIZON_RATIO = 0.25
    DASH_WORLD_LENGTH = 54.0

    @classmethod
    def road_half_width(cls, progress: float, screen_width: int) -> float:
        progress = max(0.0, min(progress, 1.0))
        top = screen_width * cls.ROAD_TOP_WIDTH_RATIO / 2
        bottom = screen_width * cls.ROAD_BOTTOM_WIDTH_RATIO / 2
        return top + (bottom - top) * progress

    @classmethod
    def project_progress(
        cls,
        progress: float,
        screen_size: tuple[int, int],
    ) -> float:
        width, height = screen_size
        horizon = height * cls.HORIZON_RATIO
        return horizon + (height - horizon) * max(0.0, min(progress, 1.0))

    @classmethod
    def traffic_rect(
        cls,
        car: TrafficCar,
        road: Road,
        road_bounds: pygame.Rect,
        screen_size: tuple[int, int] | None,
    ) -> pygame.Rect:
        if screen_size is None:
            return car.rect(road, road_bounds)
        width, height = screen_size
        progress = max(
            0.0,
            min((car.y + car.HEIGHT) / (height + car.HEIGHT), 1.0),
        )
        screen_y = cls.project_progress(progress**1.35, screen_size)
        scale = 0.18 + 0.82 * progress
        road_center = width / 2
        half_road = cls.road_half_width(progress, width)
        lane_offset = half_road * (2.0 / 3.0)
        lane_x = {
            Lane.LEFT: road_center - lane_offset,
            Lane.CENTER: road_center,
            Lane.RIGHT: road_center + lane_offset,
        }
        center_x = lane_x[car.lane]
        car_width = max(8, round(TRAFFIC_CAR_WIDTH * 1.45 * scale))
        car_height = max(12, round(TRAFFIC_CAR_HEIGHT * 1.15 * scale))
        return pygame.Rect(
            round(center_x - car_width / 2),
            round(screen_y - car_height / 2),
            car_width,
            car_height,
        )

    def draw(self, surface: pygame.Surface, scene: DrivingScene) -> None:
        size = surface.get_size()
        # Rebuild the entire display each frame.  Moving vehicles are never drawn
        # onto a persistent static/background surface, so there is no old-frame trail.
        surface.fill((104, 153, 198))
        self._draw_city_sky(surface)
        self._draw_city_buildings(surface, scene.road)
        self._draw_road(surface, scene.road)
        bounds = scene.road.bounds(*size)
        self._draw_roadside_objects(surface, scene.road)
        for car in scene.traffic.cars:
            self._draw_traffic_car(surface, car, scene.road, bounds, size)
        self._draw_player(surface, scene.player, size)
        self._draw_hud(surface, scene)

        messages = {
            GameState.READY: ("READY", "Press Enter or Space to start"),
            GameState.STOPPED: ("STOPPED", "Press Space to resume"),
            GameState.PAUSED: ("PAUSED", "Press Space to resume  |  R to restart"),
            GameState.GAME_OVER: ("GAME OVER", "Press R or click Restart"),
        }
        if scene.state in messages:
            self._draw_overlay(surface, *messages[scene.state])

    def _draw_desert(self, surface: pygame.Surface) -> None:
        """Backward-compatible name; draws the city sky during transition-era tests."""
        self._draw_city_sky(surface)

    def _draw_mountains(self, surface: pygame.Surface) -> None:
        """Backward-compatible name; draws the skyline rather than mountains."""
        self._draw_city_buildings(surface, Road())

    def _draw_city_sky(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        horizon = round(height * self.HORIZON_RATIO)
        for y in range(horizon + 1):
            blend = y / max(horizon, 1)
            color = (
                round(104 + 55 * blend),
                round(153 + 44 * blend),
                round(198 + 38 * blend),
            )
            pygame.draw.line(surface, color, (0, y), (width, y))

        sun_x = round(width * 0.78)
        sun_y = round(horizon * 0.38)
        pygame.draw.circle(surface, (244, 224, 164), (sun_x, sun_y), max(7, width // 60))

    def _draw_city_buildings(self, surface: pygame.Surface, road: Road) -> None:
        width, height = surface.get_size()
        horizon = round(height * self.HORIZON_RATIO)
        road_center = width / 2

        # Distant city: low-detail, lightly saturated silhouettes.
        distant = [
            (0.00, 0.34, 0.08, (118, 137, 151)),
            (0.08, 0.28, 0.06, (130, 147, 158)),
            (0.15, 0.42, 0.07, (112, 132, 148)),
            (0.23, 0.24, 0.05, (137, 151, 160)),
            (0.67, 0.30, 0.05, (137, 151, 160)),
            (0.73, 0.46, 0.07, (112, 132, 148)),
            (0.81, 0.32, 0.06, (130, 147, 158)),
            (0.88, 0.38, 0.09, (118, 137, 151)),
        ]
        for start, building_height_ratio, building_width_ratio, color in distant:
            building_width = round(width * building_width_ratio)
            building_height = round(horizon * building_height_ratio)
            left = round(width * start)
            top = horizon - building_height
            pygame.draw.polygon(surface, color, (
                (left, horizon),
                (left, top + 8),
                (left + building_width // 3, top + 8),
                (left + building_width // 3, top),
                (left + building_width * 2 // 3, top),
                (left + building_width * 2 // 3, top + 12),
                (left + building_width, top + 12),
                (left + building_width, horizon),
            ))

        # Nearer, stronger-contrast urban blocks outside the road and sidewalks.
        closer = (
            (0.0, 0.16, 0.62, (62, 76, 88)),
            (0.18, 0.10, 0.51, (72, 84, 96)),
            (0.72, 0.10, 0.56, (72, 84, 96)),
            (0.84, 0.16, 0.68, (62, 76, 88)),
        )
        for start, width_ratio, height_ratio, base_color in closer:
            left = round(width * start)
            building_width = round(width * width_ratio)
            building_height = round(horizon * height_ratio)
            top = horizon - building_height
            pygame.draw.rect(surface, base_color, (left, top, building_width, building_height))

            roof = max(2, building_width // 14)
            pygame.draw.rect(surface, (48, 60, 72), (left + roof, top - 4, max(5, building_width // 3), 4))
            column_gap = max(12, building_width // 6)
            window_y = top + 12
            while window_y < horizon - 8:
                window_x = left + 9
                while window_x < left + building_width - 7:
                    lit = ((window_x // column_gap + window_y) % 5) != 0
                    window_color = (196, 213, 222) if lit else (92, 119, 132)
                    pygame.draw.rect(surface, window_color, (window_x, window_y, max(3, column_gap // 3), 6))
                    window_x += column_gap
                window_y += 15

    def _draw_road(self, surface: pygame.Surface, road: Road) -> None:
        width, height = surface.get_size()
        center_x = width / 2
        horizon = round(height * self.HORIZON_RATIO)
        bottom = height + 2

        steps = 48
        for index in range(steps):
            top_progress = index / steps
            bottom_progress = (index + 1) / steps
            top_y = round(horizon + (height - horizon) * top_progress)
            bottom_y = round(horizon + (height - horizon) * bottom_progress) + 1
            top_half = self.road_half_width(top_progress, width)
            bottom_half = self.road_half_width(bottom_progress, width)
            shade = round(14 * bottom_progress)
            color = (49 + shade, 51 + shade, 54 + shade)
            pygame.draw.polygon(
                surface,
                color,
                (
                    (round(center_x - top_half), top_y),
                    (round(center_x + top_half), top_y),
                    (round(center_x + bottom_half), bottom_y),
                    (round(center_x - bottom_half), bottom_y),
                ),
            )

        texture_span = max(height - horizon, 1)
        for index in range(144):
            texture_y = horizon + (
                index * 67 + round(road.texture_offset)
            ) % texture_span
            progress = (texture_y - horizon) / texture_span
            half_width = self.road_half_width(progress, width) - 4
            lateral = ((index * 193) % 1000) / 999 * 1.8 - 0.9
            texture_x = round(center_x + lateral * half_width)
            grain = 55 + (index * 13) % 13
            pygame.draw.line(
                surface,
                (grain, grain + 1, grain + 2),
                (texture_x, texture_y),
                (texture_x + max(1, round(1 + 3 * progress)), texture_y),
                1,
            )

        top_half = self.road_half_width(0, width)
        bottom_half = self.road_half_width(1, width)
        for side in (-1, 1):
            pygame.draw.line(
                surface,
                (238, 225, 187),
                (round(center_x + side * top_half), horizon),
                (round(center_x + side * bottom_half), bottom),
                max(2, round(width * 0.006)),
            )
            pygame.draw.line(
                surface,
                (124, 132, 138),
                (round(center_x + side * (top_half + 12)), horizon),
                (round(center_x + side * (bottom_half + 42)), bottom),
                max(3, round(width * 0.012)),
            )
            pygame.draw.line(
                surface,
                (205, 209, 210),
                (round(center_x + side * (top_half + 22)), horizon),
                (round(center_x + side * (bottom_half + 66)), bottom),
                max(2, round(width * 0.006)),
            )

        phase = road.marking_offset % self.DASH_WORLD_LENGTH
        distance = phase
        while distance < 1500:
            start_progress = 1 - math.exp(-distance / 600)
            end_progress = 1 - math.exp(
                -(distance + self.DASH_WORLD_LENGTH * 0.42) / 600
            )
            start_y = self.project_progress(start_progress, surface.get_size())
            end_y = self.project_progress(end_progress, surface.get_size())
            if end_y - start_y > 1:
                stripe_width = max(1, round(1 + 3 * end_progress))
                start_half = self.road_half_width(start_progress, width)
                end_half = self.road_half_width(end_progress, width)
                for lane_fraction in (-1.0 / 3.0, 1.0 / 3.0):
                    pygame.draw.line(
                        surface,
                        (244, 246, 247),
                        (round(center_x + lane_fraction * start_half), round(start_y)),
                        (round(center_x + lane_fraction * end_half), round(end_y)),
                        stripe_width,
                    )
            distance += self.DASH_WORLD_LENGTH

    def _draw_roadside_objects(self, surface: pygame.Surface, road: Road) -> None:
        width, _ = surface.get_size()
        center_x = width / 2
        for is_right, y in road.roadside_positions:
            progress = max(0.0, min(y / max(surface.get_height(), 1), 1.0))
            screen_y = self.project_progress(progress, surface.get_size())
            half_road = self.road_half_width(progress, width)
            side_offset = half_road + 18 + 48 * progress
            x = center_x + side_offset if is_right else center_x - side_offset
            size = max(3, round(4 + 14 * progress))

            # Streetlamp pole and warm lamp head.
            pygame.draw.rect(
                surface,
                (54, 61, 66),
                (round(x - size * 0.12), round(screen_y - size * 2.2), max(2, size // 4), round(size * 1.8)),
            )
            pygame.draw.circle(
                surface,
                (255, 226, 151),
                (round(x), round(screen_y - size * 2.45)),
                max(2, size // 2),
            )

            pygame.draw.rect(
                surface,
                (132, 138, 142),
                (round(x - size * 0.7), round(screen_y - size), round(size * 1.4), size),
            )
            pygame.draw.rect(
                surface,
                (64, 68, 72),
                (round(x - size * 0.12), round(screen_y - size * 2.2), max(2, size // 4), round(size * 1.8)),
            )
            pygame.draw.circle(
                surface,
                (45, 52, 58),
                (round(x), round(screen_y - size * 2.45)),
                max(2, size // 2),
            )
            pygame.draw.rect(
                surface,
                (44, 112, 62),
                (round(x - size * 1.2), round(screen_y - size * 0.25), round(size * 2.4), max(2, size // 3)),
            )

    def _draw_traffic_car(
        self,
        surface: pygame.Surface,
        car: TrafficCar,
        road: Road,
        road_bounds: pygame.Rect,
        screen_size: tuple[int, int],
    ) -> None:
        rect = self.traffic_rect(car, road, road_bounds, screen_size)
        kind_index = (car.lane.value + max(0, round(car.y))) % 5
        vehicle_type = ("sedan", "suv", "van", "compact", "taxi")[kind_index]
        self._draw_vehicle(
            surface,
            rect,
            car.color,
            vehicle_type=vehicle_type,
            window_tint=(74, 112, 130),
            steering_tilt=0.0,
        )

    @staticmethod
    def _draw_player(
        surface: pygame.Surface,
        player: PlayerCar,
        screen_size: tuple[int, int],
    ) -> None:
        rect = player.rect(screen_size[1])
        tilt = getattr(player, "steering_tilt", 0.0)
        GameRenderer._draw_vehicle(
            surface,
            rect,
            (29, 116, 198),
            vehicle_type="sedan",
            window_tint=(18, 48, 66),
            steering_tilt=tilt,
            player_vehicle=True,
        )

    @staticmethod
    def _draw_vehicle(
        surface: pygame.Surface,
        rect: pygame.Rect,
        body_color: tuple[int, int, int],
        vehicle_type: str = "sedan",
        window_tint: tuple[int, int, int] = (74, 112, 130),
        steering_tilt: float = 0.0,
        player_vehicle: bool = False,
    ) -> None:
        left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
        width, height = rect.size
        offset = round(steering_tilt * 0.45)

        shadow = pygame.Rect(left - 4 + offset, bottom - 8, width + 8, max(4, height // 10))
        pygame.draw.ellipse(surface, (14, 18, 24), shadow)

        roof_scale = 0.78 if vehicle_type == "compact" else 0.72
        if vehicle_type == "van":
            roof_scale = 0.88
        elif vehicle_type == "suv":
            roof_scale = 0.82

        body_top = top + round(height * 0.28)
        highlight = tuple(min(255, channel + 48) for channel in body_color)
        shadow_color = tuple(max(0, channel - 34) for channel in body_color)

        # Tires sit behind the body and remain visible on both sides.
        wheel_width = max(4, round(width * 0.13))
        wheel_height = max(6, round(height * 0.16))
        wheel_y = bottom - round(height * 0.30)
        for wheel_x in (left - wheel_width // 3, right - wheel_width * 2 // 3):
            pygame.draw.ellipse(surface, (18, 21, 24), (wheel_x, wheel_y, wheel_width, wheel_height))
            pygame.draw.ellipse(surface, (145, 152, 158), (wheel_x + wheel_width // 4, wheel_y + wheel_height // 4,
                                                               max(2, wheel_width // 2), max(2, wheel_height // 2)))

        # Aerodynamic rear silhouette with a darker lower bumper.
        pygame.draw.polygon(surface, shadow_color, (
            (left + offset - 3, bottom - height // 12),
            (left + offset, body_top + height // 9),
            (left + width // 7 + offset, top + height // 5),
            (right - width // 7 + offset, top + height // 5),
            (right + offset, body_top + height // 9),
            (right + offset + 3, bottom - height // 12),
            (right - width // 10 + offset, bottom),
            (left + width // 10 + offset, bottom),
        ))
        pygame.draw.polygon(surface, body_color, (
            (left + offset, bottom - height // 7),
            (left + width // 11 + offset, body_top),
            (left + width // 6 + offset, top + round(height * 0.20)),
            (right - width // 6 + offset, top + round(height * 0.20)),
            (right - width // 11 + offset, body_top),
            (right + offset, bottom - height // 7),
            (right - width // 10 + offset, bottom - height // 18),
            (left + width // 10 + offset, bottom - height // 18),
        ))

        # Metallic highlight along the shoulder line.
        pygame.draw.line(surface, highlight,
                         (left + width // 7 + offset, body_top + height // 10),
                         (right - width // 7 + offset, body_top + height // 10),
                         max(1, round(height / 55)))

        # Rear windshield and roof/trunk separation.
        rear_glass = pygame.Rect(
            left + round(width * 0.23),
            top + round(height * 0.22),
            round(width * 0.54),
            round(height * 0.23 * roof_scale),
        )
        pygame.draw.polygon(surface, window_tint, (
            (rear_glass.left, rear_glass.bottom),
            (left + round(width * 0.31), rear_glass.top),
            (right - round(width * 0.31), rear_glass.top),
            (rear_glass.right, rear_glass.bottom),
        ))
        pygame.draw.line(surface, (205, 224, 232),
                         (rear_glass.left + 4, rear_glass.top + 3),
                         (left + width // 2, rear_glass.top + 1), 1)

        # Side mirrors.
        mirror_width = max(4, round(width * 0.11))
        mirror_height = max(3, round(height * 0.055))
        pygame.draw.ellipse(surface, body_color,
                            (left - mirror_width // 2, body_top + height // 12, mirror_width, mirror_height))
        pygame.draw.ellipse(surface, body_color,
                            (right - mirror_width // 2, body_top + height // 12, mirror_width, mirror_height))

        # Tail lamps, trunk line, license plate, and dark rear bumper.
        lamp_width = max(4, round(width * 0.16))
        lamp_height = max(3, round(height * 0.065))
        lamp_y = bottom - round(height * 0.27)
        pygame.draw.rect(surface, (255, 70, 82), (left + width // 8, lamp_y, lamp_width, lamp_height), border_radius=2)
        pygame.draw.rect(surface, (255, 70, 82), (right - width // 8 - lamp_width, lamp_y, lamp_width, lamp_height), border_radius=2)
        pygame.draw.rect(surface, (18, 22, 27),
                         (left + width // 3, bottom - round(height * 0.16), round(width // 3), max(5, round(height * 0.07))),
                         border_radius=max(2, round(height * 0.03)))
        pygame.draw.rect(surface, (225, 232, 235),
                         (left + width * 0.38, bottom - round(height * 0.145), round(width * 0.24), max(3, round(height * 0.045))),
                         border_radius=1)

        if vehicle_type == "taxi":
            pygame.draw.rect(surface, (244, 205, 72),
                             (left + width * 0.41, top + round(height * 0.05), round(width * 0.18), max(3, round(height * 0.035))),
                             border_radius=2)

        if player_vehicle:
            pygame.draw.line(surface, (118, 204, 255),
                             (left + width // 2 - 1, top + 2),
                             (left + width // 2 - 1, bottom - height // 7), 1)

    def _draw_hud(self, surface: pygame.Surface, scene: DrivingScene) -> None:
        width, height = surface.get_size()
        font = pygame.font.Font(None, 22)
        small = pygame.font.Font(None, 18)

        def panel(rect: pygame.Rect, title: str, lines: list[str], accent: tuple[int, int, int] = (76, 154, 219)) -> None:
            panel_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            panel_surface.fill((14, 24, 34, 210))
            pygame.draw.rect(panel_surface, accent, (0, 0, 4, rect.height))
            surface.blit(panel_surface, rect.topleft)
            surface.blit(font.render(title, True, (184, 210, 228)), (rect.left + 14, rect.top + 9))
            for index, line in enumerate(lines):
                surface.blit(small.render(line, True, (244, 248, 250)), (rect.left + 14, rect.top + 34 + index * 19))

        panel(pygame.Rect(14, 12, 178, 92), "VEHICLE", [
            f"{scene.speed:05.1f} KM/H",
            f"LANE  {scene.player.lane.name}",
            f"DIST  {scene.distance:0.1f} km",
        ])
        panel(pygame.Rect(width - 214, 12, 200, 92), "SESSION", [
            f"STATE  {scene.state.name}",
            f"SCORE  {scene.score}",
            f"TIME   {scene.survival_time:.1f}s",
        ], (88, 196, 180))

        gesture_ok = scene.camera_status == "Connected" and "Inference" in scene.model_status
        status_color = (92, 201, 144) if gesture_ok else (224, 159, 82)
        gesture_text = f"GESTURE  {scene.detected_gesture}  {scene.gesture_confidence:.0%}" if gesture_ok else "GESTURE  UNAVAILABLE"
        status = (
            f"INPUT {scene.input_mode.name.replace('_', ' ')}  |  "
            f"CAMERA {'CONNECTED' if scene.camera_status == 'Connected' else 'OFFLINE'}  |  MODEL {'READY' if gesture_ok else 'OFFLINE'}"
        )
        bar_width = min(width - 28, 620)
        bar = pygame.Rect((width - bar_width) // 2, height - 42, bar_width, 30)
        bar_surface = pygame.Surface(bar.size, pygame.SRCALPHA)
        bar_surface.fill((12, 21, 30, 215))
        surface.blit(bar_surface, bar.topleft)
        surface.blit(small.render(gesture_text, True, status_color), (bar.left + 12, bar.top + 8))
        status_surface = small.render(status, True, (210, 222, 230))
        surface.blit(status_surface, status_surface.get_rect(right=bar.right - 12, centery=bar.centery))

        if scene.control_warning:
            warning = small.render(scene.control_warning, True, (255, 204, 122))
            surface.blit(warning, warning.get_rect(center=(width // 2, height - 55)))

    @staticmethod
    def _draw_overlay(
        surface: pygame.Surface,
        title_text: str,
        prompt_text: str,
    ) -> None:
        width, height = surface.get_size()
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((7, 15, 23, 112))
        surface.blit(overlay, (0, 0))

        panel_width = min(width - 40, 360)
        panel_height = 112
        panel = pygame.Rect((width - panel_width) // 2, height // 2 - panel_height // 2, panel_width, panel_height)
        panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        panel_surface.fill((14, 24, 34, 230))
        pygame.draw.rect(panel_surface, (76, 154, 219), (0, 0, 4, panel_height))
        surface.blit(panel_surface, panel.topleft)

        title = pygame.font.Font(None, 38).render(title_text, True, (244, 248, 250))
        prompt = pygame.font.Font(None, 22).render(prompt_text, True, (181, 205, 220))
        surface.blit(title, title.get_rect(center=(panel.centerx, panel.top + 34)))
        surface.blit(prompt, prompt.get_rect(center=(panel.centerx, panel.top + 78)))

        if title_text == "GAME OVER":
            button = pygame.Rect(panel.centerx - 58, panel.bottom + 10, 116, 34)
            pygame.draw.rect(surface, (38, 118, 180), button, border_radius=6)
            label = pygame.font.Font(None, 22).render("RESTART", True, (255, 255, 255))
            surface.blit(label, label.get_rect(center=button.center))


def run_game() -> None:
    """Initialize Pygame and run the resizable 60 FPS game loop."""
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption("Three-Lane Hand Gesture Driving Simulator")

    scene = DrivingScene()
    mapper = GestureCommandMapper()
    model_path = ML_DIR / "models" / "gesture_model.pkl"
    inference = GestureInferenceAdapter(model_path)
    inference.start()
    clock = pygame.time.Clock()
    running = True

    try:
        while running:
            dt = min(clock.tick(TARGET_FPS) / 1000.0, 0.1)
            for event in pygame.event.get():
                if event.type == pygame.VIDEORESIZE:
                    new_size = (
                        max(event.w, MIN_WINDOW_SIZE[0]),
                        max(event.h, MIN_WINDOW_SIZE[1]),
                    )
                    screen = pygame.display.set_mode(new_size, pygame.RESIZABLE)
                running = scene.handle_event(event) and running

            prediction = inference.latest()
            if prediction is not None:
                scene.detected_gesture = prediction.label.upper()
                scene.gesture_confidence = prediction.confidence
                scene.camera_status = "Connected" if inference.status.startswith("Model and camera") else "Disconnected"
                scene.model_status = "Inference available" if inference.status.startswith("Model and camera") else inference.status
                if scene.input_mode in (InputMode.HAND_GESTURE, InputMode.BOTH):
                    mapper.map_prediction(scene, prediction)

            inference_status = inference.status
            if inference_status.startswith(("Camera unavailable", "Camera disconnected", "Inference error", "Model load error", "Missing", "Model file unavailable")):
                scene.detected_gesture = "UNKNOWN"
                scene.gesture_confidence = 0.0
                mapper.active_label = "UNKNOWN"
                mapper.last_steering_label = None
            if inference_status.startswith("Model and camera"):
                scene.camera_status = "Connected"
                scene.model_status = "Inference available"
            else:
                scene.camera_status = inference_status if "Camera" in inference_status else scene.camera_status
                scene.model_status = inference_status if inference_status != "Disconnected" else "Disconnected"

            if scene.input_mode in (InputMode.HAND_GESTURE, InputMode.BOTH):
                mapper.update_speed_target(scene)

            scene.update(dt, screen.get_size())
            scene.draw(screen)
            pygame.display.flip()
    finally:
        inference.stop()
        pygame.quit()


if __name__ == "__main__":
    run_game()
