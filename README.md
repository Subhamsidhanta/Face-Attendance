# Face Attendance System with Anti-Spoofing

An AI-powered face recognition attendance system with **liveness detection** and **blink verification** to prevent spoofing attacks.

## Features

- **Face Recognition** - LBPH (Local Binary Patterns Histograms) based face recognition
- **Liveness Detection** - CNN model to detect real faces vs photos/screens
- **Blink Detection** - Eye Aspect Ratio (EAR) based blink counting using MediaPipe
- **Anti-Spoofing** - Requires both liveness check and blink verification before marking attendance
- **Attendance Logging** - Automatic CSV logging with name, date, and timestamp

## Project Structure

```
Face_Attendance_Project/
├── backend/                   # FastAPI REST backend
│   ├── main.py                # API entry point
│   ├── camera_manager.py      # Camera listing, switching, MJPEG streaming
│   ├── attendance_engine.py   # Real-time recognition pipeline
│   ├── alert_manager.py       # Unknown-person alert + image capture
│   ├── face_register.py       # Face registration API
│   ├── trainer.py             # LBPH model training API
│   └── requirements.txt       # Backend Python deps
├── frontend/                  # React (Vite) web UI
│   ├── src/
│   │   ├── pages/             # Dashboard, Register, Settings, Unknown
│   │   ├── components/        # LiveFeed, AlertPanel, CameraSettings, etc.
│   │   └── services/api.js    # API client
│   └── index.html
├── attendance_ai.py           # Original standalone attendance script
├── register_face.py           # Original standalone registration script
├── train_cnn.py               # Train face recognition model (LBPH)
├── train_liveness.py          # Train liveness detection CNN
├── blink.py                   # Eye Aspect Ratio calculation
├── attendance.csv             # Attendance records
├── dataset/                   # Registered face images
│   └── <person_name>/         # Images per person (configurable)
├── unknown_captures/          # Captured unknown-person images
└── models/
    ├── recognizer.yml         # Trained LBPH model
    ├── liveness_model.pth     # Trained liveness CNN (PyTorch)
    └── names.txt              # List of registered names
```

## Requirements

- Python 3.10+
- Node.js 18+
- Webcam

### Python Dependencies

```
opencv-python
opencv-contrib-python
numpy
scipy
mediapipe
torch
fastapi
uvicorn[standard]
python-multipart
```

## Installation & Running

### Option A: Full-Stack Web App (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Face_Attendance_Project.git
   cd Face_Attendance_Project
   ```

2. **Install backend dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Start the backend** (Terminal 1)
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   > **Conda users:** Replace `uvicorn` with your env's Python:
   > ```bash
   > C:\Users\<you>\miniconda3\envs\<env>\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   > ```

5. **Start the frontend** (Terminal 2)
   ```bash
   cd frontend
   npm run dev
   ```

6. **Open** [http://localhost:5173](http://localhost:5173) in your browser.

#### Web App Features

| Page | What it does |
|------|-------------|
| **Dashboard** | Live camera feed, start/stop monitoring, alert panel, attendance log |
| **Register Face** | Enter name, set capture limit (10–500), capture face images |
| **Unknown Gallery** | View captured images of unrecognised faces (watermarked with camera name) |
| **Settings** | Switch cameras, view system info |

**Workflow:**
1. Go to **Register Face** → enter a name → adjust the image count slider → click **Start Capture**
2. Click **Train Model** after registration
3. Go to **Dashboard** → click **Start Monitoring**
4. Blink 3 times in front of the camera → attendance is marked automatically
5. Unknown faces trigger an **alert** with image capture → view in **Unknown Gallery**

---

### Option B: Standalone CLI Scripts (Original)

1. **Register a face** — captures face images for training:
   ```bash
   python register_face.py
   ```

2. **Train the model** — trains LBPH recognizer on all registered faces:
   ```bash
   python train_cnn.py
   ```

3. **Run attendance** — real-time face recognition with anti-spoofing:
   ```bash
   python attendance_ai.py
   ```

4. **(Optional) Train liveness model** — if you have a `liveness_dataset/real/` and `liveness_dataset/fake/` directory:
   ```bash
   python train_liveness.py
   ```

Press `ESC` to exit any script.

## How It Works

### Face Recognition
Uses OpenCV's LBPH (Local Binary Patterns Histograms) recognizer to identify registered faces with confidence scoring.

### Liveness Detection
A PyTorch CNN model analyzes the face region to distinguish between:
- **Real faces** - Live person in front of camera
- **Fake faces** - Printed photos, screen displays, masks

### Blink Detection
Uses MediaPipe Face Mesh to track eye landmarks and calculate the Eye Aspect Ratio (EAR):

```
EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
```

When EAR drops below threshold (0.20), a blink is detected.

### Anti-Spoofing Pipeline
```
Face Detection → Liveness Check → Blink Count (≥3) → Face Recognition → Mark Attendance
```

## Output

Attendance is saved to `attendance.csv`:
```csv
name,date,time
John,2026-02-19,10:30:45
Jane,2026-02-19,10:32:12
```

## Camera Configuration

By default, the system uses camera index `1`. To change this, modify the following line in the scripts:

```python
cap = cv2.VideoCapture(1)  # Change to 0 for default webcam
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera not opening | Change `VideoCapture(1)` to `VideoCapture(0)` |
| Face not detected | Ensure proper lighting and face the camera directly |
| Low recognition accuracy | Register more face images with varied angles |
| Blinks not counting | Ensure full face is visible and blink clearly |

## Technologies Used

- **OpenCV** - Face detection & recognition
- **PyTorch** - Liveness detection CNN
- **MediaPipe** - Face mesh for blink detection
- **NumPy/SciPy** - Numerical computations

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
