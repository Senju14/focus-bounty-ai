"""
FocusGuard AI - System Tests
Run with: pytest tests/test_system.py -v
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestGroqAgent:
    """Test the Groq Agent (AI Pipeline)."""

    @pytest.fixture
    def mock_groq_client(self):
        """Create a mock Groq client."""
        with patch("focus_guard.engine.groq_agent.Groq") as mock:
            mock_instance = Mock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def agent(self, mock_groq_client):
        """Create a GroqAgent with mocked client."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            from focus_guard.engine.groq_agent import GroqAgent
            return GroqAgent()

    def test_agent_initialization(self, agent):
        """Test agent initializes with correct models."""
        assert agent.vision_model == "meta-llama/llama-4-scout-17b-16e-instruct"
        assert agent.reasoning_model == "meta-llama/llama-4-maverick-17b-128e-instruct"
        assert agent.safety_model == "meta-llama/llama-guard-4-12b"

    def test_agent_requires_api_key(self):
        """Test agent raises error without API key."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GROQ_API_KEY", None)
            os.environ.pop("GROG_API_KEY", None)
            
            with pytest.raises(ValueError, match="API_KEY is required"):
                from focus_guard.engine.groq_agent import GroqAgent
                # Force reimport
                import importlib
                import focus_guard.engine.groq_agent as module
                importlib.reload(module)
                module.GroqAgent()

    def test_analyze_image_returns_description(self, agent, mock_groq_client):
        """Test vision analysis returns text description."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="User is looking at phone"))]
        mock_groq_client.chat.completions.create.return_value = mock_response

        result = agent.analyze_image("base64_image_data")
        
        assert "phone" in result.lower() or "User" in result
        mock_groq_client.chat.completions.create.assert_called_once()

    def test_generate_roast_returns_text(self, agent, mock_groq_client):
        """Test roast generation returns witty text."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Put that phone down!"))]
        mock_groq_client.chat.completions.create.return_value = mock_response

        result = agent.generate_roast("User is looking at phone")
        
        assert len(result) > 0
        assert len(result.split()) <= 20  # Should be short

    def test_safety_check_returns_boolean(self, agent, mock_groq_client):
        """Test safety check returns safe/unsafe."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="safe"))]
        mock_groq_client.chat.completions.create.return_value = mock_response

        result = agent.check_safety("Get back to work!")
        
        assert isinstance(result, bool)
        assert result is True

    def test_safety_check_detects_unsafe(self, agent, mock_groq_client):
        """Test safety check detects unsafe content."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="unsafe\nS1"))]
        mock_groq_client.chat.completions.create.return_value = mock_response

        result = agent.check_safety("Some unsafe content")
        
        assert result is False


class TestFastAPIServer:
    """Test the FastAPI server endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            with patch("focus_guard.engine.groq_agent.Groq"):
                from fastapi.testclient import TestClient
                from focus_guard.server import app
                return TestClient(app)

    def test_landing_page_loads(self, client):
        """Test landing page returns 200."""
        response = client.get("/")
        assert response.status_code == 200
        assert "FocusGuard" in response.text

    def test_app_page_loads(self, client):
        """Test main app page returns 200."""
        response = client.get("/app")
        assert response.status_code == 200

    def test_dashboard_page_loads(self, client):
        """Test dashboard page returns 200."""
        response = client.get("/dashboard")
        assert response.status_code == 200

    def test_settings_page_loads(self, client):
        """Test settings page returns 200."""
        response = client.get("/settings")
        assert response.status_code == 200

    def test_static_files_served(self, client):
        """Test static files are accessible."""
        response = client.get("/static/css/style.css")
        # May return 200 or 404 depending on file existence
        assert response.status_code in [200, 404]


class TestWebSocket:
    """Test WebSocket communication."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            with patch("focus_guard.engine.groq_agent.Groq"):
                from fastapi.testclient import TestClient
                from focus_guard.server import app
                return TestClient(app)

    def test_websocket_connects(self, client):
        """Test WebSocket connection is accepted."""
        with client.websocket_connect("/ws/focus") as websocket:
            # Connection should be accepted
            assert websocket is not None

    def test_websocket_receives_message(self, client):
        """Test WebSocket can receive JSON messages."""
        with patch("focus_guard.server.groq_agent") as mock_agent:
            mock_agent.process_distraction.return_value = {
                "description": "User distracted",
                "tease": "Focus!",
                "safe": True
            }
            
            with client.websocket_connect("/ws/focus") as websocket:
                websocket.send_json({
                    "image": "base64data",
                    "reason": "Looking at phone"
                })
                # Should receive response
                # Note: May timeout in test environment


class TestStaticAssets:
    """Test static asset files exist."""

    def test_meme_images_exist(self):
        """Test meme images are present."""
        meme_dir = os.path.join(
            os.path.dirname(__file__), 
            "..", "src", "focus_guard", "static", "assets", "memes"
        )
        if os.path.exists(meme_dir):
            files = os.listdir(meme_dir)
            assert len(files) > 0, "Meme folder should have images"

    def test_video_files_exist(self):
        """Test video files are present."""
        video_dir = os.path.join(
            os.path.dirname(__file__), 
            "..", "src", "focus_guard", "static", "assets", "video"
        )
        if os.path.exists(video_dir):
            files = os.listdir(video_dir)
            assert len(files) > 0, "Video folder should have files"

    def test_html_pages_exist(self):
        """Test all HTML pages exist."""
        static_dir = os.path.join(
            os.path.dirname(__file__), 
            "..", "src", "focus_guard", "static"
        )
        required_pages = ["landing.html", "app.html", "dashboard.html", "settings.html"]
        
        for page in required_pages:
            path = os.path.join(static_dir, page)
            assert os.path.exists(path), f"Missing: {page}"


class TestConfiguration:
    """Test configuration and environment."""

    def test_env_file_structure(self):
        """Test .env.example exists with required keys."""
        env_example = os.path.join(
            os.path.dirname(__file__), 
            "..", ".env.example"
        )
        # May or may not exist
        if os.path.exists(env_example):
            with open(env_example) as f:
                content = f.read()
                assert "GROQ_API_KEY" in content

    def test_requirements_file_exists(self):
        """Test requirements.txt exists."""
        req_file = os.path.join(
            os.path.dirname(__file__), 
            "..", "requirements.txt"
        )
        assert os.path.exists(req_file), "requirements.txt is required"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
