## Purpose

`engine.db` is MarketForge's persistent metadata and catalog database.

It stores:

```text
exchanges
instruments
instrument specifications
raw format definitions
normalization rules
dataset state
raw exchange metadata
```

It does **not** store trades, L2 events, or normalized market observations. Those belong in Parquet. :chatgpt-content-reference{index="0"}

Runtime database:

```text
data/catalog/engine.db
```

---

## Architecture

```text
Exchange APIs
      ↓
providers
      ↓
engine.db
      ↓
normalization
      ↓
Rust engine
      ↓
Parquet
```

Responsibilities:

```text
providers       → exchange APIs and terminology
catalog         → persistent metadata and state
normalization   → canonical interpretation
engine          → high-throughput processing
```

---

# Schema

## exchanges

```sql
CREATE TABLE exchanges (
    id          INTEGER PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Examples:

```text
bybit
binance
okx
bitget
gateio
```

---

## instruments

One row per exchange instrument.

```sql
CREATE TABLE instruments (
    id                  INTEGER PRIMARY KEY,

    exchange_id         INTEGER NOT NULL,
    symbol              TEXT NOT NULL,

    instrument_type     TEXT NOT NULL,
    market_category     TEXT NOT NULL,

    base_asset          TEXT,
    quote_asset         TEXT,
    settlement_asset    TEXT,

    launch_time_ns      INTEGER,
    expiry_ns           INTEGER,

    strike              TEXT,
    option_type         TEXT,

    status              TEXT,

    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (exchange_id)
        REFERENCES exchanges(id),

    UNIQUE(exchange_id, symbol)
);
```

Canonical values:

```text
instrument_type:
    spot
    perpetual
    future
    option

market_category:
    spot
    linear
    inverse
    option

option_type:
    call
    put
    NULL
```

Decimal values such as `strike` are stored as text to preserve exact representation.

---

## instrument_specs

Normalization and trading specifications for an instrument.

```sql
CREATE TABLE instrument_specs (
    instrument_id          INTEGER PRIMARY KEY,

    quantity_type          TEXT NOT NULL,

    contract_value         TEXT,
    contract_value_asset   TEXT,

    tick_size              TEXT,
    qty_step               TEXT,
    min_qty                TEXT,
    max_qty                TEXT,
    min_notional           TEXT,

    fetched_at             TEXT NOT NULL,

    FOREIGN KEY (instrument_id)
        REFERENCES instruments(id)
        ON DELETE CASCADE
);
```

`quantity_type` describes what the exchange's raw quantity represents:

```text
base
quote
contracts
```

Examples:

```text
Bybit BTCUSDT Spot
quantity_type = base

Bybit BTCUSDT Linear
quantity_type = base

Bybit BTCUSD Inverse
quantity_type = quote

Bybit BTC Option
quantity_type = base

Binance BTCUSD inverse contract
quantity_type        = contracts
contract_value       = 100
contract_value_asset = USD
```

Generic normalization:

```text
quantity_type = base
    quantity_base = raw_quantity
    quantity_quote = quantity_base × price

quantity_type = quote
    quantity_quote = raw_quantity
    quantity_base = quantity_quote / price

quantity_type = contracts
    raw_quantity
        ↓
    contract_value
    contract_value_asset
        ↓
    quantity_base
    quantity_quote
```

If contract conversion is unknown, preserve the contract quantity and leave derived quantities null.

Never guess.

---

## instrument_api_raw

Preserves the original exchange API metadata.

```sql
CREATE TABLE instrument_api_raw (
    id              INTEGER PRIMARY KEY,
    instrument_id   INTEGER NOT NULL,

    fetched_at      TEXT NOT NULL,
    raw_json        TEXT NOT NULL,

    FOREIGN KEY (instrument_id)
        REFERENCES instruments(id)
        ON DELETE CASCADE
);
```

Flow:

```text
Exchange API
     │
     ├── raw response → instrument_api_raw
     │
     └── parsed data
             ├── instruments
             └── instrument_specs
```

Keeping the original response allows metadata interpretation to evolve without losing exchange information.

---

## raw_formats

Registry of known physical raw formats.

```sql
CREATE TABLE raw_formats (
    id              TEXT PRIMARY KEY,
    exchange_id     INTEGER NOT NULL,
    data_type       TEXT NOT NULL,
    description     TEXT,

    FOREIGN KEY (exchange_id)
        REFERENCES exchanges(id)
);
```

Examples:

```text
BYBIT-T1
BYBIT-T2
BYBIT-T3
BYBIT-B1
BYBIT-B2

