"""
Camera Manager — thread-safe singleton that owns the OpenCV VideoCapture.
Supports listing available cameras, switching, and MJPEG frame generation.
"""

import cv2
import threading
import time


class CameraManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialised = False
        return cls._instance

    def __init__(self):
        if self._initialised:
            return
        self._initialised = True
        self._cap = None
        self._current_index = 0
        self._current_name = "Webcam 0"
        self._frame = None
        self._frame_lock = threading.Lock()
        self._running = False
        self._read_thread = None

    # ── Camera discovery ───────────────────────────────────────────────
    @staticmethod
    def list_cameras(max_index: int = 5):
        """Probe camera indices 0‥max_index and return available ones."""
        cameras = []
        for i in range(max_index):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    backend = cap.getBackendName()
                    name = f"Camera {i} ({backend})"
                    cameras.append({"index": i, "name": name})
                cap.release()
        # Always include at least the default
        if not cameras:
            cameras.append({"index": 0, "name": "Webcam 0"})
        return cameras

    # ── Lifecycle ──────────────────────────────────────────────────────
    def open(self, index: int = 0):
        """Open a camera by index and start the background read loop."""
        self.close()
        self._cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            # Fallback without CAP_DSHOW
            self._cap = cv2.VideoCapture(index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera {index}")
        self._current_index = index
        self._current_name = f"Camera {index}"
        self._running = True
        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()

    def close(self):
        self._running = False
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2)
        if self._cap and self._cap.isOpened():
            self._cap.release()
        self._cap = None
        self._frame = None

    def switch(self, index: int):
        """Switch to a different camera."""
        self.open(index)

    # ── Frame access ──────────────────────────────────────────────────
    def _read_loop(self):
        fail_count = 0
        while self._running and self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if ret:
                with self._frame_lock:
                    self._frame = frame
                fail_count = 0
            else:
                fail_count += 1
                # Throttle on repeated failures to avoid log spam
                time.sleep(min(0.5 * fail_count, 5.0))

    def get_frame(self):
        """Return the latest frame (BGR numpy array) or None."""
        with self._frame_lock:
            return self._frame.copy() if self._frame is not None else None

    @property
    def current_index(self):
        return self._current_index

    @property
    def current_name(self):
        return self._current_name

    @property
    def is_open(self):
        return self._cap is not None and self._cap.isOpened()

    # ── MJPEG generator ───────────────────────────────────────────────
    def mjpeg_generator(self):
        """Yield MJPEG-encoded frames for streaming."""
        while self._running:
            frame = self.get_frame()
            if frame is None:
                time.sleep(0.03)
                continue
            ret, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + jpeg.tobytes()
                    + b"\r\n"
                )
            time.sleep(0.033)  # ~30 fps
