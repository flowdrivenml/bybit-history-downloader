from __future__ import annotations

import argparse

from marketforge.acquisition.client import MarketForgeClient
from marketforge.cli.ui.instruments import print_instruments
from marketforge.models import DataType, Exchange, InstrumentType, MarketCategory


def run(
    args: argparse.Namespace,
) -> int:
    """Discover instruments available from an exchange."""

    exchange = Exchange(args.exchange)

    instrument_type = InstrumentType(args.instrument_type)

    market_category = MarketCategory(args.category)

    data_type = DataType(args.data_type)

    with MarketForgeClient() as client:
        instruments = client.instruments(
            exchange=exchange,
            instrument_type=instrument_type,
            market_category=market_category,
            data_type=data_type,
        )

    if args.search:
        needle = args.search.casefold()

        instruments = [
            instrument
            for instrument in instruments
            if (
                needle in instrument.symbol.casefold()
                or (
                    instrument.family is not None
                    and needle in instrument.family.casefold()
                )
            )
        ]

    instruments = sorted(
        instruments,
        key=lambda instrument: (instrument.symbol),
    )

    print_instruments(
        instruments,
        exchange=exchange,
        instrument_type=instrument_type,
        market_category=market_category,
        data_type=data_type,
        search=args.search,
    )

    return 0
