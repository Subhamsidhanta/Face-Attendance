import cv2
import numpy as np
import mediapipe as mp
import torch
from datetime import datetime
from blink import eye_aspect_ratio
from train_liveness import LivenessModel

# ===== LOAD NAME LIST =====
with open("models/names.txt") as f:
    names = [line.strip() for line in f.readlines()]

# ===== LOAD RECOGNIZER =====
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("models/recognizer.yml")

# ===== LOAD LIVENESS CNN (PyTorch) =====
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
liveness_model = LivenessModel().to(device)
liveness_model.load_state_dict(torch.load("models/liveness_model.pth", map_location=device))
liveness_model.eval()

# ===== FACE DETECTOR =====
faceCascade = cv2.CascadeClassifier(
    cv2.data.haarcascades+'haarcascade_frontalface_default.xml'
)

# ===== MEDIAPIPE FACE MESH =====
mp_face_mesh = mp.solutions.face_mesh.FaceMesh()

# ===== TRACK MARKED ATTENDANCE =====
marked_attendees = set()  # Prevent duplicate attendance marking

def markAttendance(name):
    """Mark attendance only if not already marked today."""
    if name in marked_attendees:
        return False
    
    with open("attendance.csv", "a+") as f:
        date = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M:%S")
        f.write(f"{name},{date},{time}\n")
    
    marked_attendees.add(name)
    print(f"✅ Attendance marked for {name}")
    return True

cap = cv2.VideoCapture(1)

blink_counter = 0
BLINK_THRESHOLD = 3  # Number of blinks required
EAR_THRESHOLD = 0.20  # Eye aspect ratio threshold for blink
eye_closed = False  # Track eye state for proper blink detection

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = frame.shape[:2]

    faces = faceCascade.detectMultiScale(gray, 1.3, 5)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = mp_face_mesh.process(rgb)

    for (x, y, ww, hh) in faces:

        face = frame[y:y+hh, x:x+ww]

        # ===== LIVENESS CHECK (PyTorch) =====
        face_resized = cv2.resize(face, (64, 64))
        face_resized = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
        face_resized = face_resized / 255.0
        face_resized = np.transpose(face_resized, (2, 0, 1))  # HWC to CHW
        face_tensor = torch.from_numpy(face_resized).float().unsqueeze(0).to(device)
        
        with torch.no_grad():
            live_pred = liveness_model(face_tensor)
        live = True if live_pred[0][0].item() > 0.5 else False

        # ===== BLINK CHECK =====
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = np.array(
                    [(lm.x*w, lm.y*h) for lm in face_landmarks.landmark]
                )

                left_eye = [33, 160, 158, 133, 153, 144]
                ear = eye_aspect_ratio(landmarks, left_eye)

                # Proper blink detection: count when eye closes then opens
                if ear < EAR_THRESHOLD:
                    eye_closed = True
                elif eye_closed and ear >= EAR_THRESHOLD:
                    blink_counter += 1
                    eye_closed = False

        # ===== FACE RECOGNITION & ATTENDANCE =====
        if live and blink_counter >= BLINK_THRESHOLD:

            id, conf = recognizer.predict(gray[y:y+hh, x:x+ww])

            if conf < 60:
                name = names[id]

                if markAttendance(name):
                    # Reset blink counter after successful attendance
                    blink_counter = 0

                cv2.putText(frame, f"{name} - VERIFIED", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Unknown", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 0, 255), 2)
        else:
            # Show status
            status = f"Blinks: {blink_counter}/{BLINK_THRESHOLD}"
            cv2.putText(frame, status, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 255, 0), 2)

        # Draw rectangle: green if live, red if not
        color = (0, 255, 0) if live else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x+ww, y+hh), color, 2)

    cv2.imshow("AI Face Attendance", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
