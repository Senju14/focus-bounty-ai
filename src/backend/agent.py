"""
FocusBounty - Discipline AI Agent
Strict monitoring with face/eye tracking and firm interventions.
"""

import os
import time
import random
from datetime import datetime
from typing import Dict, Any, List

import opik
from opik import track, opik_context

from dotenv import load_dotenv
load_dotenv()

OPIK_API_KEY = os.getenv("OPIK_API_KEY")
OPIK_PROJECT = "FocusBounty-Hackathon"

if OPIK_API_KEY:
    opik.configure(api_key=OPIK_API_KEY)
    print(f"✓ Opik configured - Project: {OPIK_PROJECT}")


# Discipline messages - strict but motivating
DISCIPLINE_MESSAGES = {
    "focused": [
        "Good. Keep your eyes on the prize! 👁️",
        "Excellent focus! Don't let up! 💪",
        "That's what I like to see! Stay sharp! ⚡",
    ],
    "distracted": [
        "Hey! Eyes on the screen! 👀",
        "I see you looking away. Focus! 🎯",
        "Where are you looking? Get back to work! 😤",
    ],
    "drowsy": [
        "Wake up! I see your eyes closing! ☕",
        "Are you sleeping?! Stay alert! 😠",
        "Eyes OPEN! Take a break if you need to! 💥",
    ],
    "away": [
        "Where did you go? Get back here! 🔍",
        "Your desk is empty! Return immediately! ⚠️",
        "I'm watching an empty chair. Not acceptable! 😤",
    ],
    "absent": [
        "MISSING IN ACTION! Return to your post! 🚨",
        "You've been gone too long! This is unacceptable! 😡",
        "Discipline requires PRESENCE! Come back NOW! 🔥",
    ],
    "welcome_back": [
        "Finally! You're back. Now FOCUS! 💪",
        "Good to see you. Let's make up for lost time! ⚡",
        "Back to work! No more breaks! 🎯",
    ],
    "encouragement": [
        "Outstanding discipline! Keep it up! 🏆",
        "You're crushing it! Stay strong! 💪",
        "Excellent work ethic! Keep going! 🌟",
    ],
}


class FocusAgent:
    """
    Discipline AI Agent - strict monitoring with firm interventions.
    Tracks face, eyes, and attention for maximum productivity.
    """
    
    def __init__(self, strictness: int = 5):
        self.strictness = strictness
        self.decision_history: List[Dict] = []
        self.session_start = datetime.now()
        self.session_id = f"session_{int(time.time())}"
        self.focus_streak = 0
        self.last_status = "focused"
        self.last_intervention_time = datetime.now()
        self.total_away_time = 0.0
        self.total_distracted_time = 0.0
        
    @track(name="discipline_decision", capture_input=True, capture_output=True, project_name=OPIK_PROJECT)
    def decide(self, perception_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main decision function for discipline monitoring."""
        start_time = time.time()
        
        try:
            opik_context.update_current_trace(
                input={
                    "perception": perception_data,
                    "strictness": self.strictness,
                    "session_id": self.session_id
                },
                metadata={
                    "session_duration_sec": (datetime.now() - self.session_start).total_seconds(),
                    "project": OPIK_PROJECT
                }
            )
        except Exception:
            pass
        
        decision = self._make_decision(perception_data)
        
        latency_ms = (time.time() - start_time) * 1000
        decision["latency_ms"] = latency_ms
        decision["timestamp"] = datetime.now().isoformat()
        decision["focus_streak"] = self.focus_streak
        
        try:
            opik_context.update_current_trace(
                output=decision,
                metadata={
                    "latency_ms": latency_ms,
                    "intervention_triggered": decision.get("should_intervene", False),
                    "discipline_status": decision.get("discipline_status", "unknown")
                }
            )
        except Exception:
            pass
        
        self.decision_history.append(decision)
        return decision
    
    def _make_decision(self, perception: Dict) -> Dict[str, Any]:
        """Make discipline decision based on perception."""
        status = perception.get("discipline_status", "focused")
        attention = perception.get("attention_score", 1.0)
        away_duration = perception.get("away_duration", 0)
        eyes_closed = perception.get("eyes_closed_duration", 0)
        
        now = datetime.now()
        since_last = (now - self.last_intervention_time).total_seconds()
        
        # Cooldown between interventions (based on strictness)
        cooldown = max(3, 15 - self.strictness)
        
        # Track statistics
        if status in ["away", "absent"]:
            self.total_away_time += 1
            self.focus_streak = 0
        elif status in ["distracted", "unfocused"]:
            self.total_distracted_time += 1
            self.focus_streak = 0
        elif status == "focused":
            self.focus_streak += 1
        
        # Welcome back after being away
        if self.last_status in ["away", "absent"] and status == "focused":
            self.last_status = status
            self.last_intervention_time = now
            return {
                "should_intervene": True,
                "intervention_type": "welcome_back",
                "message": random.choice(DISCIPLINE_MESSAGES["welcome_back"]),
                "severity": "medium",
                "discipline_status": status,
                "tts_enabled": True
            }
        
        self.last_status = status
        
        # No intervention if focused and not time for encouragement
        if status == "focused":
            # Encourage every 2 minutes of focus (strictness affects frequency)
            encourage_interval = max(60, 180 - self.strictness * 10)
            if self.focus_streak > 0 and self.focus_streak % encourage_interval == 0 and since_last > 30:
                self.last_intervention_time = now
                return {
                    "should_intervene": True,
                    "intervention_type": "encouragement",
                    "message": random.choice(DISCIPLINE_MESSAGES["encouragement"]),
                    "severity": "positive",
                    "discipline_status": status,
                    "tts_enabled": True
                }
            return {
                "should_intervene": False,
                "intervention_type": "none",
                "message": "",
                "severity": "none",
                "discipline_status": status,
                "tts_enabled": False
            }
        
        # Check cooldown
        if since_last < cooldown:
            return {
                "should_intervene": False,
                "intervention_type": "none",
                "message": "",
                "severity": "none",
                "discipline_status": status,
                "tts_enabled": False
            }
        
        # Determine severity based on status and strictness
        severity = "low"
        if status == "absent" or away_duration > 30:
            severity = "critical"
        elif status == "drowsy" or eyes_closed > 3:
            severity = "high"
        elif status == "away" or away_duration > 10:
            severity = "medium"
        elif status == "distracted":
            severity = "low" if self.strictness < 5 else "medium"
        
        # Get appropriate message
        messages = DISCIPLINE_MESSAGES.get(status, DISCIPLINE_MESSAGES["distracted"])
        
        self.last_intervention_time = now
        
        return {
            "should_intervene": True,
            "intervention_type": status,
            "message": random.choice(messages),
            "severity": severity,
            "discipline_status": status,
            "tts_enabled": severity in ["medium", "high", "critical"]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        if not self.decision_history:
            return {"total_decisions": 0}
        
        interventions = [d for d in self.decision_history if d.get("should_intervene")]
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        return {
            "session_id": self.session_id,
            "total_decisions": len(self.decision_history),
            "total_interventions": len(interventions),
            "intervention_rate": len(interventions) / len(self.decision_history) if self.decision_history else 0,
            "focus_streak": self.focus_streak,
            "total_away_time": self.total_away_time,
            "total_distracted_time": self.total_distracted_time,
            "focus_percentage": max(0, 100 - (self.total_away_time + self.total_distracted_time) / max(1, session_duration) * 100),
            "session_duration_minutes": session_duration / 60,
            "opik_project": OPIK_PROJECT
        }
