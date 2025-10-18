"""Application logging configuration utilities."""

from __future__ import annotations

import logging
import sys
from typing import Optional


DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(level: int = logging.INFO, format: Optional[str] = None) -> None:
    """Configure application wide logging.

    The backend relies on :func:`logging.info` calls (for example in the Gemini
    realtime service) to stream transcription chunks to the terminal. When the
    backend starts via Uvicorn, Python's root logger keeps the default WARNING
    level which prevents these INFO messages from being displayed. This helper
    enforces an INFO log level with a simple formatter so that the transcription
    messages appear in the terminal output.

    Args:
        level: Desired logging level. Defaults to :data:`logging.INFO`.
        format: Optional log message format string.
    """

    logging.basicConfig(
        level=level,
        format=format or DEFAULT_LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

