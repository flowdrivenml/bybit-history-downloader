## Testing Strategy

MarketForge should use several complementary testing layers. The important distinction is **what each layer is trying to prove**.

## Quick Navigation

- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [End-to-End Tests](#end-to-end-tests)
- [Fixtures and Golden Data](#fixtures-and-golden-data)
- [Live Tests](#live-tests)
- [Recommended Test Structure](#recommended-test-structure)
- [Core Mental Model](#core-mental-model)

## Unit Tests

Unit tests verify a **small piece of logic in isolation**.

Typical targets:

- URL and filename construction
- Date/range planning
- Symbol and instrument mapping
- Source capability declarations
- Timestamp conversion
- Individual validation rules
- Statistical functions
- Manifest/path logic

They should be **fast, deterministic, and normally require no internet**.

> **Question:** Does this individual function or component work correctly?

Example:

```text
build_trade_url()
        ↓
expected URL
```

Unit tests should be run constantly during development.

## Integration Tests

Integration tests verify whether **multiple real components work correctly together**.

Examples:

```text
discovery
    ↓
planner
    ↓
downloader
```

Or:

```text
Python
    ↓
Rust subprocess
    ↓
Parquet
    ↓
Python reads result
```

For the Rust engine:

```text
decompress
    ↓
parse
    ↓
normalize
    ↓
validate
    ↓
write Parquet
```

And eventually:

```text
Bybit stream ───┐
Binance stream ─┼─→ Rust merge → Parquet
OKX stream ─────┘
```

Integration tests are especially important around **boundaries between subsystems**.

> **Question:** Do these components work correctly when connected?

## End-to-End Tests

End-to-end tests verify a **complete MarketForge workflow**.

For example:

```text
discover
    ↓
download
    ↓
verify
    ↓
normalize
    ↓
validate
    ↓
merge
    ↓
Parquet
    ↓
quality analysis
```

E2E tests should normally use small controlled datasets rather than huge real downloads.

They verify that all major parts of MarketForge cooperate correctly from input to final output.

> **Question:** Does MarketForge as a whole produce the expected final result?

## Fixtures and Golden Data

A **fixture is controlled test input**, not a separate testing level.

Fixtures can be used by unit, integration, and E2E tests.

Example:

```text
tests/fixtures/
├── bybit/
│   ├── valid_trades.csv.gz
│   ├── malformed_trades.csv.gz
│   ├── duplicate_trades.csv.gz
│   └── orderbook_gap.jsonl.gz
│
├── binance/
│   └── ...
│
└── synthetic/
    ├── merge_equal_timestamps/
    └── orderbook_reconstruction/
```

The important property is that the fixture has **known characteristics**.

Example:

```text
Input:
    20 trade records
    1 malformed record

Expected:
    19 accepted
    1 rejected
    finding = MALFORMED_RECORD
```

Fixtures are particularly important for the Rust engine:

- Parsing
- Normalization
- Chronological merging
- Equal-timestamp ordering
- Sequence validation
- Order-book reconstruction
- Snapshot/delta handling
- Corrupt data
- Duplicate handling
- Partition boundaries
- Different timestamp precisions

### Golden Tests

A golden test goes one step further: the expected output is known precisely.

For example:

```text
BYBIT
100 ns    A
400 ns    D

BINANCE
200 ns    B
300 ns    C

OKX
150 ns    X
500 ns    E
```

Expected merged output:

```text
100    BYBIT      A
150    OKX        X
200    BINANCE    B
300    BINANCE    C
400    BYBIT      D
500    OKX        E
```

The Rust merger must reproduce that ordering exactly.

Order-book reconstruction should work similarly:

```text
snapshot
    ↓
delta
    ↓
delta
    ↓
delta
    ↓
expected final book
```

> **Question:** Given known input, do we produce exactly the expected behavior or output?

## Live Tests

Live tests contact the **real external data source over the internet**.

For MarketForge, their main purpose is:

> **Does our source adapter still work with the exchange today?**

Examples:

```text
MarketForge
    ↓
Internet
    ↓
Bybit
    ↓
actual current response
    ↓
MarketForge parser
```

A live test might check:

- Can the source be reached?
- Can instruments be discovered?
- Does a stable instrument such as `BTCUSDT` exist?
- Can historical assets be discovered?
- Is a known historical asset accessible?
- Does the returned format still match what the adapter expects?
- Have API fields or response structures changed?

This is different from an offline fixture test.

### Offline Fixture Test

```text
saved Bybit response
        ↓
Bybit parser
        ↓
expected result
```

This proves:

> **Our code understands the response format we tested against.**

### Live Test

```text
MarketForge
    ↓
real Bybit service
    ↓
current response
    ↓
adapter
```

This proves:

> **Our adapter still works against the real service today.**

This distinction is critical because an exchange can change its API, filenames, directories, schemas, or response structure while all offline tests continue to pass.

Live tests should remain **small and inexpensive**.

Do not download 50 GB of order-book data just to determine whether a source still works.

Where possible, test discovery, metadata, headers, small responses, or a known small historical asset.

Live tests should also be optional:

```bash
pytest
```

Runs normal offline tests.

```bash
pytest -m live
```

Runs tests against real external sources.

Eventually, CI can run ordinary tests on every commit while running live source smoke tests periodically.

## Recommended Test Structure

Python:

```text
tests/
├── unit/
│   ├── acquisition/
│   ├── sources/
│   ├── storage/
│   └── quality/
│
├── integration/
│   ├── test_download_pipeline.py
│   ├── test_engine_normalize.py
│   ├── test_engine_merge.py
│   └── test_manifest_pipeline.py
│
├── e2e/
│   └── test_small_pipeline.py
│
├── live/
│   ├── test_bybit.py
│   ├── test_binance.py
│   ├── test_okx.py
│   ├── test_gateio.py
│   ├── test_bitget.py
│   └── test_deribit.py
│
└── fixtures/
    ├── bybit/
    ├── binance/
    ├── okx/
    └── synthetic/
```

Rust:

```text
engine/
├── src/
│   └── ...
│
└── tests/
    ├── parsing.rs
    ├── normalization.rs
    ├── validation.rs
    ├── orderbook.rs
    └── merging.rs
```

Testing infrastructure should grow alongside MarketForge. There is no need to build every category before the corresponding functionality exists.

For the initial Python acquisition work, the priority is:

```text
unit tests
    +
saved API-response fixtures
    +
small live source tests
```

When the Rust processing engine arrives, fixtures, golden tests, integration tests, and E2E tests become substantially more important.

## Core Mental Model

```text
UNIT
"Does this small thing work?"

INTEGRATION
"Do these pieces work together?"

E2E
"Does MarketForge as a whole work?"

LIVE
"Does MarketForge still work with the real external source today?"

FIXTURE
"Controlled input/setup used to make tests reproducible."

GOLDEN TEST
"Given this exact input, do we produce the known correct output?"
```

For MarketForge specifically:

> **Python acquisition benefits heavily from unit + live tests.**

> **Rust processing benefits heavily from fixtures + golden + integration tests.**

> **The complete pipeline is protected by E2E tests.**