"""
FocusBounty - Action Executor
Handles interventions: Audio, Discord, UI notifications
"""

import os
import requests
from typing import Dict, Any

from dotenv import load_dotenv
load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


# Pre-defined messages
MESSAGES = {
    "gentle": [
        "Hey, just a friendly reminder to stay focused! 💪",
        "Quick phone check? Let's get back to work!",
        "You're doing great, keep the momentum going!",
    ],
    "audio_warning": [
        "Put that phone down and get back to work!",
        "I see you scrolling. Was that important?",
        "Your phone isn't going to finish your work.",
    ],
    "discord_shame": [
        "🚨 SHAME ALERT: Someone got caught using their phone!",
        "📱 Phone detected! Get back to work!",
        "👀 I see you procrastinating...",
    ],
    "toxic_coach": [
        "Seriously? The phone AGAIN? I expected better.",
        "Champions don't scroll social media during work.",
        "Your future self is disappointed. Get. Back. To. Work.",
    ],
    "break_suggestion": [
        "You've been working hard! Take a 5-minute break.",
        "Time to rest your eyes. Look away from the screen.",
        "Good work! Short break to recharge?",
    ],
    "posture": [
        "Sit up straight! Your back will thank you.",
        "Posture check! Straighten up.",
        "I see that slouch. Fix your posture!",
    ],
}


def get_message(intervention_type: str, custom_message: str = None) -> str:
    """Get intervention message"""
    if custom_message:
        return custom_message
    
    import random
    messages = MESSAGES.get(intervention_type, MESSAGES["gentle"])
    return random.choice(messages)


def execute_action(decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the intervention action
    
    Returns:
        {"success": bool, "action": str, "message": str}
    """
    intervention_type = decision.get("intervention_type", "none")
    custom_message = decision.get("message", "")
    
    if intervention_type == "none":
        return {"success": True, "action": "none", "message": ""}
    
    message = get_message(intervention_type, custom_message)
    result = {"success": False, "action": intervention_type, "message": message}
    
    # Execute based on type
    if intervention_type == "discord_shame":
        result["success"] = send_discord_notification(message, decision)
    elif intervention_type in ["audio_warning", "toxic_coach"]:
        result["success"] = play_audio(message)
    else:
        # UI notification (handled by frontend)
        result["success"] = True
    
    return result


def send_discord_notification(message: str, context: Dict = None) -> bool:
    """Send notification to Discord webhook"""
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook not configured")
        return False
    
    try:
        payload = {
            "embeds": [{
                "title": "🎯 FocusBounty Alert",
                "description": message,
                "color": 0xFF6B6B,  # Red
                "footer": {"text": "Stay focused! 💪"}
            }]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"Discord error: {e}")
        return False


def play_audio(message: str) -> bool:
    """Play text-to-speech audio"""
    try:
        # Try pyttsx3 for TTS
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.say(message)
        engine.runAndWait()
        return True
    except ImportError:
        print(f"[TTS not available] Would say: {message}")
        return True  # Consider success even without TTS
    except Exception as e:
        print(f"Audio error: {e}")
        return False
