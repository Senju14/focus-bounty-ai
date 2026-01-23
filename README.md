# FocusBounty - AI Focus Coach

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/focus-bounty-ai)

AI-powered focus enforcement with face detection for the **Comet Resolution V2 Hackathon**.

## Features

- 🎯 **Face Detection** - Monitors if you're at your desk
- 🤖 **AI Coach** - Cute anime-style encouragement & warnings
- 🔊 **TTS Voice** - Anime girl voice feedback
- 📊 **Opik Integration** - Full observability & tracing

## Tech Stack

- **Backend**: FastAPI + Python
- **AI**: Gemini 2.0 Flash-Lite (with fallback logic)
- **Detection**: OpenCV Haar Cascade + YOLOv8
- **Observability**: Opik (Comet)
- **Frontend**: HTML + TailwindCSS + Vanilla JS

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/focus-bounty-ai
cd focus-bounty-ai

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your GEMINI_API_KEY and OPIK_API_KEY

# Run
python main.py

# Open http://localhost:8000
```

## Deployment

### Local Network
Server binds to `0.0.0.0:8000` - accessible from any device on your network.

### Vercel (Limited)
```bash
vercel deploy
```
> Note: WebSocket not fully supported on Vercel serverless. 
> For full functionality, use Railway or Render.

### Railway (Recommended)
```bash
railway init
railway up
```

## Project Structure

```
focus-bounty-ai/
├── main.py              # Entry point (0.0.0.0:8000)
├── vercel.json          # Vercel config
├── api/index.py         # Serverless entry
├── src/
│   ├── backend/
│   │   ├── app.py       # FastAPI server
│   │   ├── agent.py     # AI logic + Opik
│   │   ├── perception.py # Face detection
│   │   ├── actions.py   # Interventions
│   │   └── evaluation.py # Benchmarks
│   └── frontend/
│       ├── index.html
│       ├── css/style.css
│       └── js/script.js
```

## Opik Integration

All decisions traced to `FocusBounty-Hackathon` project:
- Face detection events
- Intervention decisions
- Session statistics

## License

MIT

---

Built for [Comet Resolution V2 Hackathon](https://www.encodeclub.com/my-programmes/comet-resolution-v2-hackathon) 🚀
