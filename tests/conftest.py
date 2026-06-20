import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


# 测试环境强制使用 SQLite，避免机器环境变量把测试带到真实数据库
os.environ["PY_ADMIN_DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["PY_ADMIN_SECRET_KEY"] = "test-secret-key"
os.environ["PY_ADMIN_DEBUG"] = "false"
