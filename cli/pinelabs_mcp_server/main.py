"""
Pine Labs MCP Server — CLI entry point.

Usage:
    python -m cli.pinelabs_mcp_server.main stdio \\
        --client-id <ID> --client-secret <SECRET> \\
        [--env uat|prod] [--log-file /path/to/log] \\
        [--read-only] [--toolsets payment_links,orders]

    python -m cli.pinelabs_mcp_server.main http \\
        --client-id <ID> --client-secret <SECRET> \\
        [--host 0.0.0.0] [--port 8000] \\
        [--env uat|prod] [--read-only] [--toolsets payment_links,orders]
"""

import argparse
import logging
import os
import sys

from pkg.log.log import LogConfig, setup_logging
from pkg.pinelabs.config import Settings


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add arguments shared by both stdio and http subcommands."""
    parser.add_argument(
        "--client-id",
        default=os.environ.get("PINELABS_CLIENT_ID", ""),
        help="Pine Labs client ID (env: PINELABS_CLIENT_ID)",
    )
    parser.add_argument(
        "--client-secret",
        default=os.environ.get("PINELABS_CLIENT_SECRET", ""),
        help="Pine Labs client secret (env: PINELABS_CLIENT_SECRET)",
    )
    parser.add_argument(
        "--env",
        default=os.environ.get("PINELABS_ENV", "uat"),
        choices=["uat", "prod"],
        help="Environment (default: uat)",
    )
    parser.add_argument(
        "--log-file",
        default=os.environ.get("LOG_FILE", ""),
        help="Log file path (default: stderr)",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        default=False,
        help="Only register read-only tools",
    )
    parser.add_argument(
        "--toolsets",
        default="",
        help="Comma-separated list of toolsets to enable (default: all)",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pinelabs-mcp-server",
        description="Pine Labs MCP Server",
    )

    sub = parser.add_subparsers(dest="command")

    stdio = sub.add_parser(
        "stdio",
        help="Run the MCP server with stdio transport",
    )
    _add_common_args(stdio)

    http = sub.add_parser(
        "http",
        help="Run the MCP server with HTTP transport",
    )
    _add_common_args(http)
    http.add_argument(
        "--host",
        default=os.environ.get("HOST", "0.0.0.0"),  # noqa: S104 - server is intended to listen on all interfaces; override via --host or HOST env
        help="Host to bind to (default: 0.0.0.0)",
    )
    http.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000")),
        help="Port to listen on (default: 8000)",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command not in ("stdio", "http"):
        parser.print_help()
        sys.exit(1)

    # Setup logging
    log_config = LogConfig(
        log_level=getattr(logging, args.log_level, logging.INFO),
        log_path=args.log_file or "",
    )
    setup_logging(log_config)

    logger = logging.getLogger("pinelabs-mcp-server")
    logger.info(
        "Starting Pine Labs MCP Server (%s)", args.command
    )

    # Build settings
    settings = Settings(
        client_id=args.client_id,
        client_secret=args.client_secret,
        environment=args.env,
    )

    if args.log_file:
        settings.log_file = args.log_file
    settings.log_level = args.log_level

    # Parse toolsets
    enabled_toolsets = None
    if args.toolsets:
        enabled_toolsets = [
            t.strip() for t in args.toolsets.split(",")
            if t.strip()
        ]

    if args.command == "stdio":
        from cli.pinelabs_mcp_server.stdio import (
            run_stdio_server,
        )
        run_stdio_server(
            settings,
            read_only=args.read_only,
            enabled_toolsets=enabled_toolsets,
        )
    elif args.command == "http":
        from cli.pinelabs_mcp_server.http import (
            run_http_server,
        )
        run_http_server(
            settings,
            host=args.host,
            port=args.port,
            read_only=args.read_only,
            enabled_toolsets=enabled_toolsets,
        )


if __name__ == "__main__":
    main()
