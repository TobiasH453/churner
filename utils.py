import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_env(key: str, default: str = None) -> str:
    """Get environment variable with fallback"""
    value = os.getenv(key, default)
    if isinstance(value, str):
        value = value.strip()
        # Handle accidental quoted values in .env
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1].strip()

    if value is None:
        raise ValueError(f"Missing required environment variable: {key}")

    if key == "ANTHROPIC_API_KEY" and value:
        # Anthropic API keys are typically much longer than 20 chars.
        if len(value) < 40 or not value.startswith("sk-ant-"):
            raise ValueError(
                "ANTHROPIC_API_KEY looks invalid. Use a real Anthropic API key "
                "from the Anthropic Console (expected format starts with 'sk-ant-')."
            )
    return value

def save_cookies(cookies: list, filepath: str = "data/cookies.json"):
    """Save browser cookies for session persistence"""
    Path("data").mkdir(exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(cookies, f)
    logger.info(f"Cookies saved to {filepath}")

def load_cookies(filepath: str = "data/cookies.json") -> list:
    """Load browser cookies"""
    if not Path(filepath).exists():
        logger.warning(f"No cookies found at {filepath}")
        return []
    with open(filepath, 'r') as f:
        cookies = json.load(f)
    logger.info(f"Loaded {len(cookies)} cookies")
    return cookies

def save_state(key: str, value: any):
    """Save state to local file (simple key-value store)"""
    Path("data").mkdir(exist_ok=True)
    state_file = Path("data/state.json")

    # Load existing state
    state = {}
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)

    # Update state
    state[key] = value

    # Save state
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def get_state(key: str, default: any = None) -> any:
    """Get state value"""
    state_file = Path("data/state.json")
    if not state_file.exists():
        return default

    with open(state_file, 'r') as f:
        state = json.load(f)

    return state.get(key, default)
