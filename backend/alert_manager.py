"""
Alert Manager — handles unknown-person alerts and image capture.
"""

import cv2
import os
import time
import threading
from datetime import datetime


class AlertManager:
    def __init__(self, camera_manager, base_dir="unknown_captures"):
        self._camera = camera_manager
        self._base_dir = base_dir
        self._active = False
        self._alert_id = None
        self._listeners = []  # SSE listeners
        self._lock = threading.Lock()
        self._capture_thread = None
        os.makedirs(base_dir, exist_ok=True)

    # ── Alert lifecycle ────────────────────────────────────────────────
    def trigger(self, face_crop=None):
        """
        Trigger an unknown-person alert.
        Captures 5-10 images with camera name watermark.
        Returns the alert id (timestamp folder name).
        """
        with self._lock:
            if self._active:
                # Reinforce: tell frontend alert is still ongoing
                self._broadcast({
                    "type": "alert_persist",
                    "alert_id": self._alert_id,
                    "timestamp": datetime.now().isoformat(),
                })
                return self._alert_id
            self._active = True

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._alert_id = ts
        folder = os.path.join(self._base_dir, ts)
        os.makedirs(folder, exist_ok=True)

        # Broadcast event
        self._broadcast({
            "type": "alert_start",
            "alert_id": ts,
            "timestamp": datetime.now().isoformat(),
            "camera": self._camera.current_name,
        })

        # Start capture in background
        self._capture_thread = threading.Thread(
            target=self._capture_images, args=(folder,), daemon=True
        )
        self._capture_thread.start()
        return ts

    def stop(self):
        """Silence the current alert."""
        with self._lock:
            self._active = False
        self._broadcast({
            "type": "alert_stop",
            "alert_id": self._alert_id,
            "timestamp": datetime.now().isoformat(),
        })

    @property
    def is_active(self):
        return self._active

    # ── Image capture with watermark ───────────────────────────────────
    def _capture_images(self, folder, count=8):
        """Capture `count` images (5-10 range) with camera name watermark."""
        captured = 0
        for i in range(count):
            if not self._active:
                break
            frame = self._camera.get_frame()
            if frame is None:
                time.sleep(0.3)
                continue

            # Burn camera name + timestamp into the image
            cam_name = self._camera.current_name
            ts_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            watermark = f"{cam_name} | {ts_text}"

            h, w = frame.shape[:2]
            # Dark backdrop strip at bottom
            cv2.rectangle(frame, (0, h - 36), (w, h), (0, 0, 0), -1)
            cv2.putText(
                frame, watermark, (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA,
            )

            filename = f"unknown_{i + 1}.jpg"
            cv2.imwrite(os.path.join(folder, filename), frame)
            captured += 1
            time.sleep(0.5)  # Space out captures

        self._broadcast({
            "type": "capture_complete",
            "alert_id": os.path.basename(folder),
            "count": captured,
        })

    # ── List captured unknown sets ─────────────────────────────────────
    def list_captures(self):
        """Return list of capture folders with metadata."""
        captures = []
        if not os.path.exists(self._base_dir):
            return captures
        for folder_name in sorted(os.listdir(self._base_dir), reverse=True):
            folder_path = os.path.join(self._base_dir, folder_name)
            if not os.path.isdir(folder_path):
                continue
            images = [f for f in os.listdir(folder_path) if f.endswith(".jpg")]
            captures.append({
                "id": folder_name,
                "count": len(images),
                "images": images,
                "timestamp": folder_name,
            })
        return captures

    # ── SSE broadcast ──────────────────────────────────────────────────
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
