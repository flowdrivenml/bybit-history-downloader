## Historical Tick-Level Microstructure Data

MarketForge should initially focus only on **free historical event-level / high-resolution microstructure data** that can actually be acquired from each source.

## Quick Navigation

- [Core Data](#core-data)
- [Initial Exchange Coverage](#initial-exchange-coverage)
- [What Does Not Belong Here](#what-does-not-belong-here)
- [MarketForge Rule](#marketforge-rule)

## Core Data

The primary historical microstructure datasets are:

```text
TRADES
Individual/tick-level executions
    ↓
timestamp
price
quantity
side/aggressor where available
trade/event ID where available


ORDER BOOK
High-resolution L2 market events
    ↓
snapshots
incremental updates
bids / asks
price levels
quantities
sequence IDs where available
```

These two datasets provide most of the raw information required for later MarketForge-derived research:

```text
trades + L2
    ↓
spread
midprice
depth
imbalance
order flow
liquidity consumption
replenishment
price impact
book resiliency
trade/book consistency
cross-exchange lead/lag
price discovery
```

## Initial Exchange Coverage

| Exchange | Tick Trades | Historical L2 / Depth | Main Value |
|---|:---:|:---:|---|
| **Bybit** | ✅ | ✅ | Trades + detailed order-book history |
| **Binance** | ✅ | ⚠️ | Excellent trade archives; historical true L2 requires more investigation |
| **OKX** | ✅ | ✅ | Tick trades + downloadable high-resolution L2 |
| **Gate.io** | ✅ | ✅ | Tick trades + market depth + depth snapshots |
| **Bitget** | ✅ | ✅* | Trades + depth candidate; exact historical format/coverage must be verified |
| **Deribit** | ✅ | ⚠️ | Particularly valuable for derivatives/options trades; historical L2 availability needs verification |

Legend:

```text
✅  Verified/strong historical source
⚠️  Historical capability needs additional investigation
*   Do not mark production-supported until tested against actual archives
```

For example, OKX explicitly provides downloadable **tick-level trading history** and **high-resolution L2 order-book data**. :chatgpt-content-reference{index="0"}

Gate explicitly provides historical **filled orders, market depth, and depth snapshots**, including deterministic download paths. :chatgpt-content-reference{index="1"}

## What Does Not Belong Here

Do **not** classify a dataset as MarketForge historical microstructure data merely because an exchange exposes it through its current REST/WebSocket API.

For example:

```text
current open interest API       ≠ historical tick OI dataset

current mark price              ≠ historical tick mark-price archive

current liquidation stream      ≠ historical liquidation dataset

current WebSocket order book    ≠ historical L2 archive
```

Likewise, lower-frequency datasets are not the initial focus:

```text
OHLC candles
daily statistics
hourly open interest
periodic long/short ratios
funding observations
borrowing rates
daily volume statistics
```

They may be useful later, but they are **not the core event-level microstructure dataset**.

## MarketForge Rule

A source capability gets added only when we establish:

```text
FREE
    +
HISTORICAL
    +
ACTUALLY ACCESSIBLE
    +
HIGH-RESOLUTION / EVENT-LEVEL
    +
SEMANTICS WE CAN VERIFY
```

Therefore the initial MarketForge data model can stay deliberately small:

```text
MarketForge
│
├── trades
│   └── tick-level executions
│
└── orderbook
    ├── snapshots
    └── incremental / high-resolution depth
```

Everything else should be added **only when we find a genuinely useful free historical high-resolution source for it**.

The goal is not to support the largest number of dataset names.

> **The goal is to collect the richest freely available historical event-level market data that can actually support serious microstructure research.**