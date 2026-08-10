"""
Structured Logger Utility (Serverless-Resilient)
"""
import os
import sys
import logging
import tempfile
from pathlib import Path

def setup_logger(name: str = "Excelo") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console Handler (Standard for Vercel / Cloud Serverless stdout logs)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # Optional File Handler (Best-effort attempt for local dev or temp storage)
        try:
            if os.environ.get("VERCEL"):
                log_dir = Path(tempfile.gettempdir()) / "logs"
            else:
                _PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
                log_dir = _PROJECT_ROOT / "logs"

            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / "excelo.log"

            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except (OSError, PermissionError):
            pass

    return logger

logger = setup_logger()
