## Project Structure and Implementation Plan

Structure the project as **one library with a reliable data pipeline at its center, and research modules built on top of that pipeline**.

The most important decision is the implementation order:

> **One exchange’s trades end to end → a second exchange → trade merging → order-book reconstruction → combined event datasets → market-integrity and venue analysis.**

Do not start by implementing six exchanges, every indicator, and the complete Rust engine simultaneously. Build something small that already produces trustworthy data, then extend it without changing its foundations.

The notebook already establishes the right foundations: independently usable pipeline stages, preserved raw data, normalized and merged Parquet, and a separation between technical validation and suspicious-activity analysis. Keep those commitments. :chatgpt-content-reference{index="0"} :chatgpt-content-reference{index="1"} :chatgpt-content-reference{index="2"}

## Changes From the Current Repository

There are three important differences between the old implementation and the new direction.

| What is in the uploaded snapshot | What that means for the rewrite |
|---|---|
| The new `src/bybit_history/` contains empty implementation files, including `cleint.py`; its `__init__.py` and CLI are also empty. Packaging still targets this directory. | Restore a working package baseline before adding features. Do not treat the new directory tree as an implemented architecture. |
| The notebook records a successful direct HTTP symbol-discovery response, after earlier requests returned 403. | Investigate direct data access first. Keep Playwright for exploration or a source-specific fallback—not as the foundation of the library. |
| The old download implementation extracts archives and deletes the originals. | Separate acquisition from extraction and normalization. The new pipeline should preserve raw source files. |

These observations come from the empty modules and packaging configuration, the saved notebook responses, and the old archive-handling code. The successful notebook request is evidence from that experiment, not a guarantee that the endpoint will always work. :chatgpt-content-reference{index="3"} :chatgpt-content-reference{index="4"} :chatgpt-content-reference{index="5"} :chatgpt-content-reference{index="6"} :chatgpt-content-reference{index="7"}

**Do not finish the browser-centered refactor in `notes.md` as the main architecture.** Its page objects and symbol-selector modules fit the earlier browser downloader, whereas the notebook now describes a broader acquisition and preparation system. Keep useful browser code isolated rather than making every future exchange conform to it. :chatgpt-content-reference{index="8"}

Treat the notebook’s exchange-capability table as a **discovery checklist**, not yet a tested support matrix. A production adapter needs evidence for the exact market, dataset, historical coverage, and source format it supports. :chatgpt-content-reference{index="9"}

## Recommended Project Structure

Keep the existing import package name initially. Renaming the project can be a separate release decision; it should not delay implementation.

This is the **target layout**, not a request to create dozens of empty files immediately:

```text
repository/
├── pyproject.toml
├── README.md
│
├── docs/
│   ├── architecture.md
│   ├── data-contract.md
│   └── sources/                  # Verified source behavior and limitations
│
├── notebooks/
│   ├── 00_bybit_discovery.ipynb
│   ├── 01_one_archive.ipynb
│   ├── 02_trade_normalization.ipynb
│   ├── 03_book_reconstruction.ipynb
│   └── 04_integrity_research.ipynb
│
├── src/
│   └── bybit_history/
│       ├── __init__.py
│       ├── client.py             # Public Python API
│       ├── cli.py                # Argument parsing and presentation
│       ├── models.py             # Requests, assets, plans, results
│       ├── schemas.py            # Canonical data schemas
│       ├── errors.py
│       ├── planning.py
│       ├── reporting.py
│       │
│       ├── sources/
│       │   ├── base.py           # Small shared source interface
│       │   ├── bybit.py
│       │   └── binance.py        # Other adapters added incrementally
│       │
│       ├── acquisition/
│       │   ├── http.py
│       │   └── download.py
│       │
│       ├── processing/
│       │   ├── parsers/          # Source/dataset/version-specific readers
│       │   ├── normalize.py
│       │   ├── books.py
│       │   └── merge.py
│       │
│       ├── storage/
│       │   ├── paths.py
│       │   └── manifests.py
│       │
│       ├── quality/
│       │   ├── technical.py
│       │   └── policy.py
│       │
│       └── analysis/
│           ├── metrics.py
│           ├── integrity.py
│           ├── intermediation.py
│           └── price_discovery.py
│
├── rust/                         # Add when the first native kernel is ready
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── readers.rs
│       ├── book.rs
│       └── merge.rs
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── live/
│
├── benchmarks/
└── data/                         # Local generated data; not committed
```

### Component Responsibilities

**`sources/` understands exchanges.** It discovers instruments and available assets, interprets source-specific metadata, and resolves download locations. It should not contain terminal progress bars or generic retry implementations.

