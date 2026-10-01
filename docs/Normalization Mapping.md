## Goal

Map every inspected raw MarketForge format into the canonical normalized schemas.

The mapping must explicitly classify every raw field as one of:

```text
MAP         → written directly to canonical output
DERIVE      → deterministically calculated
METADATA    → requires instrument metadata
VALIDATE    → used during parsing/integrity checks
EXTRA       → valuable source information not represented by current canonical schema
IGNORE      → intentionally discarded
```

No source field should disappear silently.

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
```

| Field | Type | Meaning |
|---|---|---|
| `timestamp` | `int64` | Unix nanoseconds |
| `trade_id` | `string` | Exchange trade identifier |
| `side` | enum | `buy` / `sell` |
| `price` | `float64` | Execution price |
| `quantity_base` | `float64?` | Base-asset quantity |
| `quantity_quote` | `float64?` | Quote-asset quantity |
| `quantity_contracts` | `float64?` | Contract quantity |

---

## Canonical L2 Schema

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
| `timestamp` | `int64` | Unix nanoseconds |
| `event_id` | `uint64` | Deterministic logical event identifier |
| `side` | enum | `bid` / `ask` |
| `price` | `float64` | Price level |
| `quantity` | `float64` | Source-native level quantity |
| `order_count` | `uint32?` | Number of orders when provided |
| `is_snapshot` | `bool` | Part of complete book snapshot/reset |
| `operation` | enum | `set` / `add` / `subtract` |

`quantity` preserves the source-native book quantity.

Its unit is determined by instrument metadata:

```text
base asset
contracts
other exchange-defined unit
```

---

# Common Conversions

## Timestamp

Canonical timestamp:

```text
Unix nanoseconds
```

Conversions:

```text
seconds      × 1_000_000_000
milliseconds × 1_000_000
microseconds × 1_000
```

Fractional seconds must be converted exactly rather than through binary floating-point where possible.

---

## Side

Canonical Trade:

```text
buy
sell
```

Canonical L2:

```text
bid
ask
```

Exchange-specific side encodings are converted during normalization.

---

# Trades

## BYBIT-T1 — Spot Trades

Raw:

```text
id,timestamp,price,volume,side,rpi
```

| Raw | Canonical | Rule |
|---|---|---|
| `id` | `trade_id` | MAP |
| `timestamp` | `timestamp` | ms → ns |
| `price` | `price` | MAP |
| `volume` | `quantity_base` | MAP |
| `side` | `side` | lowercase `buy` / `sell` |
| `price × volume` | `quantity_quote` | DERIVE |
| — | `quantity_contracts` | null |
| `rpi` | — | EXTRA |

### Extra Raw Information

```text
rpi
```

The current canonical Trade schema does not preserve the RPI flag.

---

## BYBIT-T2 — Linear Perpetual Trades

Raw:

```text
timestamp
symbol
side
size
price
tickDirection
trdMatchID
grossValue
homeNotional
foreignNotional
RPI
```

| Raw | Canonical | Rule |
|---|---|---|
| `timestamp` | `timestamp` | fractional seconds → ns |
| `trdMatchID` | `trade_id` | MAP |
| `side` | `side` | lowercase |
| `price` | `price` | MAP |
| `homeNotional` / `size` | `quantity_base` | MAP |
| `foreignNotional` | `quantity_quote` | MAP |
| — | `quantity_contracts` | null |

Observed invariant:

```text
homeNotional = size
foreignNotional = size × price
grossValue = foreignNotional × 1e8
```

### Validation Fields

```text
grossValue
```

May validate notional consistency.

### Extra Raw Information

```text
tickDirection
RPI
```

Not represented by the current canonical Trade schema.

---

## BYBIT-T2 — Inverse Perpetual Trades

Same physical parser as Linear.

| Raw | Canonical | Rule |
|---|---|---|
| `timestamp` | `timestamp` | fractional seconds → ns |
| `trdMatchID` | `trade_id` | MAP |
| `side` | `side` | lowercase |
| `price` | `price` | MAP |
| `foreignNotional` | `quantity_base` | MAP |
| `homeNotional` | `quantity_quote` | MAP |
| `size` | `quantity_contracts` | MAP |

Observed invariant:

```text
homeNotional = size
foreignNotional = size / price
grossValue = foreignNotional × 1e8
```

### Extra Raw Information

```text
tickDirection
RPI
```

---

## BYBIT-T3 — Option Trades

Raw:

```text
trade_id
trade_seq
timestamp
instrument_name
direction
price
amount
iv
index_price
mark_price
mark_iv
```

| Raw | Canonical | Rule |
|---|---|---|
| `trade_id` | `trade_id` | MAP |
| `timestamp` | `timestamp` | ms → ns |
| `direction` | `side` | lowercase |
| `price` | `price` | MAP |
| `amount` | `quantity_contracts` | MAP |
| — | `quantity_base` | null |
| — | `quantity_quote` | null |
| `trade_seq` | — | VALIDATE / provenance |

### Extra Raw Information

```text
iv
index_price
mark_price
mark_iv
```

These are valuable option-market fields and are not represented by the current canonical Trade schema.

---

## BINANCE-T1 — Spot Trades

Raw positional schema:

```text
trade_id
price
qty
quoteQty
time
isBuyerMaker
isBestMatch
```

| Raw | Canonical | Rule |
|---|---|---|
| column 1 | `trade_id` | MAP |
| column 2 | `price` | MAP |
| column 3 | `quantity_base` | MAP |
| column 4 | `quantity_quote` | MAP |
| column 5 | `timestamp` | µs → ns |
| column 6 | `side` | derive from buyer-maker |
| — | `quantity_contracts` | null |

Side:

```text
isBuyerMaker = false → buy
isBuyerMaker = true  → sell
```

Validation:

```text
quoteQty = price × qty
```

### Extra Raw Information

```text
isBestMatch
```

Not represented by the current canonical Trade schema.

---

## BINANCE-T2 — Linear Perpetual Trades

Raw:

```text
id,price,qty,quote_qty,time,is_buyer_maker
```

| Raw | Canonical | Rule |
|---|---|---|
| `id` | `trade_id` | MAP |
| `price` | `price` | MAP |
| `qty` | `quantity_base` | MAP |
| `quote_qty` | `quantity_quote` | MAP |
| `time` | `timestamp` | ms → ns |
| `is_buyer_maker` | `side` | derive |
| — | `quantity_contracts` | null |

Side:

```text
false → buy
true  → sell
```

Validation:

```text
quote_qty = price × qty
```

Trade IDs are unique but should not be assumed contiguous.

---

## BINANCE-T3 — Inverse Perpetual Trades

Raw:

```text
id,price,qty,base_qty,time,is_buyer_maker
```

| Raw | Canonical | Rule |
|---|---|---|
| `id` | `trade_id` | MAP |
| `price` | `price` | MAP |
| `qty` | `quantity_contracts` | MAP |
| `base_qty` | `quantity_base` | MAP |
| `time` | `timestamp` | ms → ns |
| `is_buyer_maker` | `side` | derive |
| contract metadata | `quantity_quote` | METADATA |

Observed BTCUSD_PERP relationship:

```text
base_qty = qty × 100 / price
```

Do not hardcode `100`.

Use contract metadata.

---

## OKX-T1 — Spot Trades

Raw:

```text
instrument_name
trade_id
side
price
size
created_time
source
```

| Raw | Canonical | Rule |
|---|---|---|
| `trade_id` | `trade_id` | MAP |
| `created_time` | `timestamp` | ms → ns |
| `side` | `side` | MAP |
| `price` | `price` | MAP |
| `size` | `quantity_base` | MAP |
| `price × size` | `quantity_quote` | DERIVE |
| — | `quantity_contracts` | null |
| `instrument_name` | partition identity | METADATA |

### Extra Raw Information

```text
source
```

Observed:

```text
0 → normal
1 → RPI
```

Current canonical Trade schema does not preserve it.

---

## OKX-T1 — Linear Perpetual Trades

Same raw schema.

| Raw | Canonical | Rule |
|---|---|---|
| `trade_id` | `trade_id` | MAP |
| `created_time` | `timestamp` | ms → ns |
| `side` | `side` | MAP |
| `price` | `price` | MAP |
| `size` | `quantity_contracts` | MAP |
| metadata | `quantity_base` | METADATA |
| metadata + price | `quantity_quote` | METADATA |

Contract conversions require OKX instrument metadata.

---

## OKX-T1 — Inverse Perpetual Trades

Same parser.

| Raw | Canonical | Rule |
|---|---|---|
| `trade_id` | `trade_id` | MAP |
| `created_time` | `timestamp` | ms → ns |
| `side` | `side` | MAP |
| `price` | `price` | MAP |
| `size` | `quantity_contracts` | MAP |
| metadata | `quantity_base` | METADATA |
| metadata | `quantity_quote` | METADATA |

Inverse conversion must use contract specification rather than a hardcoded formula.

---

## OKX-T1 — Option Trades

One option-chain CSV contains many instruments.

Raw schema remains:

```text
instrument_name,trade_id,side,price,size,created_time,source
```

| Raw | Canonical | Rule |
|---|---|---|
| `created_time` | `timestamp` | ms → ns |
| `trade_id` | `trade_id` | MAP |
| `side` | `side` | MAP |
| `price` | `price` | MAP |
| `size` | `quantity_contracts` | MAP |
| `instrument_name` | instrument identity | METADATA |

Raw identity before partitioning:

```text
(instrument_name, trade_id)
```

Do not assume `trade_id` is globally unique across the option chain.

Raw option-chain rows are not globally timestamp ordered.

Normalization must sort when global chronological order is required.

---

## BITGET-T1 — Spot Trades

Raw:

```text
trade_id
timestamp
price
side
volume(quote)
size(base)
```

| Raw | Canonical | Rule |
|---|---|---|
| `trade_id` | `trade_id` | MAP |
| `timestamp` | `timestamp` | ms field → ns |
| `price` | `price` | MAP |
| `side` | `side` | MAP |
| `size(base)` | `quantity_base` | MAP |
| `volume(quote)` | `quantity_quote` | MAP |
| — | `quantity_contracts` | null |

Observed:

```text
volume(quote) = price × size(base)
```

Timestamp storage is milliseconds but effective observed precision is one second.

Multiple numbered ZIPs belong to the same logical archive day.

---

## BITGET-T1 — Linear Perpetual Trades

Same physical and observed quantity representation as Spot.

| Raw | Canonical | Rule |
|---|---|---|
| `trade_id` | `trade_id` | MAP |
| `timestamp` | `timestamp` | ms → ns |
| `price` | `price` | MAP |
| `side` | `side` | MAP |
| `size(base)` | `quantity_base` | MAP |
| `volume(quote)` | `quantity_quote` | MAP |
| — | `quantity_contracts` | null |

Observed:

```text
volume(quote) = price × size(base)
```

Chunk files must be processed in numeric suffix order.

---

## GATE-T1 — Spot Trades

Raw positional schema:

```text
timestamp,trade_id,price,amount,side
```

| Raw | Canonical | Rule |
|---|---|---|
| column 1 | `timestamp` | fractional seconds → ns |
| column 2 | `trade_id` | MAP |
| column 3 | `price` | MAP |
| column 4 | `quantity_base` | MAP |
| column 5 | `side` | decode |
| `price × amount` | `quantity_quote` | DERIVE |
| — | `quantity_contracts` | null |

Side:

```text
1 → sell
2 → buy
```

---

## GATE-T2 — Linear Perpetual Trades

Raw:

```text
timestamp,trade_id,price,signed_size
```

| Raw | Canonical | Rule |
|---|---|---|
| `timestamp` | `timestamp` | fractional seconds → ns |
| `trade_id` | `trade_id` | MAP |
| `price` | `price` | MAP |
| `abs(size)` | `quantity_contracts` | MAP |
| sign(size) | `side` | derive |
| metadata | `quantity_base` | METADATA |
| metadata | `quantity_quote` | METADATA |

Side:

```text
size > 0 → buy
size < 0 → sell
```

---

## GATE-T2 — Inverse Perpetual Trades

Same parser.

```text
size > 0 → buy
size < 0 → sell
abs(size) → quantity_contracts
```

Base/quote conversion requires inverse-contract metadata.

---

# L2

## BYBIT-B1 — Spot / Linear / Inverse

Raw JSONL event:

```text
topic
ts
type
data.s
data.b
data.a
data.u
data.seq
cts
```

Level:

```text
[price, quantity]
```

Mapping:

| Raw | Canonical | Rule |
|---|---|---|
| `ts` | `timestamp` | ms → ns |
| parser event counter | `event_id` | DERIVE |
| `data.b` | `side` | `bid` |
| `data.a` | `side` | `ask` |
| level[0] | `price` | MAP |
| level[1] | `quantity` | MAP |
| — | `order_count` | null |
| `type=snapshot` | `is_snapshot` | true |
| `type=delta` | `is_snapshot` | false |
| snapshot/delta | `operation` | `set` |

Bybit delta quantities represent resulting level quantities.

```text
quantity = 0
→ remove level
```

### Validation Only

```text
data.u
data.seq
cts
```

`u` continuity must be checked before canonical output is accepted.

---

## BYBIT-B2 — Option L2

Event representation is similar to `BYBIT-B1`.

Differences:

```text
orderbook.25
many contract members per ZIP
top-level raw event id
```

Mapping remains:

```text
snapshot → is_snapshot=true, operation=set
delta    → is_snapshot=false, operation=set
```

Raw top-level event `id` may be used for validation/provenance but canonical `event_id` remains deterministic parser-generated grouping.

---

## OKX-B1 — Spot / Linear / Inverse L2

Raw:

```text
instId
action
ts
asks
bids
```

Level:

```text
[price, quantity, order_count]
```

Mapping:

| Raw | Canonical | Rule |
|---|---|---|
| `ts` | `timestamp` | ms → ns |
| parser event counter | `event_id` | DERIVE |
| `asks` | `side` | ask |
| `bids` | `side` | bid |
| level[0] | `price` | MAP |
| level[1] | `quantity` | MAP |
| level[2] | `order_count` | MAP |
| `snapshot` | `is_snapshot` | true |
| `update` | `is_snapshot` | false |
| snapshot/update | `operation` | `set` |

Zero quantity:

```text
quantity = 0
→ remove level
```

No sequence field exists in the historical raw format.

---

## OKX-B2 — Option L2

Same event representation as `OKX-B1`.

Difference:

```text
one TAR.GZ
└── hundreds of independent option-contract members
```

Each member must be normalized independently.

Mapping:

```text
snapshot → true / set
update   → false / set
```

Sparse option snapshots are valid.

Maximum archive depth does not imply every snapshot contains the maximum number of populated levels.

---

## BITGET-B1 — Spot / Linear / Inverse L2

Raw:

```text
ZIP
└── XLSX
    └── timestamp | asks | bids
