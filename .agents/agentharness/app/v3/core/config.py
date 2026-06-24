from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent.parent
HARNESS = HERE.parent.parent
AGENTS_DIR = HARNESS.parent
APP_ROOT = AGENTS_DIR.parent
WEB_DIR = HERE / "web"
PID_FILE = AGENTS_DIR / "data" / "hub.pid"
DB_PATH = HARNESS / "memory" / "runs_v3.db"
SKILLS_ROOT = AGENTS_DIR / "agents" / "projects"

for _path in (HERE, HARNESS, AGENTS_DIR, APP_ROOT):
    if str(_path) not in sys.path:
        sys.path.append(str(_path))

load_dotenv(AGENTS_DIR / '.env')

_JWT_SECRET_DEFAULT = 'archonhub-jwt-secret-change-in-production-2024'
SECRET_KEY = os.environ.get('JWT_SECRET', _JWT_SECRET_DEFAULT)
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_HOURS = 24
APP_VERSION = '1.0.0'
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'ArchonHub2024!')

_cors_origins_env = os.environ.get('CORS_ORIGINS', '')
_cors_origins = [o.strip() for o in _cors_origins_env.split(',') if o.strip()] if _cors_origins_env else ['*']
CORS_ORIGINS = _cors_origins
