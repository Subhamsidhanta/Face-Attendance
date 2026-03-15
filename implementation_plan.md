# Full-Stack Face Attendance Application

Build a React frontend + FastAPI backend that wraps the existing face attendance Python scripts, adding live monitoring, unknown-person alerts, face registration, model training, and camera management.

## User Review Required

> [!IMPORTANT]
> **Camera access is server-side only.** The webcam is accessed by the Python backend (via OpenCV), not by the browser. The React frontend receives an MJPEG stream over HTTP. This means the backend and camera must be on the same machine.

> [!WARNING]
> The existing [attendance.csv](file:///e:/vs/Subham/projects/Face-Attendance/attendance.csv) has no header row. The new backend will add a `name,date,time` header if the file is empty or missing.

---

## Proposed Changes

### Backend — `backend/`

All backend files live in a new `backend/` directory at the project root. The backend is a **FastAPI** app that wraps the existing scripts.

---

#### [NEW] [main.py](file:///e:/vs/Subham/projects/Face-Attendance/backend/main.py)

FastAPI application entry point:
- CORS middleware (allow React dev server)
- Mount routers: `/api/camera`, `/api/attendance`, `/api/register`, `/api/train`, `/api/alerts`, `/api/unknown`, `/api/settings`
- Startup/shutdown lifecycle hooks (initialise/release camera)

#### [NEW] [camera_manager.py](file:///e:/vs/Subham/projects/Face-Attendance/backend/camera_manager.py)

Singleton camera controller:
- `list_cameras()` — probe indices 0–4, return available cameras with names (e.g. "Webcam 0", "USB Camera 1")
- `switch_camera(index)` — release current, open new
- `get_frame()` — thread-safe frame read from the active camera
- MJPEG streaming generator for `GET /api/camera/stream`

#### [NEW] [attendance_engine.py](file:///e:/vs/Subham/projects/Face-Attendance/backend/attendance_engine.py)

Refactored from [attendance_ai.py](file:///e:/vs/Subham/projects/Face-Attendance/attendance_ai.py) — runs as a background thread:
- Processes frames from `CameraManager`
- Liveness CNN check → blink detection → LBPH recognition
- On **recognised person**: mark attendance, emit SSE event
- On **unknown person** (confidence ≥ 60): trigger alert, capture 5–10 images with camera-name watermark burned into the image
- Duplicate guard reads [attendance.csv](file:///e:/vs/Subham/projects/Face-Attendance/attendance.csv) on startup to prevent same-day duplicates across restarts
- Exposes start/stop controls

#### [NEW] [face_register.py](file:///e:/vs/Subham/projects/Face-Attendance/backend/face_register.py)

Registration API:
- `POST /api/register/start` — body: `{ name, captureLimit }` (default 250, user-configurable)
- Captures grayscale face crops from the live camera, saves to `dataset/<name>/`
- `POST /api/register/stop` — stop early
- `GET /api/register/status` — returns `{ capturing, count, limit, name }`

#### [NEW] [trainer.py](file:///e:/vs/Subham/projects/Face-Attendance/backend/trainer.py)

- `POST /api/train` — runs LBPH training (same logic as [train_cnn.py](file:///e:/vs/Subham/projects/Face-Attendance/train_cnn.py)) in a background thread
- `GET /api/train/status` — returns `{ training, progress, message }`
- After training completes, hot-reloads the recognizer in `AttendanceEngine`

#### [NEW] [alert_manager.py](file:///e:/vs/Subham/projects/Face-Attendance/backend/alert_manager.py)

Unknown-person alert system:
- Fires when attendance engine detects an unknown face
- Captures 5–10 images, each watermarked with camera name + timestamp
- Saves to `unknown_captures/<timestamp>/`
- `GET /api/alerts` — SSE stream of alert events
- `POST /api/alerts/stop` — silence the current alert
- `GET /api/unknown` — list captured unknown-person image sets
- `GET /api/unknown/<folder>/<filename>` — serve individual captured images

#### [NEW] [requirements.txt](file:///e:/vs/Subham/projects/Face-Attendance/backend/requirements.txt)

```
fastapi
uvicorn[standard]
python-multipart
opencv-python
opencv-contrib-python
numpy
scipy
mediapipe
torch
```

---

### Frontend — `frontend/`

React app scaffolded with **Vite**. Dark, surveillance-console-inspired aesthetic.

---

#### [NEW] [src/App.jsx](file:///e:/vs/Subham/projects/Face-Attendance/frontend/src/App.jsx)

Root component with React Router:
- `/` → Dashboard (live feed + alerts + attendance)
- `/register` → Face Registration
- `/settings` → Camera & system settings
- `/unknown` → Unknown person gallery

#### [NEW] [src/index.css](file:///e:/vs/Subham/projects/Face-Attendance/frontend/src/index.css)

Design system:
- Dark background (`#0a0e17`), accent green (`#00ff88`) for "live/verified", red (`#ff3358`) for alerts
- Typography: **JetBrains Mono** for the surveillance/terminal feel, **Outfit** for headings
- CSS variables, utility classes, animation keyframes

#### [NEW] [src/components/LiveFeed.jsx](file:///e:/vs/Subham/projects/Face-Attendance/frontend/src/components/LiveFeed.jsx)

- Renders MJPEG stream as an `<img>` tag pointing to `/api/camera/stream`
- Overlays: camera name badge, recording indicator pulse, timestamp
- Connection status indicator

#### [NEW] [src/components/AlertPanel.jsx](file:///e:/vs/Subham/projects/Face-Attendance/frontend/src/components/AlertPanel.jsx)

- Listens to SSE `/api/alerts` for real-time unknown-person alerts
- Flashing red border + audio beep on alert
- **STOP** button → `POST /api/alerts/stop`
- Shows thumbnail of the unknown person

#### [NEW] [src/components/AttendanceLog.jsx](file:///e:/vs/Subham/projects/Face-Attendance/frontend/src/components/AttendanceLog.jsx)

- Live-updating table of today's attendance records
- Polls `GET /api/attendance` every 5s or listens to SSE

#### [NEW] [src/components/RegisterFace.jsx](file:///e:/vs/Subham/projects/Face-Attendance/frontend/src/components/RegisterFace.jsx)

- Form: name input + capture limit slider (10–500, default 250)
- Start/Stop capture buttons
- Live progress bar showing `count / limit`
- Shows live feed during registration

#### [NEW] [src/components/TrainModel.jsx](file:///e:/vs/Subham/projects/Face-Attendance/frontend/src/components/TrainModel.jsx)

- "Train Model" button → `POST /api/train`
- Progress/status indicator
- Lists registered persons from [dataset/](file:///e:/vs/Subham/projects/Face-Attendance/train_liveness.py#100-187) directory

#### [NEW] [src/components/CameraSettings.jsx](file:///e:/vs/Subham/projects/Face-Attendance/frontend/src/components/CameraSettings.jsx)

- Dropdown of available cameras (from `GET /api/camera/list`)
- Switch button → `POST /api/camera/change`
- Current camera indicator

#### [NEW] [src/components/UnknownGallery.jsx](file:///e:/vs/Subham/projects/Face-Attendance/frontend/src/components/UnknownGallery.jsx)

- Grid of captured unknown-person image sets
- Each card shows timestamp, camera name, thumbnail grid
- Lightbox view for full-size images

#### [NEW] [src/components/Sidebar.jsx](file:///e:/vs/Subham/projects/Face-Attendance/frontend/src/components/Sidebar.jsx)

- Navigation: Dashboard, Register, Unknown Gallery, Settings
- Active route indicator
- System status (camera status, model loaded, etc.)

#### [NEW] [src/services/api.js](file:///e:/vs/Subham/projects/Face-Attendance/frontend/src/services/api.js)

API client:
- Base URL config (default `http://localhost:8000`)
- Functions for every endpoint
- SSE connection helper for alerts

---

## Verification Plan

### Automated Tests

1. **Backend startup**
   ```bash
   cd e:\vs\Subham\projects\Face-Attendance\backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
   Confirm the server starts without errors on `http://localhost:8000`.

2. **Frontend startup**
   ```bash
   cd e:\vs\Subham\projects\Face-Attendance\frontend
   npm install
   npm run dev
   ```
   Confirm the dev server starts on `http://localhost:5173`.

3. **API endpoint smoke test** — Use browser to open:
   - `http://localhost:8000/api/camera/list` → returns JSON array of cameras
   - `http://localhost:8000/api/camera/stream` → MJPEG video stream
   - `http://localhost:8000/api/attendance` → returns attendance records

### Manual Verification

4. **Live feed** — Open the React dashboard, confirm the webcam stream renders in real-time.
5. **Camera switching** — Go to Settings, switch camera from the dropdown, confirm the feed changes.
6. **Registration flow** — Go to Register page, enter a name, set capture limit, start capture, watch progress bar fill, stop early if desired.
7. **Training flow** — Click "Train Model", watch the status update, confirm it completes successfully.
8. **Unknown person alert** — Point the camera at an unregistered face. Confirm the alert panel flashes, captured images appear in the Unknown Gallery with camera name watermarked.
9. **Alert stop** — Click the STOP button during an alert, confirm it silences.
