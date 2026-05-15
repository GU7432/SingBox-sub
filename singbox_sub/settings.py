from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TOKENS_PATH = DATA_DIR / "tokens.yaml"
CONFIG_DIR = DATA_DIR / "configs"
