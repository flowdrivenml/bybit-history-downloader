MarketForge will use **PostgreSQL as its primary operational database** rather than SQLite.

The decision is driven primarily by the planned live architecture. MarketForge is expected to support historical bootstrapping alongside real-time WebSocket ingestion, with several trading or analytical processes potentially running on the same server. The database should therefore provide enough headroom for concurrent access and a rolling recent-data store without requiring an early database migration.

PostgreSQL is **not part of the latency-critical market-data path**. Live normalized events should travel directly from the Rust market-data process to trading software through fast local IPC. PostgreSQL provides persistence and bootstrap history rather than acting as the message transport.

## Database Role

PostgreSQL has two responsibilities.

The first is persistent metadata required to interpret market data:

```text
exchanges
instruments
instrument_specs
instrument_api_raw
raw_formats
normalization_rules
```

This includes instrument identity, contract and quantity semantics, exchange metadata, and the normalization knowledge required to convert exchange-specific data into MarketForge's canonical representation.

The second responsibility will be a **rolling recent market-data store**, initially intended to retain approximately one day of normalized data:

```text
recent trades
recent L2 data
```

The exact physical representation of the live L2 store should be designed when the streaming subsystem is implemented. In particular, MarketForge should not assume that flattened price-level rows used for analytical Parquet storage are also the optimal representation for fast bootstrap and replay.

## Live Data Path

The database must remain outside the critical event-delivery path.

The intended architecture is:

```text
Exchange WebSockets
        ↓
Rust Market Data Process
        ↓
parse
validate
normalize
reconstruct books
        ↓
        ├────────→ fast local IPC ────────→ trading software
        │
        └────────→ PostgreSQL persistence
```

A slow database operation must therefore not delay delivery of market events to trading processes.

The Rust process should decouple persistence from live distribution through queues or channels.

## Bootstrapping

PostgreSQL's recent-data store exists primarily to allow software to recover or initialize state.

A newly started process can:

```text
start
  ↓
load instrument metadata
  ↓
load recent trades / required history
  ↓
load latest L2 snapshot
  ↓
replay subsequent L2 events
  ↓
synchronize with buffered live events
  ↓
continue from live IPC stream
```

This provides continuity without requiring each trading process to maintain its own historical database or reconnect independently to every exchange.

The transition from stored history to the live stream must eventually include explicit synchronization so that events are neither lost nor processed twice during bootstrap.

## Historical Storage

PostgreSQL is not intended to replace Parquet as MarketForge's long-term market-data format.

The storage hierarchy remains:

```text
PostgreSQL
    recent / operational / bootstrap data

Parquet
    permanent normalized historical data
```

Historical research, large scans, merging, feature generation, and integration with `mlfindgen` should continue to use partitioned Parquet.

PostgreSQL should remain bounded rather than becoming the permanent tick archive.

## Rust and Python Responsibilities

Python remains the control and acquisition layer:

```text
instrument discovery
REST metadata APIs
historical acquisition
metadata synchronization
CLI / orchestration
notebooks and research
```

Rust becomes the high-throughput data plane:

```text
historical parsing
decompression
normalization
validation
L2 reconstruction
WebSocket ingestion
live sequence handling
local IPC
recent-data persistence
Parquet processing
```

Keeping WebSocket processing in Rust allows live parsing, validation, book reconstruction, normalization, and publication to remain inside one process without introducing an unnecessary Python-to-Rust boundary.

The reason is not simply raw WebSocket receive speed. A small number of WebSocket connections can also be handled effectively in Python. Rust is preferred because the complete live pipeline includes JSON decoding, sequence validation, mutable L2 state, normalization, batching, persistence, and low-latency IPC.

## Local IPC

Trading software should consume live market data directly from the Rust process rather than querying PostgreSQL for each update.

The initial transport can use a fast local mechanism such as:

```text
Unix domain sockets
+
compact binary canonical messages
```

The protocol should use numeric instrument identifiers rather than repeatedly transmitting exchange and symbol strings.

For example:

```text
instrument_id
timestamp
price
quantity
side
flags
```

Trading processes can resolve `instrument_id` from PostgreSQL during bootstrap.

If profiling later demonstrates that socket IPC is material to latency, shared-memory ring buffers can be considered. They should not be introduced before measurements demonstrate a need.

## TimescaleDB

MarketForge will begin with **plain PostgreSQL**.

TimescaleDB should remain an optional future extension rather than an initial dependency.

It becomes worth considering if the rolling store develops requirements such as:

```text
very large hot time-series tables
automatic time-based retention
time partitioning
many concurrent analytical queries
high sustained ingestion rates
```

Because TimescaleDB extends PostgreSQL, adopting it later does not require abandoning the PostgreSQL architecture.

The live L2 representation should be understood and benchmarked before making that decision.

## Immediate Implementation Scope

The first PostgreSQL implementation should remain narrow.

Implement:

```text
exchanges
instruments
instrument_specs
instrument_api_raw
```

These support the first real workflow:

```text
Bybit API
    ↓
Python metadata provider
    ↓
canonical instrument metadata
    ↓
PostgreSQL
```

After instrument metadata ingestion works, add:

```text
raw_formats
normalization_rules
```

from MarketForge's version-controlled normalization definitions.

The rolling live tables should be added only when the Rust streaming subsystem is implemented and its bootstrap requirements are concrete.

## Final Architecture

```text
                         MarketForge

                    ┌──── CONTROL ────┐
                    │                 │
                 Python          PostgreSQL
                    │                 │
                    │          metadata + recent
                    │          bootstrap history
                    │
                    └────────┬────────┘
                             │
                             ▼
                    Rust Market Data
                    ├── historical parsing
                    ├── WebSockets
                    ├── normalization
                    ├── validation
                    ├── L2 reconstruction
                    └── persistence
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
            Fast local IPC           Parquet
                  │                 long-term
                  ▼                  history
           Trading software
```

The central rule is:

> **PostgreSQL provides state and history; Rust provides the live data path; Parquet provides permanent history.**

This keeps live delivery close to the trading processes while giving MarketForge a robust bootstrap and metadata layer with room to grow.