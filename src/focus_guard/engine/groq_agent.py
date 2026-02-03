import os
from groq import Groq
from opik import Opik, track
from typing import Dict, Any

# Configure Opik for Hackathon
os.environ["OPIK_PROJECT_NAME"] = "Commit Hackathon"

class GroqAgent:
    """Agent specialized in generating 'Toxic Coach' roasts using Groq."""
    
    
    def __init__(self, reasoning_model: str = "meta-llama/llama-4-maverick-17b-128e-instruct"):
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROG_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY or GROG_API_KEY is required.")
        
        self.client = Groq(api_key=api_key)
        self.reasoning_model = reasoning_model
        self.vision_model = "meta-llama/llama-4-scout-17b-16e-instruct"
        self.safety_model = "meta-llama/llama-guard-4-12b"
        
        self.system_prompt = (
            "Role: You are 'The Toxic Discipline Coach,' an AI agent designed to keep the user focused on their work.\n"
            "Context: The user is currently in a deep work session. You are monitoring them via computer vision metadata.\n"
            "Tone: Sarcastic, blunt, witty, but ultimately motivating. Use a 'tough love' approach.\n"
            "Instruction: When the user is distracted (e.g., looking at their phone, closing their eyes, or leaving their desk), "
            "generate a short, biting comment (under 15 words) to shame them back into productivity.\n"
            "Example: 'Is that TikTok more important than your career, Huy? Put the phone down.'"
        )

    @track(name="vision_analysis")
    def analyze_image(self, image_b64: str) -> str:
        """Stage 1: The Scout - Analyze the image to find the distraction."""
        try:
            # Prepare image URL format for Groq Vision
            image_url = f"data:image/jpeg;base64,{image_b64}"
            
            completion = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe what the person is doing in this image. Are they focused on the screen, looking at a phone, sleeping, or away? Be specific about objects like phones."},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                temperature=0.7,
                max_tokens=100
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    @track(name="generate_roast")
    def generate_roast(self, distraction_description: str) -> str:
        """Stage 2: The Toxic Coach - Generate a roast based on the vision description."""
        try:
            completion = self.client.chat.completions.create(
                model=self.reasoning_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"User is distracted. Vision Analysis: {distraction_description}"}
                ],
                temperature=0.8,
                max_tokens=60
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return "Get back to work."

    @track(name="safety_check")
    def check_safety(self, text: str) -> bool:
        """Stage 3: The HR Department - Ensure the roast is safe."""
        try:
            completion = self.client.chat.completions.create(
                model=self.safety_model,
                messages=[
                    {"role": "user", "content": text}
                ],
            )
            # Llama Guard returns 'safe' or 'unsafe\n<category>'
            result = completion.choices[0].message.content.strip()
            return result == "safe"
        except Exception:
            # Fail safe
            return True

    @track(name="process_distraction")
    def process_distraction(self, image_b64: str) -> Dict[str, Any]:
        """Orchestrates the 3-stage pipeline."""
        
        # 1. Vision
        description = self.analyze_image(image_b64)
        
        # 2. Reasoning
        roast = self.generate_roast(description)
        
        # 3. Safety (Optional - log warning but don't blocking for demo fun unless extremely unsafe)
        is_safe = self.check_safety(roast)
        if not is_safe:
            roast = "I have no words for your laziness. Back to work."
            
        return {
            "is_focused": False,
            "activity": description,
            "tease": roast,
            "pipeline": {
                "vision": description,
                "roast": roast,
                "safe": is_safe
            }
        }
