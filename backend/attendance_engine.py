"""
Attendance Engine — refactored from attendance_ai.py.
Runs the recognition pipeline in a background thread, emitting events
for recognised and unknown persons.
"""

import cv2
import numpy as np
import threading
import time
import os
import sys
from datetime import datetime

import torch

# Workaround: mediapipe.tasks imports tensorflow which has a protobuf conflict.
# Block it by injecting a dummy module before importing mediapipe.
import types
import importlib
_dummy = types.ModuleType("mediapipe.tasks")
sys.modules["mediapipe.tasks"] = _dummy
sys.modules["mediapipe.tasks.python"] = _dummy
import mediapipe as mp

# Add project root to path so we can import existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from blink import eye_aspect_ratio
from train_liveness import LivenessModel


class AttendanceEngine:
    def __init__(self, camera_manager, alert_manager):
        self._camera = camera_manager
        self._alert = alert_manager
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

        # Detection state
        self._blink_counter = 0
        self._eye_closed = False
        self.BLINK_THRESHOLD = 1
        self.EAR_THRESHOLD = 0.20

        # Performance tuning for lower-latency detection on modest hardware.
        self.PROCESS_EVERY_N_FRAMES = 1
        self.DETECTION_SCALE = 0.4
        self.LIVENESS_EVERY_N_FRAMES = 5
        self.RECOGNITION_COOLDOWN = 0.2
        self._frame_index = 0
        self._last_liveness = True
        self._last_recognition_time = 0.0

        # Track today's marked attendees (survives across start/stop)
        self._marked_today = set()
        self._today_date = None

        # Models (loaded lazily)
        self._recognizer = None
        self._liveness_model = None
        self._names = []
        self._face_cascade = None
        self._mp_face_mesh = None
        self._device = None
        self._models_loaded = False

        # Listeners for attendance events
        self._listeners = []

        # Cooldown to prevent spamming unknown alerts
        self._last_unknown_alert = 0
        self.UNKNOWN_ALERT_COOLDOWN = 15  # seconds

    # ── Model loading ──────────────────────────────────────────────────
    def load_models(self):
        """Load or reload all models from disk."""
        root = os.path.join(os.path.dirname(__file__), "..")

        # Face cascade
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # LBPH recognizer
        recognizer_path = os.path.join(root, "models", "recognizer.yml")
        names_path = os.path.join(root, "models", "names.txt")
        if os.path.exists(recognizer_path) and os.path.exists(names_path):
            self._recognizer = cv2.face.LBPHFaceRecognizer_create()
            self._recognizer.read(recognizer_path)
            with open(names_path) as f:
                self._names = [line.strip() for line in f.readlines()]
        else:
            self._recognizer = None
            self._names = []

        # Liveness CNN
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        liveness_path = os.path.join(root, "models", "liveness_model.pth")
        if os.path.exists(liveness_path):
            self._liveness_model = LivenessModel().to(self._device)
            self._liveness_model.load_state_dict(
                torch.load(liveness_path, map_location=self._device)
            )
            self._liveness_model.eval()
        else:
            self._liveness_model = None

        # MediaPipe Face Mesh
        self._mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.4,
            min_tracking_confidence=0.4,
        )

        self._models_loaded = True

        # Load today's already-marked attendees from CSV
        self._load_today_attendance()

    def _load_today_attendance(self):
        """Read attendance.csv and populate today's marked set."""
        root = os.path.join(os.path.dirname(__file__), "..")
        csv_path = os.path.join(root, "attendance.csv")
        today = datetime.now().strftime("%Y-%m-%d")
        self._today_date = today
        self._marked_today.clear()

        if not os.path.exists(csv_path):
            return
        with open(csv_path, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 2 and parts[1] == today:
                    self._marked_today.add(parts[0])

    # ── Attendance marking ─────────────────────────────────────────────
    def _mark_attendance(self, name):
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._today_date:
            self._today_date = today
            self._marked_today.clear()

        if name in self._marked_today:
            return False

        root = os.path.join(os.path.dirname(__file__), "..")
        csv_path = os.path.join(root, "attendance.csv")

        # Add header if file is empty or new
        write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
        with open(csv_path, "a") as f:
            if write_header:
                f.write("name,date,time\n")
            t = datetime.now().strftime("%H:%M:%S")
            f.write(f"{name},{today},{t}\n")

        self._marked_today.add(name)
        self._broadcast({
            "type": "attendance",
            "name": name,
            "date": today,
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        return True

    # ── Main loop ──────────────────────────────────────────────────────
    def start(self):
        if self._running:
            return
        if not self._models_loaded:
            self.load_models()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    @property
    def is_running(self):
        return self._running

    @property
    def models_loaded(self):
        return self._models_loaded

    @property
    def status(self):
        return {
            "running": self._running,
            "modelsLoaded": self._models_loaded,
            "recognizerLoaded": self._recognizer is not None,
            "livenessLoaded": self._liveness_model is not None,
            "registeredNames": self._names,
            "blinks": self._blink_counter,
            "blinkThreshold": self.BLINK_THRESHOLD,
        }

    def _run(self):
        while self._running:
            frame = self._camera.get_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            self._frame_index += 1
            if self._frame_index % self.PROCESS_EVERY_N_FRAMES != 0:
                time.sleep(0.005)
                continue

            try:
                self._process_frame(frame)
            except Exception as e:
                print(f"[AttendanceEngine] Error: {e}")
            time.sleep(0.033)  # ~30 fps

    def _process_frame(self, frame):
        # Run heavy detectors on a smaller frame, then map bboxes back.
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(frame, None, fx=self.DETECTION_SCALE, fy=self.DETECTION_SCALE)
        hs, ws = small.shape[:2]
        gray_small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        faces_small = self._face_cascade.detectMultiScale(gray_small, 1.2, 5)
        if len(faces_small) == 0:
            return

        sx = w / ws
        sy = h / hs

        # MediaPipe for blink detection
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        mp_results = self._mp_face_mesh.process(rgb)

        for (x_s, y_s, ww_s, hh_s) in faces_small:
            x = int(x_s * sx)
            y = int(y_s * sy)
            ww = int(ww_s * sx)
            hh = int(hh_s * sy)

            x = max(0, min(x, w - 1))
            y = max(0, min(y, h - 1))
            ww = max(1, min(ww, w - x))
            hh = max(1, min(hh, h - y))

            face_roi = frame[y : y + hh, x : x + ww]
            if face_roi.size == 0:
                continue

            # Liveness check
            is_live = True
            if self._liveness_model is not None:
                if self._frame_index % self.LIVENESS_EVERY_N_FRAMES == 0:
                    self._last_liveness = self._check_liveness(face_roi)
                is_live = self._last_liveness

            if not is_live:
                continue

            # Blink detection
            if mp_results and mp_results.multi_face_landmarks:
                for fl in mp_results.multi_face_landmarks:
                    landmarks = np.array([(lm.x * ws, lm.y * hs) for lm in fl.landmark])
                    left_eye = [33, 160, 158, 133, 153, 144]
                    ear = eye_aspect_ratio(landmarks, left_eye)

                    if ear < self.EAR_THRESHOLD:
                        self._eye_closed = True
                    elif self._eye_closed and ear >= self.EAR_THRESHOLD:
                        self._blink_counter += 1
                        self._eye_closed = False

            # Recognition after blink threshold
            if self._blink_counter >= self.BLINK_THRESHOLD:
                if self._recognizer is None:
                    continue
                now = time.time()
                if now - self._last_recognition_time < self.RECOGNITION_COOLDOWN:
                    continue
                self._last_recognition_time = now
                id_, conf = self._recognizer.predict(gray[y : y + hh, x : x + ww])

                if conf < 60 and id_ < len(self._names):
                    name = self._names[id_]
                    self._mark_attendance(name)
                    self._blink_counter = 0
                else:
                    # Unknown person — keep alert active until manually stopped
                    self._handle_unknown()
                    # Don't reset blink counter so alert keeps re-triggering
                    # self._blink_counter = 0

    def _check_liveness(self, face_roi):
        face_resized = cv2.resize(face_roi, (64, 64))
        face_resized = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
        face_resized = face_resized / 255.0
        face_resized = np.transpose(face_resized, (2, 0, 1))
        tensor = torch.from_numpy(face_resized).float().unsqueeze(0).to(self._device)

        with torch.no_grad():
            pred = self._liveness_model(tensor)
        return pred[0][0].item() > 0.5

    def _handle_unknown(self):
        now = time.time()
        if now - self._last_unknown_alert < self.UNKNOWN_ALERT_COOLDOWN:
            return
        self._last_unknown_alert = now
        self._alert.trigger()

    # ── SSE event listeners ────────────────────────────────────────────
    def add_listener(self, queue):
        self._listeners.append(queue)

    def remove_listener(self, queue):
        if queue in self._listeners:
            self._listeners.remove(queue)

    def _broadcast(self, event: dict):
        dead = []
        for q in self._listeners:
            try:
                q.put_nowait(event)
            except Exception:
                dead.append(q)
        for q in dead:
            self._listeners.remove(q)

    # ── Attendance CSV reading ─────────────────────────────────────────
    def get_attendance(self, date=None):
        """Read attendance records, optionally filtered by date."""
        root = os.path.join(os.path.dirname(__file__), "..")
        csv_path = os.path.join(root, "attendance.csv")
        records = []
        if not os.path.exists(csv_path):
            return records
        with open(csv_path, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) < 3 or parts[0] == "name":
                    continue
                record = {"name": parts[0], "date": parts[1], "time": parts[2]}
                if date is None or parts[1] == date:
                    records.append(record)
        return records
