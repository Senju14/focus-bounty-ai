import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from opik import Opik, track
from opik.evaluation import evaluate
from focus_guard.engine.groq_agent import GroqAgent
from dotenv import load_dotenv

load_dotenv()

# Configure Opik for Hackathon
os.environ["OPIK_PROJECT_NAME"] = "Commit Hackathon"

def evaluate_toxic_coach():
    """Runs an Opik evaluation on the Toxic Coach persona."""
    agent = GroqAgent()
    
    # Mock dataset of distractions
    # Comprehensive dataset for system testing
    dataset = [
        {"reason": "User is sleeping on the keyboard"},
        {"reason": "User is looking at phone scrolling TikTok"},
        {"reason": "User left the desk empty"},
        {"reason": "User is eating a sandwich"},
        {"reason": "User is staring at a second monitor coding"},
        {"reason": "User is chatting with a colleague"},
        {"reason": "User is playing video games"}
    ]

    # Mock base64 image (10x10 red square) - Groq requires >1x1 pixel
    mock_image = "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8z8BQz0AEYBxVCNqXBAArEQIg/1R8XAAAAABJRU5ErkJggg=="

    @track(name="evaluation_task")
    def evaluation_task(item):
        if item.get("image"):
             return agent.process_distraction(item['image'])
        return agent.generate_roast(item['reason'])

    print("Running Opik Evaluation for Toxic Coach (Multi-Model)...")
    
    # Test text pipeline
    for item in dataset:
        result = evaluation_task(item)
        roast_text = result['tease'] if isinstance(result, dict) else result
        print(f"Distraction: {item['reason']} | Roast: {roast_text}")
    
    # Test full pipeline (Vision -> Text -> Safety)
    print("\nTesting Vision Pipeline...")
    vision_result = evaluation_task({"image": mock_image})
    print(f"Vision Output: {vision_result.get('activity')} | Roast: {vision_result.get('tease')}")

    print("\nEvaluation complete. Check your Opik/Comet dashboard for full traces.")

if __name__ == "__main__":
    evaluate_toxic_coach()
