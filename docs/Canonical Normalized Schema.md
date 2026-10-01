## Goal

MarketForge normalizes exchange-specific raw market data into two canonical datasets:

```text
Trade
L2
```

The canonical schemas preserve economically meaningful market information while removing exchange-specific representation differences.

```text
Raw exchange data
        ↓
Exchange-specific parser
        ↓
Validation
        ↓
Normalization
        ↓
Canonical Trade / L2
        ↓
Partitioned Parquet
        ↓
mlfindgen
```

Raw parsing may require exchange-specific handling for:

```text
containers
timestamps
side encoding
contract quantities
snapshots
deltas
sequence identifiers
update semantics
```

These differences must not create exchange-specific downstream schemas.

---

## Canonical Trade Schema

```text
timestamp
trade_id
side
price

quantity_base
quantity_quote
quantity_contracts

is_rpi
```

| Field | Type | Meaning |
|---|---|---|
| `timestamp` | `int64` | Unix timestamp in nanoseconds |
| `trade_id` | `string` | Exchange trade identifier |
| `side` | enum | `buy` / `sell` |
| `price` | numeric | Execution price |
| `quantity_base` | numeric? | Base-asset quantity |
| `quantity_quote` | numeric? | Quote-asset quantity |
| `quantity_contracts` | numeric? | Contract quantity |
| `is_rpi` | `bool?` | Retail Price Improvement trade |

Quantity fields are nullable because raw quantity representation differs by market and exchange.

Examples:

```text
Spot
├── quantity_base
└── quantity_quote

Linear / inverse derivative
├── quantity_contracts
├── quantity_base?
└── quantity_quote?

Option
└── quantity_contracts
```

Quantities that can be derived safely from instrument metadata may be populated during normalization.

Raw quantities supplied directly by the exchange take precedence over derived quantities.

---

## RPI

RPI means:

```text
Retail Price Improvement
```

It identifies trades involving special price-improvement liquidity intended for eligible retail order flow.

This is economically meaningful microstructure information and cannot generally be reconstructed from ordinary trade fields.

Therefore it is preserved canonically:

```text
is_rpi
```

Mapping examples:

```text
Bybit RPI = 1
→ is_rpi = true

Bybit RPI = 0
→ is_rpi = false

OKX source = 1
→ is_rpi = true

OKX source = 0
→ is_rpi = false

Exchange/source does not provide RPI information
→ is_rpi = null
```

`null` means:

```text
RPI status unavailable
```

not:

```text
definitely non-RPI
```

---

## Derived Trade Features

Some useful microstructure information can be calculated consistently from canonical trades and therefore does not need to be stored as exchange-specific raw fields.

### Tick Direction

Canonical derived feature:

```text
tick_direction
```

Possible values:

```text
plus
minus
zero_plus
zero_minus
```

Derivation:

```text
current_price > previous_price
→ plus

current_price < previous_price
→ minus

current_price == previous_price
and previous non-zero direction was plus
→ zero_plus

current_price == previous_price
and previous non-zero direction was minus
→ zero_minus
```

Bybit provides this directly as:

```text
PlusTick
MinusTick
ZeroPlusTick
ZeroMinusTick
```

MarketForge should derive the same concept consistently for all exchanges.

Bybit's supplied `tickDirection` can be used to validate the implementation.

Tick-direction calculation must preserve continuity across raw file and Parquet partition boundaries.

---

## Option Trade Extension

Options contain economically important trade-time information that does not apply to ordinary Spot or Perpetual trades.

These fields should not be added as mostly-null columns to every Trade dataset.

Use an option-specific extension:

```text
OptionTradeExtra
```

Canonical fields:

```text
implied_volatility
mark_implied_volatility
mark_price
index_price
forward_price
```

