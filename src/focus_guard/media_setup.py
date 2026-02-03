import os
import requests
from pathlib import Path

# Config
BASE_DIR = Path(__file__).parent / "static" / "assets"
MEME_POS_DIR = BASE_DIR / "memes" / "positive"
MEME_NEG_DIR = BASE_DIR / "memes" / "negative"
VIDEO_DIR = BASE_DIR / "video"

# URLs (Placeholders that are reliable/safe)
# In a real app, you'd host these yourself. Using placehold.co for safety/reliability in demo.
ASSETS = {
    "positive": [
        ("good_job_1.png", "https://placehold.co/600x400/00CC00/FFFFFF/png?text=Great+Focus!+Keep+it+up!"),
        ("good_job_2.png", "https://placehold.co/600x400/00CC00/FFFFFF/png?text=You+are+a+Machine!"),
        ("good_job_3.png", "https://placehold.co/600x400/00CC00/FFFFFF/png?text=Focus+Level:+9000")
    ],
    "negative": [
        ("roast_1.png", "https://placehold.co/600x400/CC0000/FFFFFF/png?text=Get+Back+To+Work!"),
        ("roast_2.png", "https://placehold.co/600x400/CC0000/FFFFFF/png?text=TikTok+Wont+Pay+Rent"),
        ("roast_3.png", "https://placehold.co/600x400/CC0000/FFFFFF/png?text=Why+Are+You+Like+This?")
    ],
    "video": [
        # Using a small standard sample video for tests if needed, or stick to generated
        # For the "Warning Video", let's use a placeholder unless user provides one.
        # Actually, let's download a small "Emergency" style gif/video if possible, 
        # or just a scary red static image sequences.
        # For reliability, I'll generate a "WARNING" placeholder video/gif.
        ("warning.mp4", "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDdtY2J6eXF6YjJ6YjJ6YjJ6YjJ6YjJ6YjJ6YjJ6YjJ6/13d2jHlSlxcl0I/giphy.mp4") # Glitch effect or similar
    ]
}

def download_file(url, path):
    print(f"Downloading {path.name}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Done.")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def main():
    print("📦 Setting up Media Assets...")
    
    # Ensure dirs exist
    for d in [MEME_POS_DIR, MEME_NEG_DIR, VIDEO_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Download Positive
    for name, url in ASSETS["positive"]:
        download_file(url, MEME_POS_DIR / name)

    # Download Negative
    for name, url in ASSETS["negative"]:
        download_file(url, MEME_NEG_DIR / name)

    # Download Video
    for name, url in ASSETS["video"]:
        # Disclaimer: GIF as MP4 for demo
        download_file("https://media.giphy.com/media/26tP7axeTIW9V05UY/giphy.mp4", VIDEO_DIR / "warning.mp4")
        
    print("✅ All assets ready.")

if __name__ == "__main__":
    main()