**`acquisition/` transfers and preserves source data.** It handles HTTP sessions, streaming downloads, retries, temporary files, and transport failures. It should not know what a trade-size anomaly is.

**`processing/` turns source records into canonical datasets.** Source-specific readers interpret formats; shared code coordinates normalization, validation, output, and merging.

**`quality/` determines technical trust and applies explicit selection policies.** `analysis/` calculates market-behavior evidence. Neither should silently rewrite raw data.

**`client.py` coordinates these components.** It should not become another large class containing HTTP, parsing, statistics, and presentation.

Use ordinary functions for transformations and small objects for components that hold resources or state. There is no need for a general plugin framework yet.

### Python and Rust Responsibilities

Keep the intended division, but introduce it progressively:

| Work | Recommended implementation |
|---|---|
| Discovery, HTTP, planning, configuration, CLI | Python |
| First normalization implementation and reference calculations | Python + Polars |
| Statistical indicators and research experiments | Python + Polars |
| Large sequential readers, stateful book reconstruction, specialized merges | Rust once behavior is specified and tested |
| Public interface to native processing | Python wrapper around PyO3 |

Polars supports streaming execution and storage sinks, although some operations can fall back to in-memory execution. That makes it a useful first implementation, but inspect memory use rather than assuming every lazy query is bounded-memory. See the [Polars streaming documentation](https://docs.pola.rs/user-guide/concepts/streaming/).

For Rust, use **one crate initially**, with an internal extension such as `bybit_history._native`. Maturin supports a mixed project with Python under `src/`, Rust in a separate directory, and a private native submodule. See the [Maturin project-layout documentation](https://www.maturin.rs/project_layout.html).

**Pass paths, configuration, or batches across the Python–Rust boundary—not one Python call per market event.**

## Define the Core Contracts First

The notebook contains the goals, but not the raw trade and depth samples needed to finalize every field mapping. Start with a small contract and refine it against actual source files.

### Request Contract

A request should describe **what the user wants**, independently of where it comes from:

```text
exchange
market_kind
instrument
dataset
start
end
```

Distinguish `spot`, `perpetual`, `future`, and `option`. Do not let the old broad `"Contract"` argument become the only internal market classification.

Use **half-open time ranges internally: `[start, end)`**. The compatibility CLI can keep inclusive calendar dates by translating the end date to the following midnight.

### Source Asset Contract

A source asset describes **what can actually be acquired**:

```text
stable asset ID
source and dataset
coverage interval
download locator or API retrieval specification
compression / source format
expected checksum or size, when available
availability evidence
source-format version
```

A URL is not the asset’s identity. The design should allow a locator to change without treating the underlying historical asset as new.

Keep these availability states separate:

```text
AVAILABLE
UNAVAILABLE
UNKNOWN
```

An access-denied response must not become “this date has no trades.”

### Canonical Event Schemas

Start with trades. The essential concepts are:

| Field group | What to preserve |
|---|---|
| Identity | Exchange, native symbol, canonical instrument ID, market kind |
| Time | Normalized timestamp, original timestamp semantics and precision |
| Values | Exact price and quantity representation, explicit quantity units |
| Trade semantics | Source trade ID when present; verified aggressor side or unknown |
| Provenance | Source asset, archive member, original record position |
| Versioning | Schema and parser versions |

Do not infer nanosecond precision merely because timestamps are stored in nanoseconds. The notebook explicitly calls for preserving original precision and semantics. :chatgpt-content-reference{index="10"}

For numeric values, select an exact decimal or scaled-integer representation after inspecting samples. Make scales and units explicit, and reject overflow or unsupported precision rather than silently rounding.

Distinguish **individual trades from aggregated trade records**. Normalizing their column names should not make their granularity appear identical.

For order books, preserve **whole message boundaries**, snapshot/delta type, source sequence fields, and the relationship between all level changes in one update. Those are explicit requirements in the notebook. :chatgpt-content-reference{index="11"}

### Manifest Contract

Every completed dataset should have a small manifest recording:

```text
input asset IDs and hashes
requested coverage and observed coverage
schema / parser / pipeline versions
output files and row counts
timestamp range and ordering rules
quality findings and excluded intervals
filter-policy version, when applied
completion status
```

This becomes the foundation for reproducibility and restarting work.

**A file existing on disk is not sufficient evidence that a pipeline stage completed successfully.**

## Implementation Sequence

### Milestone 0 — Restore a Working Baseline

First make installation, imports, and the existing command entry point work again.

Preserve the old implementation as a reference, correct the `cleint.py` naming issue, and make an explicit decision about which implementation the package exports.

Keep the old public API and CLI through a thin compatibility layer where practical. However, do not preserve browser-specific limitations inside the new core. The old implementation’s five-day chunk restriction belongs to its acquisition method, not to historical market data generally. :chatgpt-content-reference{index="12"}

Clean the development material too: keep generated `.virtual_documents/` content and captured cookies or fingerprint tokens out of commits. The notebook currently includes copied browser-request headers containing those values. :chatgpt-content-reference{index="13"}

**Completion criterion:** A fresh environment can install the package, import its public API, and run the baseline tests.

### Milestone 1 — Discover One Bybit Trade Dataset

Start with the Bybit spot-trade case already explored in the notebook.

Implement a small flow:

```text
saved discovery response
        ↓
parsed instruments / archive entries
        ↓
typed source assets
        ↓
plan for one verified historical day
```

Separate the pure parsing function from the network request. That lets discovery tests run without repeatedly contacting Bybit.

Write a short source note containing the request, response structure, filename pattern, observed availability, and unresolved questions.

Do not immediately implement monthly optimization, all markets, or every exchange.

**Completion criterion:** The reason a particular asset belongs in the plan can be explained and tested, rather than relying on a plausible URL.

### Milestone 2 — Download One Asset Reliably

Implement the generic downloader.

Use one scoped `httpx.AsyncClient` for the acquisition session. HTTPX supports asynchronous streaming and recommends reusing clients rather than creating one inside every download iteration. See the [HTTPX asynchronous client documentation](https://www.python-httpx.org/async/).

The first implementation should:

- Write into a temporary `.part` file, then publish the completed artifact.
- Preserve the raw archive and record its hash and download result.
- Distinguish missing data, access failures, rate limits, corrupt downloads, and interrupted transfers.

Start sequentially. Add bounded concurrency after the failure behavior is correct.

For restarting, initially **skip verified completed assets and restart failed assets individually**. Byte-range resume can come later; it needs separate validation of server support and content identity.

Keep verification claims precise: a locally calculated hash identifies the downloaded bytes; matching a provider-published checksum is a separate check. Successful decompression is another check.

**Completion criterion:** An interrupted run can be repeated without mistaking partial files for valid data or downloading everything again.

This is the first useful release-sized result: **a reliable raw-data downloader without browser-driven symbol selection.**

### Milestone 3 — Normalize Trades and Validate Them

Take one small downloaded archive and implement its parser.

Before a large conversion, inspect a small sample and explicitly establish timestamp units, column meanings, quantity units, side semantics, IDs, ordering, and missing-value behavior.

Implement:

```text
raw archive
    → source records
    → canonical trade records
    → technical findings
    → normalized Parquet + manifest
```

Use Python and Polars first. Do not make native compilation a prerequisite for discovering the correct schema.

Add checks for required fields, numeric conversion, timestamp plausibility, instrument consistency, malformed rows, and ordering. Record rejected records with their source positions and reasons.

For duplicates, define a source-aware identity rule. **Two records sharing timestamp, price, and quantity are not automatically the same trade.** Without sufficient identity evidence, report ambiguity rather than deleting records.

**Completion criterion:** A normalized record can be traced back to its source, every rejected record has an explanation, and the output can be read from a clean notebook.

At this point, test the proposed Parquet contract against `mlfindgen` with a tiny dataset. Do not postpone discovering a consumer incompatibility until after terabytes have been processed.

### Milestone 4 — Extend Bybit, Then Add the Second Exchange

First cover the existing Bybit contract-trade use cases, including the DOGEUSDT and XRPUSDT regressions identified in the notes. :chatgpt-content-reference{index="14"} :chatgpt-content-reference{index="15"}

Then implement Binance trades as the second adapter, for a verified comparable market and date range.

This is where the shared interface gets tested.

The question is:

> Can a second source be added mostly through discovery and format-handling code, without rewriting downloads, manifests, storage, or reporting?

Only now should the small interface in `sources/base.py` be finalized. Two real implementations provide evidence about what is genuinely shared.

**Completion criterion:** Two exchanges produce the same canonical trade schema while retaining their distinct source semantics.

Do not add all the remaining exchanges yet.

### Milestone 5 — Materialize a Two-Exchange Trade Dataset

Implement the simplest merge product first: **trades only**.

Select explicitly comparable instruments. Do not group spot, perpetuals, inverse contracts, and options merely because their symbols contain the same underlying asset.

Validate each input’s ordering and coverage, then write a deterministic merged dataset with a manifest listing its inputs.

The notebook calls for k-way streaming merges when inputs are already sorted. Make that precondition explicit; unsorted inputs need a separate sorting or rejection policy. :chatgpt-content-reference{index="16"}

Distinguish:

**Replay order:** The source’s event or message ordering.

**Analytical time order:** The ordering selected for a chronological research view.

A timestamp sort must not silently rewrite a sequence-sensitive stream. Where the two orders conflict, retain the source evidence and flag the conflict.

**Completion criterion:** Equal-timestamp events have a documented tie rule, overlapping source coverage does not cause accidental duplication, and every output event retains its venue identity.

### Milestone 6 — Add One Order-Book Source, Then the Native Engine

This is the stage where implementation should deliberately slow down.

Build a tiny reference reconstruction using synthetic messages whose expected book state is calculated manually.

Test:

```text
snapshot
    → insert level
    → change quantity
    → delete level
    → invalid/missing update
    → untrusted interval
    → new snapshot
    → trusted state again
```

Use the exact archive semantics verified for the source. For comparison, Bybit’s WebSocket documentation specifies snapshot replacement and zero-size level deletion, but that is not proof that every historical archive has identical semantics. See the [Bybit order-book documentation](https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook).

Important implementation rules:

**Apply a complete message before calculating book metrics.** Do not expose intermediate states created while applying its individual level changes.

**Do not assume every sequence field increments by one.** Implement only the continuity rules supported by that source.

**Plan for initialization.** A requested interval may need an earlier snapshot or checkpoint to establish its starting state.

**Do not repair gaps by pretending they did not happen.** The notebook specifies that affected intervals remain untrusted until valid resynchronization. :chatgpt-content-reference{index="17"}

Once the reference behavior is correct, implement the production stateful kernel in Rust. Use the same fixtures to compare reconstructed states, values, ordering, and findings—not necessarily byte-identical Parquet files.

Then extend materialization to the notebook’s three products: `trades`, `depth`, and combined `events`. Preserve separate book state for each venue and instrument. :chatgpt-content-reference{index="18"}

**Completion criterion:** Reconstruction failures are detectable and explainable, Python and Rust agree on fixtures, and memory use is measured on representative files.

### Milestone 7 — Build Research Indicators in Dependency Order

Technical validation has already been part of earlier milestones. This stage adds the statistical research layer—not basic correctness.

The notebook’s indicators naturally form dependency groups:

| Available foundation                    | Research to build on it                                                                                                                    |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Validated trades                        | Counts and volume, size roundness and clustering, digit distributions, tails, inter-trade timing, entropy, volume–volatility relationships |
| Trades with verified side semantics     | Signed flow, reversal frequency, run lengths, autocorrelation, descriptive churn                                                           |
| Trusted reconstructed books plus trades | Spread and depth, replenishment, volume relative to visible liquidity, price impact, trade–book consistency                                |
| Comparable multi-exchange datasets      | Price and volume divergence, lead–lag, price-discovery analysis, incremental venue information                                             |

These groups preserve the scope of the integrity, intermediation, and price-discovery notes without requiring every detector before the system becomes usable. :chatgpt-content-reference{index="19"} :chatgpt-content-reference{index="20"} :chatgpt-content-reference{index="21"}

For each detector, write a small specification **before** implementing it:

```text
required inputs and source capabilities
method / research reference
window and sample-size requirements
baseline construction
output fields and interpretation
known limitations
synthetic tests
```

The notebook names research methods, but does not provide a complete reproducible specification for every detector. Do not replace those missing specifications with arbitrary thresholds.

A particularly important limitation is cancellation and quote-lifetime analysis. Aggregated price-level updates should not be labeled as exact individual-order cancellations or lifetimes. Bybit’s documented zero-size update, for example, can mean that quotations at that price were filled **or** cancelled. Use explicitly labeled proxies or return `NOT_EVALUABLE`. See the [Bybit order-book documentation](https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook).

Keep anomaly results descriptive, as the notes require. Suspicious patterns are not proof of wash trading, and two-sided churn does not establish hot-potato trading. :chatgpt-content-reference{index="22"} :chatgpt-content-reference{index="23"}

**Completion criterion:** Every finding has a method and version, evidence, and an applicability status.

Trade-only research can begin after Milestone 3; it does not need to wait for the entire order-book implementation.

### Milestone 8 — Expand Coverage and Evaluate Venue Selection

Add OKX, Gate.io, Bitget, and Deribit incrementally, following verified source capabilities—not a requirement that every exchange provide every dataset.

Each addition should bring its own source note, fixtures, parser mappings, capability declarations, and live smoke test.

Then implement the more advanced venue-analysis experiments and compare dataset constructions in `mlfindgen`.

Keep the notebook’s distinction between **price discovery** and **incremental predictive information**. A venue-selection policy should be an experimental result, not a hardcoded assumption that one exchange is always the useful one. :chatgpt-content-reference{index="24"} :chatgpt-content-reference{index="25"}

## Storage and Filtering Rules

Keep the storage layers from the notebook, adding explicit manifests and run identities:

```text
data/
├── raw/
│   └── exchange / source assets
├── normalized/
│   └── schema_version / dataset / exchange / instrument / date
├── merged/
│   └── view_id / dataset / date
├── quality/
│   └── audit_id / findings and interval evidence
└── manifests/
```

A merged `view_id` should identify the input datasets, selected venues, ordering rules, and filter policy. That prevents different research datasets from overwriting one another simply because both represent “BTC-USDT.”

Use the planned Parquet + ZSTD output. Treat the notebook’s 256–512 MB file target as something to benchmark later, not as a prerequisite for the first implementation. A date partition can contain multiple files. :chatgpt-content-reference{index="26"}

**Publish completed datasets through their manifests.** Downstream readers should not accidentally discover half-written outputs by globbing a working directory.

Preserve the audit-first policy: findings are separate from source data, and filtering is explicit and reproducible. :chatgpt-content-reference{index="27"} :chatgpt-content-reference{index="28"}

For books, filtering needs extra care: dropping individual deltas can invalidate subsequent state. Exclude appropriately defined intervals or rebuild from valid initialization; do not treat arbitrary row removal as harmless.

Protect downstream experiments from look-ahead. The impact notes explicitly use future mid-prices. Any such output should record its horizon and earliest availability, so `mlfindgen` cannot mistake a retrospective statistic for a feature available at trade time. :chatgpt-content-reference{index="29"}

## Jupyter Development Workflow

Use the same small cycle for every component:

> **Explore one behavior → save a tiny fixture → implement a package function → test it → import it back into the notebook.**

The notebook is where behavior is inspected and understood. The reusable implementation lives in `src/`. This also follows the workflow already described in the project notes. :chatgpt-content-reference{index="30"} :chatgpt-content-reference{index="31"}

For Python iteration:

```python
%load_ext autoreload
%autoreload 2
```

IPython supports this reload workflow, but native extension modules are not autoreloaded. After rebuilding the Rust extension, restart the kernel rather than assuming the loaded native code changed. See the [IPython autoreload documentation](https://ipython.readthedocs.io/en/stable/config/extensions/autoreload.html).

Design the eventual public API so intermediate results can be inspected. The following is conceptual, not an API already implemented:

```python
assets = await client.discover(request)
plan = client.plan(request, assets)

raw = await client.download(plan)
verification = client.verify(raw)

normalized = client.normalize(raw, verification=verification)
audit = client.validate(normalized)

dataset = client.materialize(
    normalized,
    audit=audit,
    policy=policy,
)
```

Only add a convenience `run()` method after these individual operations work.

### Tests Accompany Every Milestone

| Test category | Essential cases |
|---|---|
| Pure unit tests | Dates, asset selection, schema mappings, numeric conversions, deduplication rules |
| Download integration tests | Interrupted transfer, HTML error response, corrupt archive, retries, existing verified file |
| Golden-data tests | Tiny raw input with manually checked normalized output and findings |
| Stateful book tests | Message atomicity, initialization, sequence failure, snapshot reset, partition boundaries |
| Compatibility and live tests | Existing CLI and API behavior; opt-in checks against actual supported sources |

Include DOGEUSDT and XRPUSDT as explicit regressions, then broaden coverage with unusual symbol shapes and reproducible samples of supported instruments. Do not depend only on random live tests.

The current ignore rules exclude CSV, GZIP, and JSONL broadly, so explicitly allow the tiny fixtures needed by tests—or generate them during testing. :chatgpt-content-reference{index="32"}

## First Implementation Target

After restoring package imports, implement only this:

```text
Bybit discovery
    → plan one verified archive
    → download it safely
    → preserve its original bytes
    → normalize a small trade dataset
    → produce Parquet, findings, and a manifest
    → read it successfully in Jupyter and mlfindgen
```

**That is the first complete piece to build.**

Once it works, a second exchange tests the architecture, order-book reconstruction tests the state model, and large datasets reveal where custom Rust is actually valuable. Everything else in the notebook then has a trustworthy foundation instead of becoming another large rewrite.