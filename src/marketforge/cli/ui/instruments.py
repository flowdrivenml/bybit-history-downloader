from __future__ import annotations

from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text

from marketforge.cli.ui.console import console
from marketforge.models import (
    DataType,
    Exchange,
    Instrument,
    InstrumentType,
    MarketCategory,
)


def print_instruments(
    instruments: list[Instrument],
    *,
    exchange: Exchange,
    instrument_type: InstrumentType,
    market_category: MarketCategory,
    data_type: DataType,
    search: str | None = None,
) -> None:
    """Render the complete discovered instrument universe."""

    _print_header(
        exchange=exchange,
        instrument_type=instrument_type,
        market_category=market_category,
        data_type=data_type,
        search=search,
        total=len(instruments),
    )

    console.print()

    if not instruments:
        console.print(
            Panel(
                "No instruments found.",
                border_style="yellow",
            )
        )
        return

    items = [_instrument_text(instrument) for instrument in instruments]

    console.print(
        Columns(
            items,
            padding=(0, 3),
            equal=True,
            expand=True,
        )
    )

    console.print()

    _print_footer(
        exchange=exchange,
        instrument_type=instrument_type,
        data_type=data_type,
        total=len(instruments),
    )


def _instrument_text(
    instrument: Instrument,
) -> Text:
    """Render one instrument for the symbol grid."""

    text = Text()

    text.append(
        instrument.symbol,
        style="bold white",
    )

    if instrument.family:
        text.append(
            f"  {instrument.family}",
            style="dim cyan",
        )

    return text


def _print_header(
    *,
    exchange: Exchange,
    instrument_type: InstrumentType,
    market_category: MarketCategory,
    data_type: DataType,
    search: str | None,
    total: int,
) -> None:
    title = Text()

    title.append(
        " MARKETFORGE ",
        style="bold black on cyan",
    )

    title.append(
        "  INSTRUMENTS",
        style="bold",
    )

    body = Text()

    body.append(
        exchange.value.upper(),
        style="bold cyan",
    )

    body.append(
        "  ·  ",
        style="dim",
    )

    body.append(
        instrument_type.value.upper(),
        style="bold white",
    )

    body.append(
        "  ·  ",
        style="dim",
    )

    body.append(
        market_category.value.upper(),
        style="bold white",
    )

    body.append(
        "  ·  ",
        style="dim",
    )

    body.append(
        data_type.value.upper(),
        style="bold magenta",
    )

    body.append("\n\n")

    body.append(
        f"{total:,}",
        style="bold green",
    )

    body.append(
        " instruments",
        style="dim",
    )

    if search:
        body.append("    ")

        body.append(
            "FILTER  ",
            style="dim",
        )

        body.append(
            search,
            style="bold yellow",
        )

    console.print()

    console.print(
        Panel(
            body,
            title=title,
            title_align="left",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def _print_footer(
    *,
    exchange: Exchange,
    instrument_type: InstrumentType,
    data_type: DataType,
    total: int,
) -> None:
    footer = Text()

    footer.append(
        f"{total:,}",
        style="bold",
    )

    footer.append(
        " instruments",
        style="dim",
    )

    footer.append(
        "   •   ",
        style="dim",
    )

    footer.append(
        exchange.value.upper(),
        style="cyan",
    )

    footer.append(
        "   •   ",
        style="dim",
    )

    footer.append(
        instrument_type.value.upper(),
        style="bold",
    )

    footer.append(
        "   •   ",
        style="dim",
    )

    footer.append(
        data_type.value.upper(),
        style="magenta",
    )

    console.rule(
        footer,
        style="dim",
    )
