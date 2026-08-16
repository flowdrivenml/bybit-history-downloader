# Bybit Historical Market Data Downloader

[![PyPI version](https://img.shields.io/pypi/v/bybit-history-downloader.svg)](https://pypi.org/project/bybit-history-downloader/0.1.0/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](#requirements)
[![Platform](https://img.shields.io/badge/platform-Linux-informational.svg)](#requirements)
[![Browser](https://img.shields.io/badge/browser-Firefox-orange.svg)](#requirements)

**Historical market data, without the repetitive clicks.**

Python CLI and library for downloading public Bybit historical market data.

It automates symbol selection, date ranges, downloads, chunking, and extraction for longer research datasets.

> **Current support:** Linux + Firefox.

---

## Quick Navigation

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Python API](#python-api)
- [Output](#output)
- [Limitations](#limitations)

## Features

- Spot and Contract markets
- Historical trades
- L2 order-book data
- Automatic date-range chunking
- Symbol discovery
- Automatic `.zip` and `.gz` extraction
- Headless execution
- CLI and Python API
- No API key required
- Available on PyPI

## Installation

```bash
python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install bybit-history-downloader
python -m playwright install firefox
```

If Firefox dependencies are missing:

```bash
python -m playwright install-deps firefox
```

Check the installation:

```bash
bybit-history --help
```

## Usage

### List symbols

Contract:

```bash
bybit-history symbols contract
```

Spot:

```bash
bybit-history symbols spot
```

### Download trades

```bash
bybit-history download contract trades \
  --symbol BTCUSDT \
  --start 2026-08-01 \
  --end 2026-08-05 \
  --out ./data/trades \
  --chunk-days 5
```

### Download L2 order-book data

```bash
bybit-history download contract l2book \
  --symbol BTCUSDT \
  --start 2026-08-01 \
  --end 2026-08-05 \
  --out ./data/l2book \
  --chunk-days 5
```

Long date ranges are automatically divided into smaller chunks.

For debugging, run with a visible browser:

```bash
bybit-history --no-headless symbols contract
```

## Python API

The downloader can also be used directly from Python:

```python
import asyncio
from pathlib import Path

from bybit_history import BybitHistoryClient


async def main() -> None:
    async with BybitHistoryClient(
        browser_name="firefox",
        headless=True,
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

## Output

Downloaded archives are extracted automatically.

| Dataset | Output |
|---|---|
| Trades | `.csv` |
| L2 order book | `.jsonl` |

Example:

```text
data/
└── trades/
    ├── BTCUSDT2026-08-01.csv
    └── BTCUSDT2026-08-02.csv
```

## Limitations

- Linux only
- Firefox only
- `chunk-days` must be below `6`
- Symbol discovery can take some time
- L2 datasets can be very large
- Website changes may require selector updates

This project is not affiliated with or endorsed by Bybit.
