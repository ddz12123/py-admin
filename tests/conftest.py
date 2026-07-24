import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

os.environ["PY_ADMIN_DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["PY_ADMIN_DEBUG"] = "false"
