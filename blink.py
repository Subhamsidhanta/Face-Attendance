import numpy as np
from scipy.spatial import distance as dist


def eye_aspect_ratio(landmarks, eye_indices):
    """
    Calculate the Eye Aspect Ratio (EAR) for blink detection.
    
    EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
    
    Args:
        landmarks: Array of facial landmarks (x, y) coordinates
        eye_indices: List of 6 landmark indices for the eye
                     [p1, p2, p3, p4, p5, p6] representing:
                     p1: left corner, p4: right corner
                     p2, p6: upper lid points
                     p3, p5: lower lid points
    
    Returns:
        float: Eye aspect ratio value (lower = more closed)
    """
    # Extract the eye landmark coordinates
    eye = landmarks[eye_indices]
    
    # Compute euclidean distances between vertical eye landmarks
    A = dist.euclidean(eye[1], eye[5])  # p2 to p6
    B = dist.euclidean(eye[2], eye[4])  # p3 to p5
    
    # Compute euclidean distance between horizontal eye landmarks
    C = dist.euclidean(eye[0], eye[3])  # p1 to p4
    
    # Compute the eye aspect ratio
    ear = (A + B) / (2.0 * C)
    
    return ear