```

`asks` / `bids` contain JSON arrays:

```text
[[price, quantity], ...]
```

Each spreadsheet row is a complete independent snapshot.

Mapping:

| Raw | Canonical | Rule |
|---|---|---|
| `timestamp` | `timestamp` | seconds → ns |
| workbook row identity | `event_id` | DERIVE |
| asks | `side` | ask |
| bids | `side` | bid |
| level[0] | `price` | MAP |
| level[1] | `quantity` | MAP |
| — | `order_count` | null |
| every row | `is_snapshot` | true |
| every level | `operation` | set |

### Required Preprocessing

Raw XLSX rows are not chronologically ordered.

Normalization must:

```text
parse rows
↓
assign stable raw-row identity
↓
sort by timestamp
↓
preserve separate events when timestamps duplicate
↓
emit canonical levels
```

`event_id` must distinguish duplicate-timestamp snapshots.

No delta reconstruction is performed.

---

## GATE-B1 — Spot L2

Raw:

```text
timestamp
side
action
price
amount
begin_id
merged_count
```

Side:

```text
1 → ask
2 → bid
```

Initial `set` rows form one logical snapshot.

Mapping:

### `set`

```text
is_snapshot = true
operation   = set
quantity    = amount
```

All initial `set` rows sharing the initial snapshot timestamp and sequence ID receive the same `event_id`.

### `make`

```text
is_snapshot = false
operation   = add
quantity    = amount
```

### `take`

```text
is_snapshot = false
operation   = subtract
quantity    = amount
```

### Validation Only

```text
begin_id
merged_count
```

Continuity:

```text
next.begin_id =
    current.begin_id + current.merged_count
