
## Phase 8 — CLI

Implement:

```text
src/marketforge/cli.py
```

The current package entry point already expects:

```text
marketforge = marketforge.cli:main
```

so the CLI must eventually provide `main()`.

### 8.1 First commands

Start with:

```text
marketforge instruments
marketforge availability
marketforge plan
marketforge download
```

### 8.2 `instruments`

Example:

```bash
marketforge instruments \
    --exchange bybit \
    --type perpetual \
    --category linear \
    --data trades
```

### 8.3 `availability`

Example:

```bash
marketforge availability \
    --exchange okx \
    --symbol BTC-USDT-SWAP \
    --type perpetual \
    --category linear \
    --data trades \
    --start 2026-09-01 \
    --end 2026-09-10
```

### 8.4 `plan`

Print:

```text
Exchange
Instrument
Dataset
Requested range
Remote archives
Files requiring download
Files reusable
Known bytes
Unknown-size files
```

### 8.5 `download`

Run the acquisition plan and show progress.

Do not duplicate downloader logic in the CLI.

### Phase 8 completion criterion

The same operation behaves consistently from:

```text
Python
Jupyter
CLI
```

---

## Phase 9 — First Complete Raw Acquisition Workflow

Before moving to normalization, prove one complete raw acquisition workflow.

Use a small Bybit trade example first.

Pipeline:

```text
AcquisitionRequest
        ↓
MarketForgeClient.plan()
        ↓
BybitSource.discover_files()
        ↓
AcquisitionPlan
        ↓
download.py
        ↓
temporary file
        ↓
verified raw archive
        ↓
raw acquisition record
```

Then rerun the identical request:

```text
same request
    ↓
plan
    ↓
existing verified archive
    ↓
REUSE
    ↓
zero unnecessary download
```

Then test a partially overlapping request:

```text
existing files
+
new files
    ↓
reuse old
download new
```

### Phase 9 completion criterion

MarketForge has a trustworthy reusable raw-data acquisition pipeline.

This is the point where acquisition can be considered operational.

---

## Phase 10 — Trade Normalization

After raw acquisition is reliable, begin processing.

Do not start with every exchange.

Start with one small trade archive.

Suggested first source:

```text
Bybit Spot BTCUSDT trades
```

### 10.1 Inspect the raw schema

Determine explicitly:

```text
timestamp field
timestamp unit
timestamp precision
price
quantity
quantity units
trade ID
side/aggressor semantics
ordering
header behavior
missing values
numeric precision
```

### 10.2 Define canonical trade schema

Initial concepts:

```text
exchange
instrument_type
market_category
native_symbol
timestamp
price
quantity
side/aggressor if verified
native_trade_id if available
source_file
source_row
```

Preserve original precision and semantics.

### 10.3 Python reference implementation

Implement first with:

```text
Python + Polars
```

The goal is understanding and verifying behavior.

Do not make Rust necessary for basic schema research.

### 10.4 Technical validation

Check:

```text
required fields
timestamp plausibility
numeric conversion
instrument consistency
ordering
malformed rows
duplicate evidence
```

Do not automatically delete records merely because:

```text
timestamp + price + quantity
```

are equal.

### 10.5 Parquet output

Write:

```text
data/datasets/<dataset_name>/
├── manifest.json
├── processing.json
├── quality.json
└── data/
    └── *.parquet
```

This matches the current storage plan. :chatgpt-content-reference{index="4"}

### Phase 10 completion criterion

One real raw trade archive becomes reproducible canonical Parquet with provenance and technical findings.

---

## Phase 11 — Rust Engine Boundary

Only after the normalization behavior is understood should the production Rust engine be introduced.

Use the intended standalone-binary architecture:

```text
Python
    ↓
subprocess
    ↓
Rust binary
    ↓
Parquet / result metadata
```

No event-by-event Python/Rust calls.

### 11.1 Existing Python locations

Use:

