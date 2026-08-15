from __future__ import annotations

from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


console = Console()


def human_size(size: int) -> str:
    value = float(size)

    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024:
            return f"{value:.1f} {unit}"

        value /= 1024

    return f"{value:.1f} PB"


def show_job(
    *,
    symbol: str,
    margin: str,
    data_type: str,
    start_date: str,
    end_date: str,
    output_dir: str,
    chunks: int,
) -> None:
    grid = Table.grid(
        padding=(0, 2),
    )

    grid.add_column(
        style="dim",
        width=12,
    )

    grid.add_column(
        style="bold",
    )

    grid.add_row(
        "Symbol",
        f"[bold cyan]{symbol}[/bold cyan]",
    )

    grid.add_row(
        "Market",
        margin.upper(),
    )

    grid.add_row(
        "Dataset",
        data_type.upper(),
    )

    grid.add_row(
        "Date range",
        f"{start_date}  →  {end_date}",
    )

    grid.add_row(
        "Chunks",
        str(chunks),
    )

    grid.add_row(
        "Output",
        output_dir,
    )

    console.print()

    console.print(
        Panel(
            grid,
            title="[bold cyan] BYBIT HISTORY [/bold cyan]",
            subtitle="[dim]Historical market data, without the clicks[/dim]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    console.print()


def step(message: str) -> None:
    console.print(f"  [bold green]✓[/bold green] {message}")


def action(message: str) -> None:
    console.print(f"  [bold cyan]→[/bold cyan] {message}")


def warning(message: str) -> None:
    console.print(f"  [bold yellow]![/bold yellow] {message}")


def show_complete(
    paths: list[Path],
    *,
    elapsed: float,
    output_dir: str,
) -> None:
    console.print()

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold",
        expand=False,
    )

    table.add_column(
        "File",
        style="bold",
    )

    table.add_column(
        "Size",
        justify="right",
    )

    table.add_column(
        "Status",
        justify="center",
    )

    total_size = 0

    for path in paths:
        path = Path(path)

        try:
            size = path.stat().st_size
        except OSError:
            size = 0

        total_size += size

        table.add_row(
            path.name,
            human_size(size),
            "[green]✓ Ready[/green]",
        )

    summary = Table.grid(
        padding=(0, 2),
    )

    summary.add_column(
        style="dim",
        width=12,
    )

    summary.add_column(
        style="bold",
    )

    summary.add_row(
        "Files",
        str(len(paths)),
    )

    summary.add_row(
        "Total",
        human_size(total_size),
    )

    summary.add_row(
        "Time",
        f"{elapsed:.1f} seconds",
    )

    summary.add_row(
        "Output",
        output_dir,
    )

    console.print(
        Panel(
            table,
            title="[bold green] DOWNLOAD COMPLETE [/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )

    console.print(summary)
    console.print()