```

---

## GATE-B2 — Linear / Inverse Perpetual L2

Raw:

```text
timestamp
action
price
signed_size
begin_id
merged_count
```

Side:

```text
size > 0 → bid
size < 0 → ask
```

Quantity:

```text
abs(size)
```

Mapping:

### `set`

```text
side        = sign(size)
quantity    = abs(size)
is_snapshot = true
operation   = set
```

### `make`

```text
side        = sign(size)
quantity    = abs(size)
is_snapshot = false
operation   = add
```

### `take`

```text
side        = sign(size)
quantity    = abs(size)
is_snapshot = false
operation   = subtract
```

Gate relative update semantics were verified by reconstructing the complete Linear Perpetual hour and comparing it with the following hour's initial snapshot.

Result:

```text
RECONSTRUCTED LEVELS: 42158
NEXT SNAPSHOT LEVELS: 42158

MATCHING:          42158
MISSING:               0
EXTRA:                 0
QUANTITY MISMATCH:     0
```

Therefore:

```text
set  → absolute assignment
make → relative addition
take → relative subtraction
```

### Validation

```text
next.begin_id =
    current.begin_id + current.merged_count
```

---

# Deterministic `event_id`

`event_id` is generated by MarketForge.

Requirements:

```text
unique within one instrument stream
deterministic across repeated normalization
identical for all levels belonging to one logical event
```

Suggested rule:

```text
event_id = monotonically increasing uint64
```

assigned after determining the canonical raw event order.

Examples:

### Bybit / OKX

One JSONL event:

```text
event_id = N
```

for every level contained in that event.

### Bitget

One XLSX snapshot row:

```text
event_id = N
```

for all bid/ask levels in that row.

### Gate

Initial `set` block:

```text
event_id = N
```

for the entire snapshot.

Each subsequent physical `make` / `take` row:

```text
event_id = N + 1
N + 2
...
```

unless later batching rules intentionally preserve raw merged-event grouping.

---

# Partition Identity

The following do not need to be repeated inside every canonical row:

```text
exchange
instrument_type
market_category
symbol
date
```

They are encoded by dataset/partition identity.

Example:

```text
exchange=okx/
instrument_type=perpetual/
market_category=linear/
symbol=BTC-USDT-SWAP/
date=2026-09-01/
```

Partition date must be derived from normalized UTC timestamps.

Never use the raw archive filename date blindly.

---

# Instrument Metadata Required

Normalization requires a separate instrument metadata model for derivative quantity conversion.

Minimum expected fields:

```text
exchange
symbol