```text
src/marketforge/engine/
├── commands.py
├── results.py
└── runner.py
```

### 11.2 Rust first operations

Implement only what has verified semantics:

```text
decompress
parse
normalize trades
validate
write Parquet
```

### 11.3 Command contract

Example concept:

```text
marketforge-engine normalize
    --exchange bybit
    --data-type trades
    --input ...
    --output ...
    --config ...
```

### 11.4 Result contract

Rust should return structured execution metadata:

```text
success
rows read
rows written
rows rejected
timestamp min/max
output files
findings
```

### Phase 11 completion criterion

Python and Rust produce equivalent normalized output for a controlled fixture.

---

## Phase 12 — Multi-Exchange Trades

After one trade parser works:

```text
Bybit
    ↓
canonical trades
```

add another source:

```text
Binance
    ↓
canonical trades
```

Then:

```text
OKX
Bitget
Gate.io
```

### 12.1 Same schema, different provenance

Every normalized row must retain:

```text
exchange
native symbol
market category
instrument type
source archive
```

### 12.2 Trades-only merge first

Build:

```text
exchange A trades ─┐
exchange B trades ─┼─→ deterministic chronological merge
exchange C trades ─┘
```

Specify equal-timestamp ordering explicitly.

### 12.3 Do not merge incompatible instruments automatically

Do not treat:

```text
BTC spot
BTC linear perpetual
BTC inverse future
BTC option
```

as equivalent merely because they contain BTC.

### Phase 12 completion criterion

Two or more exchanges can generate one deterministic trades-only research dataset while preserving venue identity.

---

## Phase 13 — Order-Book Reconstruction

Only after trades are stable should order-book state become the focus.

Start with one source.

### 13.1 Synthetic reference tests

Create known sequences:

```text
snapshot
    ↓
insert level
    ↓
change quantity
    ↓
delete level
    ↓
gap
    ↓
untrusted state
    ↓
new snapshot
    ↓
trusted state restored
```

### 13.2 Preserve message boundaries

Apply an entire update message before exposing derived state.

Do not calculate metrics halfway through one multi-level message.

### 13.3 Sequence rules

Use only source-specific continuity guarantees.

Do not assume every sequence field increments by exactly one.

### 13.4 Initialization

A requested interval may require data before `start` to establish valid state.

Support:

```text
earlier snapshot / checkpoint
        ↓
reconstruct state
        ↓
begin requested output
```

### 13.5 Rust

Once Python/reference behavior is verified, implement high-volume reconstruction in Rust.

### Phase 13 completion criterion

Book-state failures are detectable, explainable, and recover correctly after valid resynchronization.

---

## Phase 14 — Quality and Integrity

Technical validation begins during normalization.

This phase expands the structured quality layer.

Keep separate:

```text
TECHNICAL QUALITY
vs
MARKET BEHAVIOUR / INTEGRITY ANALYSIS
```

The project documentation explicitly requires that separation. :chatgpt-content-reference{index="5"}

### 14.1 Technical checks

Include:

```text
archive integrity
successful decompression
parser completion
required fields
numeric validity
timestamp precision
instrument consistency
exact duplicate evidence
conflicting records
ordering
sequence continuity
snapshot/delta validity
book reconstruction validity
invalid intervals
```

### 14.2 Findings

Prefer explicit findings:

```text
PASS
FAIL
NOT_EVALUABLE
VALID_WITH_EXCLUDED_INTERVALS
REVIEW
```

Do not collapse everything into one vague score.

### 14.3 Audit first

Default:

```text
AUDIT
  ↓
REPORT
  ↓
OPTIONAL FILTER POLICY
  ↓
MATERIALIZED DATASET
```

Do not silently delete suspicious-but-technically-valid observations.

### Phase 14 completion criterion

Every exclusion or warning can be traced to a specific finding, rule, detector version, source file, and interval.

---

## Phase 15 — Research Layer

