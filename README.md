# FocusGuard AI

FocusGuard AI is a productivity tool built for the Comet Resolution V2 Hackathon. It uses computer vision to track your focus and generative AI to provide feedback if you get distracted.

## How It Works

The system uses a 3-step pipeline to ensure accuracy and safety:

1.  **Vision (The Scout)**: A computer vision model analyzes your webcam feed to detect what you are doing—whether you are working, looking at your phone, or absent.
2.  **Reasoning (The Coach)**: If you are distracted, a reasoning model generates a sarcastic or "tough love" comment based on your specific distraction.
3.  **Safety (The Guard)**: A safety filter checks the comment to ensure it is appropriate before it is spoken aloud.

## Key Features

*   **Iris Tracking**: Detects if your eyes are looking away from the screen, even if your head is facing forward.
*   **Dynamic Voice**: Uses different voices for variety.
*   **Report Card**: Grades your focus session from F to A+ when you finish.
*   **Tab Awareness**: Sends a browser notification if you switch tabs to procrastinate.
*   **Observability**: All AI decisions are logged to Opik for debugging.

## Getting Started

### Prerequisites

*   Python 3.10 or higher
*   A Webcam
*   Groq API Key (for the AI models)

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/focus-guard.git
    cd focus-guard
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure Environment:
    Create a file named `.env` and add your keys:
    ```env
    GROQ_API_KEY=gsk_your_key_here
    OPIK_API_KEY=your_opik_key_here
    ```

4.  Run the application:
    ```bash
    python main.py
    ```

5.  Open your browser:
    *   **Landing Page**: http://localhost:8000
    *   **Application**: http://localhost:8000/app

## Technology Stack

*   **Frontend**: HTML, JavaScript, CSS
*   **Vision**: Google MediaPipe (Face Mesh & Iris)
*   **Backend**: Python (FastAPI)
*   **AI Models**: Groq (Llama 4)
*   **Tracking**: Comet Opik

## License

MIT License