| Field | Meaning |
|---|---|
| `implied_volatility` | IV implied by the trade execution |
| `mark_implied_volatility` | Exchange mark/fair IV |
| `mark_price` | Exchange mark price at execution |
| `index_price` | Underlying index price at execution |
| `forward_price` | Forward price at execution when available |

Example Bybit mapping:

```text
iv
→ implied_volatility

mark_iv
→ mark_implied_volatility

mark_price
→ mark_price

index_price
→ index_price
```

OKX exposes equivalent concepts in its broader option-trading interfaces, although the inspected historical option-chain trade archive does not contain them.

Missing source information remains null.

Exchange-provided IV should be preserved because it is model- and convention-dependent and cannot be assumed identical to IV independently recomputed by MarketForge.

MarketForge may later calculate:

```text
computed_iv
```

as a separate derived research feature.

---

## Intentionally Excluded Trade Fields

### Binance `isBestMatch`

The inspected Binance Spot fixture contained:

```text
True = 3,662,805
False = 0
```

The field therefore contained no distinguishing information in the inspected historical dataset.

Treatment:

```text
IGNORE
```

Revisit only if another historical Binance dataset is observed where the field varies.

### Sequence / Validation Fields

Fields primarily used for integrity checking should not automatically enter canonical Trade Parquet.

Examples:

```text
Bybit trade_seq
Bybit book u
Bybit book seq

Gate begin_id
Gate merged_count
```

They are consumed by validation and may be discarded after successful validation.

---

## Timestamp Normalization

All canonical timestamps use:

```text
Unix nanoseconds
```

Conversions:

```text
seconds      × 1_000_000_000
milliseconds × 1_000_000
microseconds × 1_000
```

Fractional-second timestamps should be converted exactly rather than through binary floating-point arithmetic where possible.

Examples:

```text
Gate
1785542402.330460 seconds
→ 1785542402330460000 ns

OKX
1788192000381 ms
→ 1788192000381000000 ns

Bitget
1788192000 seconds effective precision
→ 1788192000000000000 ns
```

Nanosecond storage does not imply that the raw source had nanosecond precision.

MarketForge preserves the information available from the source without inventing additional precision.

---

# Canonical L2 Schema

Use one L2 representation for complete snapshots and incremental updates.

```text
timestamp
event_id
side
price
quantity
order_count
is_snapshot
operation
```

| Field | Type | Meaning |
|---|---|---|
| `timestamp` | `int64` | Unix timestamp in nanoseconds |
| `event_id` | `uint64` | Deterministic logical event identifier |
| `side` | enum | `bid` / `ask` |
| `price` | numeric | Price level |
| `quantity` | numeric | Source-native level quantity |
| `order_count` | `uint32?` | Number of orders at level when available |
| `is_snapshot` | `bool` | Level belongs to a complete snapshot/reset |
| `operation` | enum | `set` / `add` / `subtract` |

All levels belonging to the same logical event share:

```text
timestamp
event_id
is_snapshot
operation
```

---

## L2 Operations

### `set`

```text
level = quantity
```

If:

```text
quantity = 0
```

the price level is removed.

### `add`

```text
level += quantity
```

### `subtract`

```text
level -= quantity
```

If the resulting quantity becomes zero:

```text
remove level
```

Negative reconstructed quantities are invalid and indicate corrupt data, incorrect sequencing, or incorrect interpretation.

---

## Event Grouping

`event_id` identifies one logical raw book event.

It must be:

```text
deterministic
unique within an instrument stream
shared by all levels from the same logical event
```

This is required because timestamp alone does not uniquely identify an event.

Example:

```text
event_id = 100
timestamp = T
is_snapshot = true

→ complete snapshot A
```

and:

```text
event_id = 101
timestamp = T
is_snapshot = true

→ complete snapshot B
```

remain distinct even though they share a timestamp.

---

## L2 Mapping

### Bybit

```text
snapshot
→ is_snapshot = true
→ operation = set

delta
→ is_snapshot = false
→ operation = set
```