Only build research indicators after the required validated data exists.

### Trade-only indicators

Can begin after trade normalization:

```text
trade counts
volume
trade-size roundness
digit distributions
trade-size tails
transaction-count vs volume
inter-trade timing
periodicity
entropy
volume-volatility relationships
signed-flow statistics
```

### Trade + trusted order book

Add:

```text
spread
depth
visible liquidity
price impact
depth consumption
replenishment
resiliency
trade-book consistency
```

### Cross-exchange datasets

Add:

```text
price divergence
volume divergence
lead/lag
cross-correlation
information share
component share
incremental venue information
price discovery
```

Treat unusual behavior as evidence requiring review, not proof of manipulation. :chatgpt-content-reference{index="6"}

### Phase 15 completion criterion

Each research result records:

```text
required input
method
window
sample requirements
reference/baseline
version
limitations
applicability
```

---

## Definition of Done

### Acquisition source layer

```text
[ ] Source interface stable
[ ] Bybit adapter verified
[ ] Binance adapter verified
[ ] OKX adapter verified
[ ] Bitget adapter verified
[ ] Gate.io adapter verified
[ ] deterministic offline fixtures exist
[ ] live smoke tests remain small
```

### HTTP

```text
[ ] request throttling
[ ] retry policy
[ ] exponential/fixed backoff
[ ] 429 handling
[ ] transient 5xx handling
[ ] timeout handling
[ ] structured expected-status support
[ ] tests for retry exhaustion
```

### Planning

```text
[ ] AcquisitionRequest
[ ] PlannedDownload
[ ] AcquisitionPlan
[ ] deterministic raw paths
[ ] reuse detection
[ ] known/unknown byte summary
```

### Downloading

```text
[ ] streaming
[ ] .part temporary files
[ ] atomic publication
[ ] SHA-256
[ ] actual byte count
[ ] no silent overwrite
[ ] interrupted transfer handling
[ ] verified-file reuse
[ ] sequential batch download
```

### Raw storage

```text
[ ] data/raw/
[ ] immutable archives
[ ] collision-safe layout
[ ] native filenames preserved
[ ] acquisition records
```

### Public interface

```text
[ ] MarketForgeClient
[ ] instruments()
[ ] availability()
[ ] plan()
[ ] download()
[ ] CLI equivalent
```

### Processing

```text
[ ] one canonical trade schema
[ ] one exchange normalized correctly
[ ] technical findings
[ ] Parquet output
[ ] provenance
[ ] second exchange normalized
[ ] trades-only merge
```

### Rust

```text
[ ] standalone binary
[ ] Python runner
[ ] structured command/result contract
[ ] trade normalization
[ ] golden tests
[ ] order-book reconstruction
[ ] merging when justified
```

### Quality / research

```text
[ ] technical quality separate from behavioural analysis
[ ] explicit findings
[ ] invalid intervals preserved
[ ] filter policies reproducible
[ ] trade-only indicators
[ ] book-dependent indicators
[ ] cross-exchange price-discovery analysis
```

---

## Immediate Next Work

Do these next, in this order:

```text
1. Fix and regression-test remaining source/HTTP correctness issues
2. Build proper offline source fixtures
3. Implement acquisition request/plan/result models
4. Implement storage/paths.py
5. Implement planning.py
6. Implement download.py
7. Implement raw acquisition manifest/state
8. Implement MarketForgeClient
9. Implement minimal CLI
10. Prove one complete raw acquisition workflow
11. Begin one trade normalization path
```

The next major milestone is:

```text
User request
    ↓
Source discovery
    ↓
Acquisition plan
    ↓
Safe download
    ↓
Immutable raw archive
    ↓
Hash + acquisition record
    ↓
Repeat request
    ↓
Reuse verified archive
```

Once that works reliably, move to normalization.

> **Do not start Rust processing, merging, or research indicators until raw acquisition is restartable, verifiable, and reproducible.**