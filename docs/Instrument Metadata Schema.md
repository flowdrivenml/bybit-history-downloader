## Goal

Instrument metadata provides the information required to interpret canonical Trade and L2 quantities without embedding exchange-specific contract logic inside normalized market-data rows.

It should support:

```text
Spot
Linear derivatives
Inverse derivatives
Futures
Perpetuals
Options
```

and enable:

```text
quantity_contracts
        ↓
instrument metadata
        ↓
quantity_base
quantity_quote
```

---

## Canonical Instrument Metadata

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

| Field | Type | Meaning |
|---|---|---|
| `exchange` | enum | Source exchange |
| `symbol` | string | Exchange-native instrument identifier |
| `instrument_type` | enum | `spot`, `perpetual`, `future`, `option` |
| `market_category` | enum | `spot`, `linear`, `inverse`, `option` |
| `base_asset` | string | Base / underlying asset |
| `quote_asset` | string | Price quote asset |
| `settlement_asset` | string? | Settlement / margin asset |
| `contract_value` | decimal? | Economic value represented by one contract |
| `contract_value_asset` | string? | Asset/unit in which `contract_value` is expressed |
| `expiry` | timestamp? | Expiration time for dated instruments |
| `strike` | decimal? | Option strike |
| `option_type` | enum? | `call` / `put` |

Spot instruments leave contract and option fields null.

---

# Why `contract_value_asset` Matters

A numeric contract multiplier alone is ambiguous.

For example:

```text
1 contract = 0.001 BTC
```

and:

```text
1 contract = 100 USD
```

require completely different conversions.

Therefore store both:

```text
contract_value
contract_value_asset
```

Example:

```text
contract_value       = 0.001
contract_value_asset = BTC
```

or:

```text
contract_value       = 100
contract_value_asset = USD
```

This allows normalization to determine whether contract value represents base or quote exposure.

---

# Quantity Conversion

Given:

```text
C = quantity_contracts
V = contract_value
P = execution price
```

## Contract Value Expressed in Base Asset

Example:

```text
1 contract = 0.001 BTC
```

Then:

```text
quantity_base =
    C × V

quantity_quote =
    quantity_base × P
```

Conceptually:

```text
contracts
    ↓ × contract_value
base quantity
    ↓ × price
quote quantity
```

---

## Contract Value Expressed in Quote Asset

Example:

```text
1 contract = 100 USD
```

Then:

```text
quantity_quote =
    C × V

quantity_base =
    quantity_quote / P
```

Conceptually:

```text
contracts
    ↓ × contract_value
quote quantity
    ↓ ÷ price
base quantity
```

This naturally handles many inverse contracts.

---

# Spot

Example:

```text
BTC-USDT
```

Metadata:

```text
exchange          = ...
symbol            = BTC-USDT
instrument_type   = spot
market_category   = spot

base_asset        = BTC
quote_asset       = USDT
settlement_asset  = null

contract_value       = null
contract_value_asset = null

expiry      = null
strike      = null
option_type = null
```

Trade quantities usually arrive directly:

```text
quantity_base
quantity_quote
```

No contract conversion is required.

---

# Linear Perpetual

Example:

```text
BTC-USDT-SWAP
```

Metadata conceptually:

```text
instrument_type  = perpetual
market_category  = linear

base_asset       = BTC
quote_asset      = USDT
settlement_asset = USDT
```

If one contract represents a fixed amount of BTC:

```text
contract_value       = <value>
contract_value_asset = BTC
```

Then:

```text
contracts
    ↓
quantity_base
    ↓
quantity_quote
```

No exchange-specific formula is needed after metadata has been normalized.

---

# Inverse Perpetual

Example:

```text
BTC-USD-SWAP
```

Metadata:

```text
instrument_type  = perpetual
market_category  = inverse

base_asset       = BTC
quote_asset      = USD
settlement_asset = BTC
```

If one contract represents a fixed USD amount:

```text
contract_value       = <value>
contract_value_asset = USD
```

Then:

```text
quantity_quote =
    quantity_contracts × contract_value

quantity_base =
    quantity_quote / price
```

Again, the conversion follows from metadata rather than:

```text
if exchange == X:
    ...
```

---

# Futures

Dated futures use the same contract-value model as perpetuals.

Additional metadata:

```text
expiry
```

Example:

```text
instrument_type = future
expiry          = ...
```

Linear/inverse interpretation still comes from:

```text
market_category
contract_value
contract_value_asset
```

No separate quantity model is required for futures.

---

# Options

Options require:

```text
base_asset
quote_asset
settlement_asset

contract_value
contract_value_asset

expiry
strike
option_type
```

Example:

```text
symbol          = BTC-USD-260925-80000-C
instrument_type = option
market_category = option

base_asset       = BTC
quote_asset      = USD
settlement_asset = ...

contract_value       = ...
contract_value_asset = BTC

expiry      = ...
strike      = 80000
option_type = call
```