Bybit delta quantities represent resulting level quantities.

```text
quantity = 0
→ remove level
```

Raw sequence fields such as:

```text
u
seq
```

are used for validation.

---

### OKX

```text
snapshot
→ is_snapshot = true
→ operation = set

update
→ is_snapshot = false
→ operation = set
```

Raw levels:

```text
[price, quantity, order_count]
```

map directly to:

```text
price
quantity
order_count
```

Zero quantity removes a level.

The inspected historical format does not provide an explicit sequence identifier.

---

### Bitget

Each XLSX row represents an independent complete snapshot:

```text
timestamp
asks
bids
```

Every emitted level receives:

```text
is_snapshot = true
operation = set
```

All levels from the same workbook row share one `event_id`.

Raw workbook rows are not chronologically ordered.

Normalization must:

```text
parse
↓
preserve raw event identity
↓
sort chronologically
↓
preserve duplicate-timestamp events
↓
emit canonical L2
```

No delta reconstruction is required.

---

### Gate.io

Gate uses relative incremental updates.

Initial:

```text
set
set
set
...
```

represents one complete snapshot:

```text
is_snapshot = true
operation = set
```

Subsequent:

```text
make
→ is_snapshot = false
→ operation = add

take
→ is_snapshot = false
→ operation = subtract
```

For Gate Futures, signed quantity also encodes side:

```text
size > 0 → bid
size < 0 → ask

quantity = abs(size)
```

---

## Gate L2 Semantics Verification

Gate historical `make` / `take` semantics were verified empirically using cross-hour reconstruction.

Observed semantics:

```text
set  → set absolute level quantity
make → add quantity to level
take → subtract quantity from level
```

The complete Gate Linear Perpetual book for the `2026-09-07 00:00` archive was reconstructed from its initial snapshot and every subsequent update.

The reconstructed final state was compared with the initial snapshot of the `01:00` archive.

Result:

```text
RECONSTRUCTED LEVELS: 42158
NEXT SNAPSHOT LEVELS: 42158

MATCHING:          42158
MISSING:               0
EXTRA:                 0
QUANTITY MISMATCH:     0
```

The reconstruction matched exactly.

Therefore Gate mapping is confirmed:

| Raw Event | Snapshot | Operation |
|---|---:|---|
| `set` | `true` | `set` |
| `make` | `false` | `add` |
| `take` | `false` | `subtract` |

---

## Universal L2 Mapping

| Source | Raw Event | Snapshot | Operation |
|---|---|---:|---|
| Bybit | snapshot | `true` | `set` |
| Bybit | delta | `false` | `set` |
| OKX | snapshot | `true` | `set` |
| OKX | update | `false` | `set` |
| Bitget | snapshot row | `true` | `set` |
| Gate.io | `set` | `true` | `set` |
| Gate.io | `make` | `false` | `add` |
| Gate.io | `take` | `false` | `subtract` |

This allows all inspected L2 formats to use one canonical representation without losing their update semantics.

---

# Raw Sequence Information

Exchange-specific sequence fields remain part of parsing and validation.

Examples:

```text
Bybit
u
seq

Gate.io
begin_id
merged_count

OKX
none in inspected historical format

Bitget
none
```

Pipeline:

```text
raw sequence information
        ↓
integrity validation
        ↓
canonical normalized events
```

Gate continuity rule:

```text
next.begin_id =
    current.begin_id + current.merged_count
```

Sequence failures must be reported rather than silently repaired.

---

# Instrument Metadata

Instrument identity and contract specifications are maintained separately from individual market-data rows.

Minimal metadata:

```text
exchange
symbol
instrument_type
market_category

base_asset
quote_asset
settlement_asset

contract_value
contract_value_asset

expiry
strike
option_type
```

