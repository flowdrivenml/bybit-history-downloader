from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from marketforge.models import (
    AcquisitionRequest,
    DataType,
    Exchange,
    Instrument,
    InstrumentType,
    MarketCategory,
)


def add_request_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    """Add arguments shared by acquisition commands."""

    parser.add_argument(
        "--exchange",
        required=True,
        choices=[exchange.value for exchange in Exchange],
    )

    parser.add_argument(
        "--type",
        dest="instrument_type",
        required=True,
        choices=[instrument_type.value for instrument_type in InstrumentType],
    )

    parser.add_argument(
        "--category",
        required=True,
        choices=[category.value for category in MarketCategory],
    )

    parser.add_argument(
        "--symbol",
        required=True,
    )

    parser.add_argument(
        "--family",
        default=None,
        help=("Optional exchange instrument family, " "for example BTC-USDT on OKX."),
    )

    parser.add_argument(
        "--data",
        dest="data_type",
        required=True,
        choices=[data_type.value for data_type in DataType],
    )

    parser.add_argument(
        "--start",
        required=True,
        help="Inclusive UTC start date/time.",
    )

    parser.add_argument(
        "--end",
        required=True,
        help="Exclusive UTC end date/time.",
    )

    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data"),
        help="MarketForge data root.",
    )


def request_from_args(
    args: argparse.Namespace,
) -> AcquisitionRequest:
    """Build an AcquisitionRequest from parsed CLI arguments."""

    instrument = Instrument(
        exchange=Exchange(args.exchange),
        instrument_type=InstrumentType(args.instrument_type),
        market_category=MarketCategory(args.category),
        symbol=args.symbol,
        family=args.family,
    )

    return AcquisitionRequest(
        target=instrument,
        data_type=DataType(args.data_type),
        start=parse_datetime(args.start),
        end=parse_datetime(args.end),
    )


def parse_datetime(
    value: str,
) -> datetime:
    """Parse a CLI date/time and normalize it to UTC."""

    try:
        parsed = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid date/time: {value}") from exc

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def add_instrument_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    """Add arguments used for instrument discovery."""

    parser.add_argument(
        "--exchange",
        required=True,
        choices=[exchange.value for exchange in Exchange],
    )

    parser.add_argument(
        "--type",
        dest="instrument_type",
        required=True,
        choices=[instrument_type.value for instrument_type in InstrumentType],
    )

    parser.add_argument(
        "--category",
        required=True,
        choices=[category.value for category in MarketCategory],
    )

    parser.add_argument(
        "--data",
        dest="data_type",
        required=True,
        choices=[data_type.value for data_type in DataType],
    )

    parser.add_argument(
        "--search",
        default=None,
        help="Filter returned symbols.",
    )
