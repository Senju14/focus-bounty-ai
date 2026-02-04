"""
FocusGuard AI - Groq Agent
3-stage agentic pipeline: Vision -> Reasoning -> Safety
"""

import os
from groq import Groq
from opik import track
from typing import Dict, Any

os.environ["OPIK_PROJECT_NAME"] = "FocusGuard AI"


# =============================================================================
# Configuration
# =============================================================================

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
REASONING_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
SAFETY_MODEL = "meta-llama/llama-guard-4-12b"

SYSTEM_PROMPT = """Role: You are 'The Toxic Homie Coach' - a brutally honest bestie who roasts users back to focus.

Vibe: Gen-Z energy, meme-lord humor, uses slang like 'homie', 'dude', 'bro', 'nah fr', 'lowkey', 'no cap', 'sus', 'bruh moment'.
Tone: Savage but caring. Think: Your best friend who drags you but wants you to win.

Rules:
- Keep it under 15 words
- Use trendy slang naturally (not forced)
- Reference current culture: TikTok brain rot, doom scrolling, main character syndrome, touch grass
- Mix roast with motivation
- Vary the style: sometimes short punchy, sometimes dramatic

Examples:
- 'Bro you gotta lock in fr, that phone ain't paying your bills 💀'
- 'Nah homie, focus mode or I'm telling everyone you're a NPC'
- 'Dude. The grind doesn't grind itself. Back to work.'
- 'Main character energy means WORKING not scrolling, bestie'
- 'Touch grass later, touch keyboard now. Let's cook 🔥'
- 'Lowkey disappointed rn. You're better than this, lock in.'
- 'Bruh moment detected. Alt+Tab back to productivity.'"""


# =============================================================================
# Agent Class
# =============================================================================

class GroqAgent:
    """Agent for generating personalized roasts using Groq's LPU."""
    
    def __init__(self, reasoning_model: str = REASONING_MODEL):
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROG_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY or GROG_API_KEY is required.")
        
        self.client = Groq(api_key=api_key)
        self.reasoning_model = reasoning_model
        self.vision_model = VISION_MODEL
        self.safety_model = SAFETY_MODEL
        self.system_prompt = SYSTEM_PROMPT

    # =========================================================================
    # Stage 1: Vision Analysis
    # =========================================================================

    @track(name="vision_analysis")
    def analyze_image(self, image_b64: str) -> str:
        """Analyze webcam frame to detect user activity."""
        try:
            image_url = f"data:image/jpeg;base64,{image_b64}"
            
            completion = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Describe what the person is doing. Are they focused on screen, looking at phone, sleeping, or away?"
                        },
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }],
                temperature=0.7,
                max_tokens=100
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    # =========================================================================
    # Stage 2: Roast Generation
    # =========================================================================

    @track(name="generate_roast")
    def generate_roast(self, distraction_description: str) -> str:
        """Generate a witty roast based on the vision analysis."""
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
        except Exception:
            return "Get back to work."

    # =========================================================================
    # Stage 3: Safety Check
    # =========================================================================

    @track(name="safety_check")
    def check_safety(self, text: str) -> bool:
        """Verify roast is safe using Llama Guard."""
        try:
            completion = self.client.chat.completions.create(
                model=self.safety_model,
                messages=[{"role": "user", "content": text}],
            )
            result = completion.choices[0].message.content.strip()
            return result == "safe"
        except Exception:
            return True

    # =========================================================================
    # Pipeline Orchestration
    # =========================================================================

    @track(name="process_distraction")
    def process_distraction(self, image_b64: str) -> Dict[str, Any]:
        """Run the full 3-stage pipeline."""
        # Stage 1: Vision
        description = self.analyze_image(image_b64)
        
        # Stage 2: Reasoning
        roast = self.generate_roast(description)
        
        # Stage 3: Safety
        is_safe = self.check_safety(roast)
        if not is_safe:
            roast = "I have no words for your laziness. Back to work."
            
        return {
            "is_focused": False,
            "activity": description,
            "tease": roast,
            "safe": is_safe
        }
