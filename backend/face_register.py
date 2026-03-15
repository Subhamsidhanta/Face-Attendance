"""
Face Registration — wraps register_face.py logic behind an API-friendly class.
Captures face images from the camera and saves them for training.
"""

import cv2
import os
import threading
import time


class FaceRegister:
    def __init__(self, camera_manager, dataset_dir=None):
        self._camera = camera_manager
        self._dataset_dir = dataset_dir or os.path.join(
            os.path.dirname(__file__), "..", "dataset"
        )
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # State
        self._capturing = False
        self._thread = None
        self._current_name = ""
        self._count = 0
        self._limit = 250
        self._lock = threading.Lock()

    # ── Controls ───────────────────────────────────────────────────────
    def start(self, name: str, limit: int = 250):
        """Start capturing face images for a new person."""
        if self._capturing:
            return False, "Already capturing — stop first."

        self._current_name = name
        self._count = 0
        self._limit = max(10, min(limit, 500))  # Clamp 10‥500
        save_path = os.path.join(self._dataset_dir, name)
        os.makedirs(save_path, exist_ok=True)

        self._capturing = True
        self._thread = threading.Thread(
            target=self._capture_loop, args=(save_path,), daemon=True
        )
        self._thread.start()
        return True, f"Capturing {self._limit} images for '{name}'"

    def stop(self):
        """Stop capturing early."""
        self._capturing = False
        if self._thread:
            self._thread.join(timeout=3)
        return self._count

    @property
    def status(self):
        return {
            "capturing": self._capturing,
            "name": self._current_name,
            "count": self._count,
            "limit": self._limit,
        }

    # ── Capture loop ───────────────────────────────────────────────────
    def _capture_loop(self, save_path):
        while self._capturing and self._count < self._limit:
            frame = self._camera.get_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                face = gray[y : y + h, x : x + w]
                self._count += 1
                cv2.imwrite(
                    os.path.join(save_path, f"{self._count}.jpg"), face
                )
                if self._count >= self._limit:
                    break

            time.sleep(0.08)  # ~12 fps for registration

        self._capturing = False

    # ── List registered people ─────────────────────────────────────────
    def list_registered(self):
        """Return list of registered people with image counts."""
        people = []
        if not os.path.exists(self._dataset_dir):
            return people
        for name in sorted(os.listdir(self._dataset_dir)):
            path = os.path.join(self._dataset_dir, name)
            if os.path.isdir(path):
                count = len([
                    f for f in os.listdir(path) if f.endswith(".jpg")
                ])
                people.append({"name": name, "imageCount": count})
        return people
