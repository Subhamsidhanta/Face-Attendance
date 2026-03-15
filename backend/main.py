"""
Face Attendance System — FastAPI Backend
========================================
Main application entry point. Mounts all API routes and manages
the lifecycle of the camera, attendance engine, alert system,
face registration, and model training.
"""

import asyncio
import json
import queue
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from pydantic import BaseModel

from camera_manager import CameraManager
from alert_manager import AlertManager
from attendance_engine import AttendanceEngine
from face_register import FaceRegister
from trainer import Trainer


# ── Shared instances ───────────────────────────────────────────────────
camera = CameraManager()
alert_mgr = AlertManager(camera, base_dir=os.path.join(os.path.dirname(__file__), "..", "unknown_captures"))
engine = AttendanceEngine(camera, alert_mgr)
registrar = FaceRegister(camera, dataset_dir=os.path.join(os.path.dirname(__file__), "..", "dataset"))
trainer = Trainer(
    dataset_dir=os.path.join(os.path.dirname(__file__), "..", "dataset"),
    models_dir=os.path.join(os.path.dirname(__file__), "..", "models"),
)


# ── Lifecycle ──────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — try camera 1 first (matches original scripts), then 0
    camera_opened = False
    for idx in [1, 0]:
        try:
            camera.open(idx)
            # Test if we can actually grab a frame
            import time as _time
            _time.sleep(0.5)
            test_frame = camera.get_frame()
            if test_frame is not None:
                print(f"[startup] Camera {idx} opened successfully")
                camera_opened = True
                break
            else:
                print(f"[startup] Camera {idx} opened but can't grab frames, trying next...")
                camera.close()
        except Exception as e:
            print(f"[startup] Camera {idx} failed: {e}")
    if not camera_opened:
        print("[startup] No working camera found. Use Settings to configure.")

    try:
        engine.load_models()
        print("[startup] Models loaded")
    except Exception as e:
        print(f"[startup] Could not load models: {e}")

    yield

    # Shutdown
    engine.stop()
    camera.close()
    print("[shutdown] Cleaned up")


app = FastAPI(title="Face Attendance API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════
# CAMERA ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/camera/stream")
def camera_stream():
    """MJPEG stream of the live camera feed."""
    if not camera.is_open:
        raise HTTPException(503, "Camera is not open")
    return StreamingResponse(
        camera.mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/camera/list")
def camera_list():
    """List available cameras."""
    return camera.list_cameras()


class CameraSwitch(BaseModel):
    index: int

@app.post("/api/camera/change")
def camera_change(body: CameraSwitch):
    """Switch to a different camera."""
    try:
        camera.switch(body.index)
        # Restart engine if it was running
        was_running = engine.is_running
        if was_running:
            engine.stop()
            engine.start()
        return {"ok": True, "camera": camera.current_name}
    except RuntimeError as e:
        raise HTTPException(400, str(e))


@app.get("/api/camera/status")
def camera_status():
    return {
        "open": camera.is_open,
        "index": camera.current_index,
        "name": camera.current_name,
    }


# ═══════════════════════════════════════════════════════════════════════
# ATTENDANCE ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/attendance")
def get_attendance(date: str = Query(default=None)):
    """Get attendance records, optionally filtered by date."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    return engine.get_attendance(date)


@app.post("/api/attendance/start")
def start_monitoring():
    """Start the attendance monitoring engine."""
    engine.start()
    return {"ok": True, "message": "Monitoring started"}


@app.post("/api/attendance/stop")
def stop_monitoring():
    """Stop the attendance monitoring engine."""
    engine.stop()
    return {"ok": True, "message": "Monitoring stopped"}


@app.get("/api/attendance/status")
def monitoring_status():
    return engine.status


# ═══════════════════════════════════════════════════════════════════════
# REGISTRATION ROUTES
# ═══════════════════════════════════════════════════════════════════════

class RegisterStart(BaseModel):
    name: str
    captureLimit: int = 250

@app.post("/api/register/start")
def register_start(body: RegisterStart):
    ok, msg = registrar.start(body.name, body.captureLimit)
    if not ok:
        raise HTTPException(409, msg)
    return {"ok": True, "message": msg}


@app.post("/api/register/stop")
def register_stop():
    count = registrar.stop()
    return {"ok": True, "captured": count}


@app.get("/api/register/status")
def register_status():
    return registrar.status


@app.get("/api/register/list")
def registered_list():
    """List all registered people with image counts."""
    return registrar.list_registered()


# ═══════════════════════════════════════════════════════════════════════
# TRAINING ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.post("/api/train")
def train_model():
    ok, msg = trainer.start_training()
    if not ok:
        raise HTTPException(409, msg)
    return {"ok": True, "message": msg}


@app.get("/api/train/status")
def train_status():
    return trainer.status


@app.post("/api/train/reload")
def reload_models():
    """Reload models after training. Call this after training completes."""
    engine.load_models()
    return {"ok": True, "message": "Models reloaded"}


# ═══════════════════════════════════════════════════════════════════════
# ALERT ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/alerts")
async def alert_stream():
    """SSE stream of alert events."""
    q = queue.Queue()
    alert_mgr.add_listener(q)
    engine.add_listener(q)

    async def event_generator():
        try:
            while True:
                try:
                    event = q.get_nowait()
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    yield ": heartbeat\n\n"
                    await asyncio.sleep(1)
        finally:
            alert_mgr.remove_listener(q)
            engine.remove_listener(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/alerts/stop")
def alert_stop():
    alert_mgr.stop()
    return {"ok": True}


@app.get("/api/alerts/active")
def alert_active():
    return {"active": alert_mgr.is_active}


# ═══════════════════════════════════════════════════════════════════════
# UNKNOWN CAPTURES ROUTES
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/unknown")
def list_unknown():
    """List all captured unknown-person image sets."""
    return alert_mgr.list_captures()


@app.get("/api/unknown/{folder}/{filename}")
def get_unknown_image(folder: str, filename: str):
    """Serve a specific captured image."""
    base = os.path.join(os.path.dirname(__file__), "..", "unknown_captures")
    filepath = os.path.join(base, folder, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "Image not found")
    return FileResponse(filepath, media_type="image/jpeg")


# ═══════════════════════════════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "camera": camera.is_open,
        "engine": engine.is_running,
        "modelsLoaded": engine.models_loaded,
    }
