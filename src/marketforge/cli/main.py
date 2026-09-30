from __future__ import annotations

import argparse
from typing import Sequence

from marketforge.cli.arguments import add_instrument_arguments, add_request_arguments
from marketforge.cli.commands import availability, download, instruments, plan


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """Run the MarketForge command-line interface."""

    parser = build_parser()

    args = parser.parse_args(argv)

    if args.command == "plan":
        return plan.run(args)

    if args.command == "download":
        return download.run(args)

    if args.command == "instruments":
        return instruments.run(args)

    if args.command == "availability":
        return availability.run(args)

    parser.error(f"Unknown command: {args.command}")

    return 2


def build_parser() -> argparse.ArgumentParser:
    """Build the MarketForge CLI parser."""

    parser = argparse.ArgumentParser(
        prog="marketforge",
        description=("Historical market-microstructure " "data acquisition."),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    plan_parser = subparsers.add_parser(
        "plan",
        help="Plan a historical-data acquisition.",
    )

    add_request_arguments(plan_parser)

    download_parser = subparsers.add_parser(
        "download",
        help="Download historical-data archives.",
    )

    add_request_arguments(download_parser)

    instruments_parser = subparsers.add_parser(
        "instruments",
        help="Discover exchange instruments.",
    )

    add_instrument_arguments(instruments_parser)

    availability_parser = subparsers.add_parser(
        "availability",
        help="Check historical data availability.",
    )

    add_request_arguments(availability_parser)

    return parser
