"""
ah_logging.py — ArchonHub structured logging
Logs to .agents/data/logs/<module>.log with rotation
"""
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

HERE = Path(__file__).parent
AGENTS_DIR = HERE.parent.parent.parent  # .agents/
LOG_DIR = AGENTS_DIR / "data" / "logs"

def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module name. Creates log file at LOG_DIR/<name>.log"""
    # Ensure log dir exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(f"archonhub.{name}")
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler (5MB rotation, keep 3 files)
    fh = RotatingFileHandler(LOG_DIR / f"{name}.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    
    return logger