Canonical Trade:

```text
quantity_contracts
```

can then be converted where appropriate using the same contract-value mechanism.

Option-specific market statistics such as:

```text
implied volatility
mark IV
mark price
index price
```

do not belong in instrument metadata because they vary through time.

---

# Conversion Algorithm

Normalization should use one generic conversion function.

Conceptually:

```text
if quantity_base already exists:
    preserve it

if quantity_quote already exists:
    preserve it

if quantity_contracts exists:
    inspect contract_value_asset
```

Then:

```text
if contract_value_asset == base_asset:

    quantity_base =
        quantity_contracts × contract_value

    quantity_quote =
        quantity_base × price
```

or:

```text
if contract_value_asset == quote_asset:

    quantity_quote =
        quantity_contracts × contract_value

    quantity_base =
        quantity_quote / price
```

If neither relationship is known:

```text
preserve quantity_contracts
leave derived quantities null
```

Never guess.

---

# Important Rule

Raw quantities supplied directly by the exchange take precedence over derived quantities.

Example:

```text
Bitget:

size(base)
volume(quote)
```

Both should be preserved directly.

Do not overwrite them merely because metadata allows recomputation.

Derived values can instead be validated against the supplied values.

---

# Instrument Metadata vs Partition Metadata

Instrument metadata is logically separate from tick rows.

Example partition:

```text
exchange=okx/
instrument_type=perpetual/
market_category=linear/
symbol=BTC-USDT-SWAP/
date=2026-09-01/
```

Associated instrument metadata:

```text
base_asset
quote_asset
settlement_asset

contract_value
contract_value_asset

expiry
strike
option_type
```

Therefore these values do not need to be repeated millions of times inside every Trade or L2 row.

---

# Precision

Instrument metadata should use decimal-safe representations.

Recommended conceptual types:

```text
contract_value → decimal
strike         → decimal
```

Do not normalize contract specifications through binary floating point when exact decimal representation is available.

The same consideration should later be applied to canonical:

```text
price
quantity
```

when designing the physical Parquet types.

---

# Minimal Schema

Final minimal metadata interface:

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

No additional exchange API fields should be added unless they are required for:

```text
normalization
validation
instrument identity
```

---

# Valuable Extra Trade Fields

The raw-format mapping identified several useful fields not represented by the minimal canonical Trade schema.

They should not be silently discarded.

## Observed Extras

### Bybit

```text
RPI
tickDirection

option:
iv
index_price
mark_price
mark_iv
trade_seq
```

### Binance

```text
isBestMatch
```

### OKX

```text
source
```

where observed:

```text
0 → normal
1 → RPI
```

---

# Treatment of Extra Fields

Do not enlarge the core Trade schema with every exchange-specific field.

Instead divide extras into three classes.

## 1. Universal Market Concepts

If the same concept exists across multiple exchanges and is useful for research, promote it to the canonical schema.

Example candidate:

```text
is_rpi
```

Observed in:

```text
Bybit
OKX
```

Potential canonical field:

```text
is_rpi: bool?
```

This is a genuine market concept rather than merely an exchange implementation detail.

---

## 2. Dataset-Specific Research Fields

Fields that are valuable but only meaningful for a specific instrument class should live in an optional extension dataset/schema.

The strongest example is options:

```text
iv
mark_iv
mark_price
index_price
```

Instead of polluting every Spot/Perpetual Trade row with null columns, represent option-specific trade information separately.

Conceptually:

```text
Trade
├── core trade fields
└── OptionTradeExtra
```

linked by:

```text
trade_id / event identity
```

Possible Option Trade extension:

```text
trade_id
iv
mark_iv
mark_price
index_price
```

This can be implemented later if those fields are required by research.

---

## 3. Validation / Provenance Fields

Fields useful primarily for validating the raw stream should remain internal to parsing/validation.

Examples:

```text
Bybit trade_seq
Bybit book u
Bybit book seq

Gate begin_id
Gate merged_count
```

These should normally not appear in canonical market-data Parquet after successful validation.

---

# Proposed Small Core Extension

One field is worth considering for canonical Trade:

```text
is_rpi
```

Revised candidate:

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

with:

```text
is_rpi = true / false / null
```

Mapping:

```text
Bybit RPI → is_rpi
OKX source=1 → true
OKX source=0 → false
Other exchanges → null
```

This preserves a cross-exchange microstructure concept that may be useful later for MarketForge's market-integrity research.

---

# Do Not Add to Core Trade

For now, keep these outside the universal Trade schema:

```text
tickDirection
isBestMatch
trade_seq
iv
mark_iv
mark_price
index_price
```

Reason:

```text
not universally available
or
instrument-specific
or
primarily validation/provenance information
```

They can be preserved in source-specific/extension datasets if needed later.

---

# Recommended Final Core Schemas

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

These three interfaces are sufficient to begin implementing normalization without carrying exchange-specific representations throughout the rest of MarketForge.