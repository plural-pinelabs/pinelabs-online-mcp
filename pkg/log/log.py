"""
Logging configuration for Pine Labs MCP Server.

Provides a simple structured logging setup with file and stderr modes.
"""

import logging
import os
import sys


# Logger modes
MODE_STDIO = "stdio"


class LogConfig:
    """Logger configuration with options pattern."""

    def __init__(
        self,
        mode: str = MODE_STDIO,
        log_level: int = logging.INFO,
        log_path: str = "",
    ) -> None:
        self.mode = mode
        self.log_level = log_level
        self.log_path = log_path


def setup_logging(config: LogConfig) -> logging.Logger:
    """Create and configure a logger based on the provided configuration.

    For stdio mode, logs go to a file (if log_path set) or stderr.
    """
    logger = logging.getLogger("pinelabs-mcp-server")
    logger.setLevel(config.log_level)

    # Clear existing handlers
    logger.handlers.clear()

    if config.mode == MODE_STDIO and config.log_path:
        # File-based logging for stdio mode
        log_dir = os.path.dirname(config.log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(config.log_path)
    else:
        # Stderr logging
        handler = logging.StreamHandler(sys.stderr)

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
