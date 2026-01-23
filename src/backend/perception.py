"""
FocusBounty - Computer Vision Module
Detects: Face, Eyes, Attention level for discipline monitoring.
Uses OpenCV for fast face/eye detection.
"""

import cv2
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

_face_cascade = None
_eye_cascade = None


def get_face_cascade():
    """Load face cascade."""
    global _face_cascade
    if _face_cascade is None:
        _face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        print("✓ Face detector loaded")
    return _face_cascade


def get_eye_cascade():
    """Load eye cascade."""
    global _eye_cascade
    if _eye_cascade is None:
        _eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        print("✓ Eye detector loaded")
    return _eye_cascade


class PerceptionEngine:
    """
    Discipline AI Perception - monitors face and eye attention.
    """
    
    def __init__(self):
        self.away_start_time = None
        self.away_duration = 0.0
        self.eyes_closed_start = None
        self.eyes_closed_duration = 0.0
        self.focus_history = []
        self.last_face_position = None
        
    def analyze(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Analyze frame for discipline monitoring.
        
        Returns:
            {
                "face_detected": bool,
                "eyes_detected": bool,
                "eyes_open": bool,
                "looking_at_screen": bool,
                "away_duration": float,
                "attention_score": float (0-1),
                "discipline_status": str,
                "boxes": list
            }
        """
        now = datetime.now()
        height, width = frame.shape[:2]
        
        result = {
            "timestamp": now.isoformat(),
            "face_detected": False,
            "eyes_detected": False,
            "eyes_open": True,
            "looking_at_screen": True,
            "away_duration": 0.0,
            "eyes_closed_duration": 0.0,
            "attention_score": 1.0,
            "discipline_status": "focused",
            "boxes": []
        }
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Face detection
        face_cascade = get_face_cascade()
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(80, 80)
        )
        
        if len(faces) > 0:
            result["face_detected"] = True
            
            # Get largest face
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face
            
            # Add face box
            result["boxes"].append({
                "x": x / width,
                "y": y / height,
                "w": w / width,
                "h": h / height,
                "label": "face"
            })
            
            # Check if face is centered (looking at screen)
            face_center_x = x + w / 2
            screen_center_x = width / 2
            offset_ratio = abs(face_center_x - screen_center_x) / (width / 2)
            result["looking_at_screen"] = offset_ratio < 0.4
            
            # Eye detection within face region
            roi_gray = gray[y:y+h, x:x+w]
            eye_cascade = get_eye_cascade()
            eyes = eye_cascade.detectMultiScale(
                roi_gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(20, 20)
            )
            
            if len(eyes) >= 1:
                result["eyes_detected"] = True
                result["eyes_open"] = True
                self.eyes_closed_start = None
                self.eyes_closed_duration = 0.0
                
                # Add eye boxes
                for (ex, ey, ew, eh) in eyes[:2]:
                    result["boxes"].append({
                        "x": (x + ex) / width,
                        "y": (y + ey) / height,
                        "w": ew / width,
                        "h": eh / height,
                        "label": "eye"
                    })
            else:
                # Eyes not detected - might be closed or looking away
                result["eyes_detected"] = False
                if self.eyes_closed_start is None:
                    self.eyes_closed_start = now
                self.eyes_closed_duration = (now - self.eyes_closed_start).total_seconds()
                result["eyes_closed_duration"] = self.eyes_closed_duration
                
                # If eyes closed too long, might be sleepy
                if self.eyes_closed_duration > 3:
                    result["eyes_open"] = False
            
            # Reset away timer
            self.away_start_time = None
            self.away_duration = 0.0
            
            # Store face position
            self.last_face_position = (x, y, w, h)
            
        else:
            # No face detected - user is away
            if self.away_start_time is None:
                self.away_start_time = now
            self.away_duration = (now - self.away_start_time).total_seconds()
            result["away_duration"] = self.away_duration
            result["looking_at_screen"] = False
        
        # Calculate attention score
        attention = 1.0
        
        if not result["face_detected"]:
            attention = 0.0
        elif not result["looking_at_screen"]:
            attention = 0.4
        elif not result["eyes_detected"]:
            attention = 0.6
        elif self.eyes_closed_duration > 2:
            attention = 0.3
        
        # Smooth attention score
        self.focus_history.append(attention)
        if len(self.focus_history) > 10:
            self.focus_history.pop(0)
        
        result["attention_score"] = sum(self.focus_history) / len(self.focus_history)
        
        # Determine discipline status
        if result["away_duration"] > 30:
            result["discipline_status"] = "absent"
        elif result["away_duration"] > 10:
            result["discipline_status"] = "away"
        elif self.eyes_closed_duration > 5:
            result["discipline_status"] = "drowsy"
        elif not result["looking_at_screen"]:
            result["discipline_status"] = "distracted"
        elif result["attention_score"] < 0.5:
            result["discipline_status"] = "unfocused"
        else:
            result["discipline_status"] = "focused"
        
        return result


perception = PerceptionEngine()
