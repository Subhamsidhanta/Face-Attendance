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
├── attendance_ai.py       # Main attendance system
├── register_face.py       # Face registration script
├── train_cnn.py           # Train face recognition model
├── train_liveness.py      # Train liveness detection CNN
├── blink.py               # Eye Aspect Ratio calculation
├── attendance.csv         # Attendance records
├── dataset/               # Registered face images
│   └── <person_name>/     # 250 images per person
└── models/
    ├── recognizer.yml     # Trained LBPH model
    ├── liveness_model.pth # Trained liveness CNN (PyTorch)
    └── names.txt          # List of registered names
```

## Requirements

- Python 3.10+
- Webcam

### Dependencies

```
opencv-python
opencv-contrib-python
numpy
scipy
mediapipe
torch
```

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Face_Attendance_Project.git
   cd Face_Attendance_Project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv env
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     env\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source env/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install opencv-python opencv-contrib-python numpy scipy mediapipe torch
   ```

## Usage

### Step 1: Register a New Face

Captures 250 face images for training.

```bash
python register_face.py
```

- Enter the person's name when prompted
- Face the camera and move slightly for varied angles
- Press `ESC` to stop early

### Step 2: Train the Recognition Model

Trains the LBPH face recognizer on all registered faces.

```bash
python train_cnn.py
```

### Step 3: (Optional) Train Liveness Model

If you have a liveness dataset with real/fake images:

```bash
python train_liveness.py
```

**Dataset structure:**
```
liveness_dataset/
├── real/    # Real face images
└── fake/    # Spoofed images (photos, screens)
```

### Step 4: Run Attendance System

```bash
python attendance_ai.py
```

**Verification Process:**
1. Face is detected using Haar Cascade
2. Liveness is checked using CNN (green box = live, red = spoof)
3. User must blink **3 times** to prove they are real
4. Face is recognized and attendance is marked
5. Attendance is logged to `attendance.csv`

Press `ESC` to exit.

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
