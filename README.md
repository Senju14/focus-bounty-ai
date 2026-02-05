# FocusGuard AI 🎯

> **Your brutally honest AI productivity coach that roasts you back to focus.**

https://focus-bounty-ai--522h0134.replit.app/app

Built for the **Comet Opik + Groq Hackathon** - A real-time focus monitoring system that uses computer vision and generative AI to keep you on track with a "tough love" approach.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Groq](https://img.shields.io/badge/Groq-Llama%204-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- **👁️ Real-time Face Tracking** - MediaPipe FaceMesh tracks your eyes, head pose, and iris position
- **🤖 3-Stage AI Pipeline** - Vision → Reasoning → Safety using Groq's ultra-fast Llama 4 models
- **🎤 Meme Voice Presets** - Paimon, Mickey Mouse, Morgan Freeman, Darth Vader, and more!
- **📊 Session Dashboard** - Track your focus history with grades from F to A+
- **🔔 Smart Alerts** - Browser notifications when you switch tabs
- **🎨 Custom Memes** - Add your own meme images for personalized roasts
- **📈 Opik Observability** - Full AI decision tracing and debugging

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      BROWSER (Client)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  MediaPipe  │  │   Web UI    │  │  Text-to-Speech     │  │
│  │  FaceMesh   │  │  (Vanilla)  │  │  (Meme Voices)      │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┼─────────────────────┘             │
│                          │ WebSocket                         │
└──────────────────────────┼───────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────┐
│                      SERVER (Python)                         │
│                          │                                   │
│  ┌───────────────────────▼────────────────────────────────┐  │
│  │                 FastAPI + Uvicorn                      │  │
│  └───────────────────────┬────────────────────────────────┘  │
│                          │                                   │
│  ┌───────────────────────▼────────────────────────────────┐  │
│  │               3-Stage Agentic Pipeline                 │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │  │
│  │  │   VISION    │ │  REASONING  │ │     SAFETY      │   │  │
│  │  │ Llama Scout │→│Llama Maverick│→│  Llama Guard   │   │  │
│  │  │ (Analyze)   │ │  (Roast)    │ │   (Filter)      │   │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │  │
│  └────────────────────────────────────────────────────────┘  │
│                          │                                   │
│  ┌───────────────────────▼────────────────────────────────┐  │
│  │                    Comet Opik                          │  │
│  │              (Observability & Tracing)                 │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Webcam
- [Groq API Key](https://console.groq.com)
- [Opik API Key](https://www.comet.com/opik) (optional, for tracing)

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/focus-bounty-ai.git
cd focus-bounty-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Run

```bash
python run_local.py
```

Open http://localhost:5000 in your browser!

### Deploy on Replit

1. Import this repo on [Replit](https://replit.com)
2. Add `GROQ_API_KEY` in Secrets
3. Click **Run** - that's it!

## 📁 Project Structure

```
focus-bounty-ai/
├── run_local.py           # Entry point
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── .replit               # Replit config
├── replit.nix            # Replit dependencies
├── src/
│   └── focus_guard/
│       ├── server.py     # FastAPI server
│       ├── engine/
│       │   └── groq_agent.py  # AI pipeline
│       └── static/
│           ├── app.html      # Main app
│           ├── landing.html  # Landing page
│           ├── dashboard.html # History
│           ├── settings.html # Config
│           ├── css/          # Styles
│           ├── js/           # Scripts
│           └── assets/
│               └── memes/
│                   └── uploads/  # Your custom memes!
└── tests/
    └── test_system.py    # Pytest tests
```

## 🎤 Voice Presets

| Voice | Description |
|-------|-------------|
| 🎲 Random | Auto-cycles through all voices |
| ✨ Paimon | High-pitched, fast (Genshin Impact) |
| 🐭 Mickey Mouse | Squeaky, cheerful |
| 🎬 Morgan Freeman | Deep, slow, dramatic |
| 🐿️ Chipmunk | Super high-pitched |
| ⚫ Darth Vader | Deep, ominous |
| 🌸 Anime Girl | Kawaii style |
| 🤖 Robot | Monotone, mechanical |
| 👻 Ghostface | Creepy whisper |

## 🧪 Testing

```bash
pytest tests/test_system.py -v
```

## 🔧 Configuration

Edit settings in the app or modify `src/focus_guard/static/js/app.js`:

- **Focus Buffer Size** - Frames to average (prevents flickering)
- **Roast Cooldown** - Seconds between roasts
- **Detection Thresholds** - EAR and yaw sensitivity

## 📜 License

MIT License - See [LICENSE](LICENSE)

## 🙏 Acknowledgments

- [Groq](https://groq.com) - Ultra-fast LLM inference
- [Comet Opik](https://www.comet.com/opik) - LLM observability
- [MediaPipe](https://mediapipe.dev) - Face tracking

---

**Made with 💀 tough love for the Comet Resolution V2 Hackathon**
