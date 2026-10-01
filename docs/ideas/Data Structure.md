## Structure

MarketForge separates **immutable source data** from **derived research datasets**.

```text
data/
├── raw/
├── datasets/
└── tmp/
```

```text
Exchange
   ↓
raw/
   ↓
normalize / validate / merge / align
   ↓
datasets/
   ↓
analysis / research / ML
```

## Raw Data

`raw/` contains the original exchange files exactly as downloaded.

```text
raw/
├── bybit/
├── binance/
├── okx/
├── gateio/
└── bitget/
```

Organize within each exchange by market, data type, and symbol:

```text
raw/
└── bybit/
    └── spot/
        ├── trades/
        │   └── BTCUSDT/
        └── depth/
            └── BTCUSDT/
```

Raw data is **immutable**. It is never normalized, merged, renamed unnecessarily, or overwritten.

It is the source from which every downstream dataset must be reproducible.

## Datasets

`datasets/` contains complete MarketForge outputs.

Each directory represents **one generated dataset / experiment**:

```text
datasets/
├── btc_cross_exchange/
│   ├── manifest.json
│   ├── processing.json
│   ├── quality.json
│   └── data/
│       ├── part-000.parquet
│       └── part-001.parquet
│
└── multi_asset_microstructure/
    ├── manifest.json
    ├── processing.json
    ├── quality.json
    └── data/
        └── *.parquet
```

A dataset may contain any valid combination:

```text
single exchange × single symbol
multiple exchanges × single symbol
single exchange × multiple symbols
multiple exchanges × multiple symbols

trades
depth
trades + depth

spot
linear
inverse
options
multiple market types
```

There is therefore **no separate `merged/` or `cross_exchange/` directory**.

Merging and cross-exchange alignment are processing operations, not storage categories.

## Dataset Metadata

Every dataset is self-describing.

### `manifest.json`

Defines **what the dataset contains**:

```json
{
  "name": "btc_cross_exchange",
  "exchanges": ["bybit", "binance", "okx"],
  "markets": ["spot"],
  "symbols": ["BTC-USDT"],
  "data_types": ["trades", "depth"],
  "start": "2026-09-01",
  "end": "2026-09-30",
  "schema_version": 1
}
```

### `processing.json`

Defines **how the dataset was produced**:

```text
source files
normalization configuration
merge configuration
time-alignment method
engine version
creation timestamp
```

### `quality.json`

Records technical and integrity results:

```text
missing intervals
duplicates
invalid records
timestamp problems
order-book inconsistencies
quality/integrity flags
warnings
```

### Parquet

The actual normalized data lives under:

```text
dataset/data/*.parquet
```

Rows should retain provenance where applicable:

```text
exchange
market
native_symbol
canonical_symbol
data_type
timestamp
...
```

Therefore merged observations always remain traceable to their original venue and instrument.

## Temporary Data

`tmp/` contains disposable intermediate state:

```text
partial downloads
temporary decompression
intermediate merge output
retry files
temporary Rust output
```

Deleting `tmp/` must never destroy required source or processed data.

## Rules

```text
raw/
    immutable exchange-native data

datasets/
    self-contained processed datasets + metadata

tmp/
    disposable working state
```

Key principles:

- **Raw data is immutable.**
- **Processed data uses canonical Parquet schemas.**
- **Every dataset is self-contained and reproducible.**
- **Merging is an operation, not a directory type.**
- **Native exchange/symbol identity is preserved after merging.**
- **One dataset may contain arbitrary combinations of exchanges, symbols, markets, trades, and depth.**
- **The manifest describes the dataset instead of encoding its full meaning into the filesystem path.**

> **Acquire once → preserve raw → construct self-describing datasets → reproduce any experiment from its metadata and source data.**