instrument_type
market_category

base_asset
quote_asset
settlement_asset

contract_value
contract_multiplier
inverse

expiry
strike
option_type
```

Exact metadata schema should be derived next from the actual conversion requirements.

---

# Fields Not Yet Represented Canonically

The mapping exercise reveals that the minimal Trade schema is **not completely lossless** for several useful source fields.

## Bybit

```text
RPI  ---> important
tickDirection --> derived market feature Include
option IV
index price
mark price
mark IV
trade_seq
```

## Binance

```text
isBestMatch
```

## OKX

```text
source / RPI
```

These must not be silently discarded.

Before parser implementation, decide whether they belong in:

```text
canonical Trade extensions
auxiliary source fields
research-specific datasets
or intentionally discarded metadata
```

---

# Implementation Rule

Every raw parser should conceptually perform:

```text
read raw
↓
validate raw structure
↓
validate sequence/integrity where available
↓
map raw fields
↓
derive deterministic fields
↓
apply instrument metadata where required
↓
normalize timestamps
↓
normalize side
↓
emit canonical records
```

No exchange-specific raw representation should leak beyond the normalization layer.

---

# Current Parser Mapping

## Trades

| Raw Format | Canonical |
|---|---|
| `BYBIT-T1` | Trade |
| `BYBIT-T2` | Trade |
| `BYBIT-T3` | Trade |
| `BINANCE-T1` | Trade |
| `BINANCE-T2` | Trade |
| `BINANCE-T3` | Trade |
| `OKX-T1` | Trade |
| `BITGET-T1` | Trade |
| `GATE-T1` | Trade |
| `GATE-T2` | Trade |

## L2

| Raw Format | Canonical |
|---|---|
| `BYBIT-B1` | L2 |
| `BYBIT-B2` | L2 |
| `OKX-B1` | L2 |
| `OKX-B2` | L2 |
| `BITGET-B1` | L2 |
| `GATE-B1` | L2 |
| `GATE-B2` | L2 |
