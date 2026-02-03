import os
import json
from google import genai
from google.genai import types
from typing import Dict, Any

class VisionAgent:
    """Agent specialized in detecting user focus and 'doom scrolling' via Computer Vision."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        api_key = os.getenv("GROG_API_KEY")
        if not api_key:
            raise ValueError("GROG_API_KEY is required.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def analyze(self, image_path: str) -> Dict[str, Any]:
        """Analyzes the image and returns structured data about user focus."""
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            prompt = (
                "Role: Focus & Productivity Coach.\n"
                "Task: Analyze the user's activity from the image.\n"
                "Focus Areas: \n"
                "- Detect 'doom scrolling' (obsessively scrolling on phone/social media).\n"
                "- Detect if the user is focused on their screen (coding, writing, reading).\n"
                "- Detect if the user is away or distracted.\n\n"
                "Objective: If distracted or doom scrolling, generate a sharp, witty tease to pull them back.\n\n"
                "Return JSON ONLY:\n"
                "{\n"
                '  "is_focused": boolean,\n'
                '  "is_doom_scrolling": boolean,\n'
                '  "activity": "string description",\n'
                '  "tease": "string wit teaser"\n'
                "}"
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                            types.Part.from_bytes(data=image_data, mime_type="image/jpeg"),
                        ],
                    ),
                ],
            )
            return self._parse_json(response.text)
        except Exception as e:
            return {"error": str(e), "is_focused": True, "tease": None}

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Clean and parse JSON from Gemini response."""
        try:
            cleaned = text.strip().strip('`').replace('json', '', 1).strip()
            return json.loads(cleaned)
        except:
            return {"error": "Parse failed", "is_focused": True, "tease": None}