BINANCE-T1
BINANCE-T2
BINANCE-T3

OKX-T1
OKX-B1
OKX-B2

BITGET-T1
BITGET-B1

GATE-T1
GATE-T2
GATE-B1
GATE-B2
```

`data_type`:

```text
trade
l2
```

---

## normalization_rules

Documents raw → canonical mappings.

```sql
CREATE TABLE normalization_rules (
    id                  INTEGER PRIMARY KEY,

    raw_format_id       TEXT NOT NULL,
    source_field        TEXT NOT NULL,
    canonical_field     TEXT,

    classification      TEXT NOT NULL,
    transformation      TEXT,
    notes               TEXT,

    FOREIGN KEY (raw_format_id)
        REFERENCES raw_formats(id)
        ON DELETE CASCADE
);
```

Classification:

```text
map
derive
metadata
validate
extra
ignore
```

Examples:

```text
OKX-T1
created_time
→ timestamp
map
milliseconds_to_nanoseconds
```

```text
Bybit RPI
→ is_rpi
map
boolean
```

```text
Bybit tickDirection
→ derived tick_direction validation
validate
```

```text
Binance isBestMatch
→ ignore
```

The database describes mappings.

Complex transformations remain implemented and tested in Python/Rust. SQLite must not contain executable normalization code.

---

# Relationships

```text
exchanges
    │
    ├───────────────┐
    ▼               ▼
instruments     raw_formats
    │               │
    │               ▼
    │       normalization_rules
    │
    ├───────────────┐
    ▼               ▼
instrument_specs   instrument_api_raw
    │
    └───────────────┐
                    ▼
                 datasets
```

---

# Runtime Flow

## Metadata

```text
Exchange API
     ↓
provider/instruments.py
     ↓
canonical metadata
     ↓
engine.db

├── instruments
├── instrument_specs
└── instrument_api_raw
```

## Normalization

```text
raw file
   ↓
raw_format
   ↓
normalization mapping
   ↓
instrument metadata
   ↓
canonical Trade / L2
   ↓
Parquet
```

Example:

```text
raw quantity
     ↓
quantity_type
     │
     ├── base
     ├── quote
     └── contracts
             ↓
        contract metadata
     ↓
quantity_base
quantity_quote
quantity_contracts
```

---

# Code Layout

```text
src/marketforge/
├── catalog/
│   ├── __init__.py
│   ├── database.py
│   ├── schema.py
│   ├── models.py
│   └── repository.py
│
├── normalization/
│   ├── __init__.py
│   ├── mappings.py
│   ├── quantities.py
│   └── metadata.py
│
└── providers/
    ├── bybit/
    │   └── instruments.py
    ├── binance/
    │   └── instruments.py
    ├── okx/
    │   └── instruments.py
    ├── bitget/
    │   └── instruments.py
    └── gateio/
        └── instruments.py
```

Runtime:

```text
data/catalog/engine.db
```

Tests:

```text
tests/unit/catalog/
tests/unit/normalization/
```

---

# Responsibilities

## `catalog/database.py`

```text
connection
PRAGMA configuration
transactions
initialization
```

## `catalog/schema.py`

```text
DDL
schema version
migrations
```

## `catalog/models.py`

Typed metadata models:

```text
Exchange
Instrument
InstrumentSpec
RawFormat
NormalizationRule
Dataset
```

## `catalog/repository.py`

Database operations:

```text
upsert_exchange

upsert_instrument
get_instrument
list_instruments

upsert_instrument_spec
get_instrument_spec

store_raw_instrument_metadata

register_raw_format
register_normalization_rule

register_dataset
update_dataset_status
```

Provider modules must not contain raw SQL.

---

# Scope

SQLite stores:

```text
instrument metadata
normalization metadata
raw format definitions
dataset/catalog state
raw API metadata
```

SQLite does not store:

```text
trade ticks
L2 events
normalized market observations
```

Those belong in Parquet.

---

# Current Schema

```text
engine.db
├── exchanges
├── instruments
├── instrument_specs
├── instrument_api_raw
├── raw_formats
├── normalization_rules
└── datasets
```

This is the MarketForge v1 catalog schema.

Keep it intentionally small. Add fields or tables only when an actual provider or normalization requirement demonstrates that they are necessary.