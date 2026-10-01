MarketForge uses PostgreSQL for persistent metadata and a short rolling window of live market data used for bootstrap, recovery, and recent-history access.

PostgreSQL is **not** part of the latency-critical live delivery path. Live events are distributed directly from the Rust market-data process through local IPC.

## Persistent Metadata

```text
catalog
├── exchanges
├── instruments
├── instrument_specs
├── instrument_api_raw
├── raw_formats
└── normalization_rules
```

This data is persistent and is not subject to rolling retention.

It defines:

```text
exchange identity
instrument identity
quantity / contract semantics
raw exchange metadata
raw data formats
normalization mappings
```

## Rolling Live Data

Keep approximately one day of recent normalized market data:

```text
live
├── trades
├── l2_snapshots
└── l2_updates
```

### `live.trades`

One normalized trade per row.

```text
timestamp
instrument_id
trade_id
side
price
quantities
is_rpi
```

### `live.l2_snapshots`

Periodic complete reconstructed books.

```text
timestamp
instrument_id
snapshot_id
depth
payload
```

The Rust live process maintains the current book in memory and periodically persists a complete snapshot.

Initial target:

```text
snapshot interval ≈ 30 minutes
```

The snapshot contains the complete depth represented by the subscribed stream.

One complete snapshot should be stored as one compact payload rather than thousands of individual SQL rows.

### `live.l2_updates`

Incremental L2 changes occurring between snapshots.

```text
timestamp
instrument_id
event_id
payload
```

One logical L2 update should be stored as one row with a compact payload.

Bootstrap:

```text
latest complete snapshot
        ↓
replay subsequent updates
        ↓
current reconstructed book
        ↓
handoff to live IPC
```

## Retention

Target live-data retention:

```text
trades      ≈ 24 hours
L2 updates  ≈ 24 hours
L2 snapshots > 24 hours
```

Snapshots may be retained longer because they are small and provide reconstruction checkpoints.

Long-term normalized history remains in partitioned Parquet.

```text
PostgreSQL
    → metadata
    → recent/bootstrap data

Parquet
    → permanent historical data

Rust IPC
    → live low-latency data
```