| Field | Meaning |
|---|---|
| `exchange` | Source exchange |
| `symbol` | Exchange-native instrument identifier |
| `instrument_type` | `spot`, `perpetual`, `future`, `option` |
| `market_category` | `spot`, `linear`, `inverse`, `option` |
| `base_asset` | Base/underlying asset |
| `quote_asset` | Price quote asset |
| `settlement_asset` | Settlement/margin asset |
| `contract_value` | Economic value represented by one contract |
| `contract_value_asset` | Unit in which contract value is expressed |
| `expiry` | Expiration for dated instruments |
| `strike` | Option strike |
| `option_type` | `call` / `put` |

---

## Contract Quantity Conversion

If contract value is expressed in the base asset:

```text
quantity_base =
    quantity_contracts × contract_value

quantity_quote =
    quantity_base × price
```

If contract value is expressed in the quote asset:

```text
quantity_quote =
    quantity_contracts × contract_value

quantity_base =
    quantity_quote / price
```

If the relationship cannot be established safely:

```text
preserve quantity_contracts
leave derived quantities null
```

Never guess contract semantics.

---

# Parquet Partitioning

Partition-level identity should not be repeated in every tick row.

Conceptually:

```text
exchange=okx/
instrument_type=perpetual/
market_category=linear/
symbol=BTC-USDT-SWAP/
date=2026-09-01/
```

Canonical partition dates are derived from normalized UTC timestamps.

Do not blindly use raw archive filename dates because some providers use non-UTC archive boundaries.

---

## Trade Parquet

Core:

```text
timestamp
trade_id
side
price
quantity_base
quantity_quote
quantity_contracts
is_rpi
```

Optional option extension:

```text
implied_volatility
mark_implied_volatility
mark_price
index_price
forward_price
```

Derived features such as:

```text
tick_direction
```

can be calculated consistently from canonical trades.

---

## L2 Parquet

```text
timestamp
event_id
side
price
quantity
order_count
is_snapshot
operation
```

---

# Architecture

```text
RAW
 │
 ├── Bybit parser
 ├── Binance parser
 ├── OKX parser
 ├── Bitget parser
 └── Gate.io parser
 │
 ▼
Raw validation
 │
 ▼
Normalization
 │
 ├────────────────────────────────┐
 ▼                                ▼
Trade                              L2
 │                                 │
timestamp                          timestamp
trade_id                           event_id
side                               side
price                              price
quantity_base                      quantity
quantity_quote                     order_count
quantity_contracts                 is_snapshot
is_rpi                             operation
 │                                 │
 ├── OptionTradeExtra              │
 │                                 │
 └───────────────┬─────────────────┘
                 ▼
         Partitioned Parquet
                 ▼
              mlfindgen
```

---

# Design Rules

The canonical model must:

- preserve the highest timestamp precision supplied by the source;
- preserve trade identity;
- preserve base, quote, and contract quantity distinctions;
- preserve RPI information when supplied;
- preserve economically important option trade information;
- derive universal features such as tick direction consistently across exchanges;
- use one L2 interface across all exchanges;
- preserve logical L2 event boundaries;
- preserve absolute versus relative L2 update semantics;
- use instrument metadata for contract interpretation;
- validate exchange sequence information before discarding validation-only fields;
- avoid repeating partition-level identity fields in every row;
- never silently discard a raw field without an explicit classification;
- preserve raw anomalies through validation rather than silently correcting them.

---

# Canonical Schemas

## Trade

```text
timestamp
trade_id
side
price
quantity_base
quantity_quote
quantity_contracts
is_rpi
```

## Option Trade Extension

```text
implied_volatility
mark_implied_volatility
mark_price
index_price
forward_price
```

## L2

```text
timestamp
event_id
side
price
quantity
order_count
is_snapshot
operation
```

## Instrument Metadata

```text
exchange
symbol
instrument_type
market_category

base_asset
quote_asset
settlement_asset

contract_value
contract_value_asset

expiry
strike
option_type
```

These schemas define the current canonical normalization target for MarketForge.