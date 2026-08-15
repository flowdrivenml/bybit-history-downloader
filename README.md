# Bybit History Downloader

[![PyPI version](https://img.shields.io/pypi/v/bybit-history-downloader.svg)](https://pypi.org/project/bybit-history-downloader/0.1.0/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](#requirements)
[![Platform](https://img.shields.io/badge/platform-Linux-informational.svg)](#requirements)
[![Browser](https://img.shields.io/badge/browser-Firefox-orange.svg)](#requirements)

**Historical market data, without the repetitive clicks.**

Bybit History Downloader is a Python CLI and library that automates downloads from Bybit’s public historical-data page.

I built it while collecting market data for research and experiments. The files are publicly available, but downloading longer periods manually means repeating the same browser workflow for every symbol and date range.

The downloader handles that workflow for you: it opens the page, selects the market and dataset, finds the requested symbol, divides longer date ranges into smaller chunks, downloads the files, and extracts them locally.

> **Current support:** Linux distributions and Firefox only. Chromium, WebKit, native Windows, and macOS are not supported in the current release.

> This project uses browser automation. It is not an official Bybit API client.

## Demo

![Bybit historical-data download](https://raw.githubusercontent.com/flowdrivenml/bybit-history-downloader/main/images/data.png)

The terminal interface shows the requested market, dataset, symbol, date range, progress, produced files, final sizes, and output directory.

## Features

* Spot and Contract markets
* Historical trades
* L2 order-book depth data
* Available-symbol discovery
* Automatic date-range chunking
* Headless and visible Firefox execution
* Progress bars and structured terminal output
* Automatic extraction of `.zip` and `.gz` files
* Collection of multiple files triggered by one download
* Python API and command-line interface
* No API key or Bybit account required
* Installable directly from PyPI

## Installation

The package is available on [PyPI](https://pypi.org/project/bybit-history-downloader/0.1.0/).

A virtual environment is recommended:

```bash
python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install bybit-history-downloader
```

Playwright installs its browser separately. Install Firefox after installing the package:

```bash
python -m playwright install firefox
```

If your Linux distribution is missing Firefox system dependencies, install them with:

```bash
python -m playwright install-deps firefox
```

Confirm that the CLI is available:

```bash
bybit-history --help
```

## Requirements

* Linux
* Python 3.10 or newer
* Playwright Firefox

Firefox is the only supported browser in the current release.

The CLI runs headlessly by default. Add `--no-headless` before the command to watch the browser automation in real time:

```bash
bybit-history --no-headless symbols contract
```

Visible mode is also useful when Bybit changes part of its interface or behaves differently during a headless session.

## Usage

The CLI provides two main commands:

```text
symbols     List the symbols currently available in Bybit's interface
download    Download historical data for one symbol and date range
```

Global options such as `--no-headless` must be placed before `symbols` or `download`.

## List available symbols

List Contract symbols:

```bash
bybit-history --no-headless symbols contract
```

List Spot symbols:

```bash
bybit-history --no-headless symbols spot
```

The symbol list is rendered in a compact multi-column terminal view:

![Available Bybit symbols](https://raw.githubusercontent.com/flowdrivenml/bybit-history-downloader/main/images/symbols.png)

Bybit uses a virtualized symbol list, so the program scrolls through the dropdown and collects symbols as they appear. This can take a moment, especially when the market contains many instruments.

## Download historical data

### Contract trades

```bash
bybit-history --no-headless download contract trades \
  --symbol BTCUSDT \
  --start 2026-08-01 \
  --end 2026-08-05 \
  --out ./data/trades \
  --chunk-days 5
```

### Spot trades

```bash
bybit-history --no-headless download spot trades \
  --symbol BTCUSDT \
  --start 2026-08-01 \
  --end 2026-08-05 \
  --out ./data/trades \
  --chunk-days 5
```

### Contract L2 order-book data

```bash
bybit-history --no-headless download contract l2book \
  --symbol BTCUSDT \
  --start 2026-08-01 \
  --end 2026-08-05 \
  --out ./data/l2book \
  --chunk-days 5
```

To run without displaying the browser, omit `--no-headless`:

```bash
bybit-history download contract trades \
  --symbol BTCUSDT \
  --start 2026-08-01 \
  --end 2026-08-05 \
  --out ./data/trades \
  --chunk-days 5
```

## Output formats

The downloader preserves the data format provided by Bybit:

| Dataset             | Extracted format |
| ------------------- | ---------------- |
| Trades              | `.csv`           |
| L2 order-book depth | `.jsonl`         |

Downloaded archives are processed automatically:

* `.zip` archives are extracted
* `.gz` files are decompressed
* compressed archives are removed after successful extraction
* extracted files remain in the directory passed to `--out`

For example:

```text
data/
└── trades/
    ├── BTCUSDT2026-08-01.csv
    └── BTCUSDT2026-08-02.csv
```

L2 order-book datasets can be significantly larger than trade datasets, especially over longer periods.

## Date chunking

Bybit’s interface accepts relatively small date windows for this workflow. The downloader therefore divides longer requests into smaller inclusive ranges.

For example:

```text
Requested range: 2026-08-01 → 2026-08-12
Chunk size:      5 days

Generated chunks:
2026-08-01 → 2026-08-05
2026-08-06 → 2026-08-10
2026-08-11 → 2026-08-12
```

The chunk size must be greater than zero and smaller than six:

```bash
--chunk-days 5
```

The CLI rejects invalid values before starting the browser.

## Python API

The downloader can also be used directly from Python:

```python
import asyncio
from pathlib import Path

from bybit_history import BybitHistoryClient


async def main() -> None:
    async with BybitHistoryClient(
        browser_name="firefox",
        headless=False,
    ) as client:
        files: list[Path] = await client.download_data(
            margin="Contract",
            data_type="Trades",
            symbol="BTCUSDT",
            start_date="2026-08-01",
            end_date="2026-08-05",
            final_path="./data/trades",
            chunk_days=5,
        )

    for file in files:
        print(file)


if __name__ == "__main__":
    asyncio.run(main())
```

`download_data()` returns the paths produced after downloading and extraction.

## How it works

The automated workflow is roughly:

```text
Open Bybit historical-data page
        ↓
Recover from an initial regional redirect when necessary
        ↓
Select Trades or OrderBook
        ↓
Select Spot or Contract
        ↓
Open the virtualized symbol list
        ↓
Scroll until the requested symbol is found
        ↓
Select the Everyday frequency
        ↓
Enter the requested date range
        ↓
Confirm and collect download events
        ↓
Save and extract the downloaded files
```

## Why Playwright?

The files are exposed through Bybit’s website, where the interface controls market selection, dataset selection, symbols, date ranges, and download actions.

A direct HTTP downloader would be simpler if a stable public file endpoint covered the same workflow. This project instead automates the interface that Bybit currently exposes, allowing the process to run from a terminal or Python program without repeating the same browser actions manually.

## Implementation details

Two parts of the workflow required more than ordinary button clicking.

### Virtualized symbol list

Bybit does not render every symbol in the document at once. Only the currently visible part of the dropdown exists in the page.

The client therefore positions the mouse inside the open list, scrolls it in small steps, and checks the newly rendered options until it finds the requested symbol or reaches the search limit.

The `symbols` command uses the same mechanism to collect the complete visible catalogue.

### Multiple download events

One download action can trigger more than one file. The client listens for the first Playwright download event and continues collecting additional events for a short period before saving and processing the results.

### Automatic extraction

Downloaded files are saved using Bybit’s suggested filenames. ZIP and GZIP archives are extracted automatically, and the processed archives are removed afterward.

## Development installation

Clone the repository:

```bash
git clone https://github.com/flowdrivenml/bybit-history-downloader.git
cd bybit-history-downloader
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project in editable mode:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest pytest-asyncio
python -m playwright install firefox
```

Run the tests:

```bash
pytest -v
```

Run the local CLI:

```bash
bybit-history --help
```

## Limitations

This project depends on the structure and visible text of Bybit’s public website. A substantial redesign may require selector updates.

Current limitations include:

* Linux only
* Firefox only
* `chunk-days` must remain below six
* symbol discovery may take time because the list is virtualized
* availability depends on the market, symbol, dataset, and requested date range
* L2 order-book files can be very large
* browser automation is slower and more fragile than a stable direct-download API
* headless and visible sessions may occasionally behave differently

When an interaction fails, visible mode is the easiest way to inspect what happened:

```bash
bybit-history --no-headless download contract trades \
  --symbol BTCUSDT \
  --start 2026-08-01 \
  --end 2026-08-05 \
  --out ./data/trades
```

## Disclaimer

This project is not affiliated with, maintained by, or endorsed by Bybit.

It automates access to Bybit’s public historical-data interface. Users are responsible for following Bybit’s terms, applicable limits, and any requirements governing their use of the downloaded data.

