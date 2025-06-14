"""Configuration management module"""
import os
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum

class LLMProvider(Enum):
    """Available LLM providers"""
    GEMINI = "gemini"
    LOCAL = "local"
    NONE = "none"  # Fallback to templates

# Get the root directory of the project
ROOT_DIR = Path(__file__).parent.parent
ENV_FILE = ROOT_DIR / '.env'

# Load environment variables from .env file
if ENV_FILE.exists():
    print(f"Loading environment variables from {ENV_FILE}")
    load_dotenv(ENV_FILE)
else:
    print(f"Warning: .env file not found at {ENV_FILE}")

# LLM Configuration
ACTIVE_LLM = os.getenv('ACTIVE_LLM', 'none').lower()
if ACTIVE_LLM not in [e.value for e in LLMProvider]:
    print(f"Warning: Invalid LLM provider '{ACTIVE_LLM}'. Using fallback templates.")
    ACTIVE_LLM = LLMProvider.NONE.value
else:
    print(f"Using LLM provider: {ACTIVE_LLM}")

# Gemini configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if ACTIVE_LLM == LLMProvider.GEMINI.value and not GEMINI_API_KEY:
    print("Warning: No Gemini API key found. Will use fallback templates.")
    ACTIVE_LLM = LLMProvider.NONE.value

# Ollama configuration
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')
if ACTIVE_LLM == LLMProvider.LOCAL.value:
    print(f"Using Ollama with model {OLLAMA_MODEL} at {OLLAMA_HOST}")

# Add other configuration variables here
