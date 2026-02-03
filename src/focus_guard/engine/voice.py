import pyttsx3

class VoiceAgent:
    """Agent specialized in delivering audio 'teasers' to the user."""
    
    def __init__(self, rate: int = 160):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        
        # Prefer a distinct voice if available (e.g., female voice for the 'guard' persona)
        voices = self.engine.getProperty('voices')
        if len(voices) > 1:
            self.engine.setProperty('voice', voices[1].id)

    def speak(self, text: str):
        """Converts text to speech and plays it immediately."""
        if not text:
            return
        self.engine.say(text)
        self.engine.runAndWait()
