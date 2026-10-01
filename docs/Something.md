## MarketForge — Next Development Plan

## Phase 3 — Canonical Schemas

Define common MarketForge schemas for:

- `CanonicalTrade`
- `CanonicalBookEvent`

Decide:

- Timestamp representation
- Price representation
- Quantity semantics
- Trade IDs
- Aggressor side
- Instrument metadata
- Sequence handling
- Snapshot/delta representation

## Phase 4 — Python / Polars Reference Processing

Implement simple reference processors:

```text
raw archive
    ↓
decompress
    ↓
parse
    ↓
normalize
    ↓
validate
    ↓
canonical data
    ↓
Parquet
```

Use Python/Polars first for easy inspection and experimentation.

## Phase 5 — Processing Validation

Validate every transformation:

- Rows read/written
- Timestamp ranges
- Ordering
- Duplicates
- Nulls
- Invalid prices/quantities
- Unknown sides
- Sequence integrity
- Source/output consistency

Add processing manifests for lineage and reproducibility.

## Phase 6 — Rust Processing Engine

Once the reference transformations are correct, implement the high-throughput engine in Rust.

Rust handles:

- Streaming decompression
- Parsing
- Normalization
- Validation
- Parquet writing

Python remains responsible for orchestration and CLI.

## Phase 7 — Canonical Parquet Storage

Create the final partitioned Parquet layout for consumption by MarketForge and `mlfindgen`.

```text
raw archives
      ↓
canonical Parquet
```

Keep raw exchange archives immutable.

## Phase 8 — Merge Engine

Implement:

- Trades-only merging
- Depth-only merging
- Trades + depth alignment
- Cross-exchange merging
- Timestamp alignment

## Phase 9 — Quality & Market-Integrity Analysis

Build research tooling on top of canonical Parquet:

- Digit/Benford tests
- Trade-size clustering
- Volume/count anomalies
- Inter-trade timing
- Entropy
- Price impact
- Quote lifetime/cancellation behavior
- Depth replenishment
- Trade ↔ book consistency
- Cross-exchange divergence
- Lead/lag
- Price discovery
- Wash-trading indicators

## Immediate Next Step

Start with:

```text
tests/fixtures/raw/
        ↓
Raw Format Discovery
```

Inspect and document the actual raw formats **before designing the canonical schemas or writing Rust processing code**.