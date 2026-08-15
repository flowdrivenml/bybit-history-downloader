from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Literal

from .client import BybitHistoryClient


Margin = Literal["Spot", "Contract"]
DataType = Literal["Trades", "L2Book"]


def _norm_margin(s: str) -> Margin:
    s = s.strip().lower()

    if s == "spot":
        return "Spot"

    if s in ("contract", "derivatives", "perp", "futures"):
        return "Contract"

    raise argparse.ArgumentTypeError("margin must be 'spot' or 'contract'")


def _norm_dtype(s: str) -> DataType:
    s = s.strip().lower()

    if s in ("trades", "trade"):
        return "Trades"

    if s in ("l2book", "l2", "orderbook", "order_book"):
        return "L2Book"

    raise argparse.ArgumentTypeError("data_type must be 'trades' or 'l2book'")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bybit-history",
        description="Download historical Bybit market data using Playwright.",
    )

    parser.add_argument(
        "--browser",
        default="firefox",
        choices=["firefox", "chromium", "webkit"],
        help="Browser to use (default: firefox)",
    )

    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run browser headless. Use --no-headless to see the browser.",
    )

    subparsers = parser.add_subparsers(
        dest="cmd",
        required=True,
    )

    # List symbols
    symbols_parser = subparsers.add_parser(
        "symbols",
        help="List available symbols.",
    )

    symbols_parser.add_argument(
        "margin",
        type=_norm_margin,
        help="spot|contract",
    )

    # Download data
    download_parser = subparsers.add_parser(
        "download",
        help="Download historical data.",
    )

    download_parser.add_argument(
        "margin",
        type=_norm_margin,
        help="spot|contract",
    )

    download_parser.add_argument(
        "data_type",
        type=_norm_dtype,
        help="trades|l2book",
    )

    download_parser.add_argument(
        "--symbol",
        required=True,
        help="Symbol, e.g. BTCUSDT",
    )

    download_parser.add_argument(
        "--start",
        required=True,
        help="Start date in YYYY-MM-DD format",
    )

    download_parser.add_argument(
        "--end",
        required=True,
        help="End date in YYYY-MM-DD format",
    )

    download_parser.add_argument(
        "--out",
        required=True,
        help="Output directory",
    )

    download_parser.add_argument(
        "--chunk-days",
        type=int,
        default=5,
        help="Chunk size in days (must be < 6)",
    )

    return parser


async def _run_symbols(args) -> int:
    async with BybitHistoryClient(
        headless=args.headless,
        browser_name=args.browser,
    ) as client:
        if args.margin == "Spot":
            await client.show_spot_symbols()
        else:
            await client.show_contract_symbols()

    return 0


async def _run_download(
    args,
    parser: argparse.ArgumentParser,
) -> int:

    if args.chunk_days <= 0:
        parser.error("chunk-days must be greater than 0")

    if args.chunk_days >= 6:
        parser.error("chunk-days must be < 6")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    async with BybitHistoryClient(
        headless=args.headless,
        browser_name=args.browser,
    ) as client:
        await client.download_data(
            margin=args.margin,
            data_type=args.data_type,
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
            final_path=str(out_dir),
            chunk_days=args.chunk_days,
        )

    return 0


async def amain(
    argv: list[str] | None = None,
) -> int:

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "symbols":
        return await _run_symbols(args)

    if args.cmd == "download":
        return await _run_download(args, parser)

    parser.error("unknown command")
    return 2


def main(
    argv: list[str] | None = None,
) -> None:

    raise SystemExit(asyncio.run(amain(argv)))


if __name__ == "__main__":
    main()

