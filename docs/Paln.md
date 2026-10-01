## Remaining MarketForge Implementation

- **Instrument metadata**
    
    - `exchanges`
    - `instruments`
    - `instrument_specs`
    - `instrument_api_raw`
    - Repository/models for those tables.
    - Reusable metadata synchronization interface.
- **Exchange metadata providers**
    - Bybit first.
    - Binance.
    - OKX.
    - Bitget.
    - Gate.io.
    - Resolve quantity semantics and contract specifications while implementing each provider.
- **Raw-format registry**
    
    - Encode the raw formats we already inspected:  
        `BYBIT-T1`, `OKX-B1`, `GATE-B2`, etc.
    - Populate `raw_formats`.
- **Normalization mappings**
    
    - Convert `docs/Normalization Mapping.md` into version-controlled definitions.
    - Populate `normalization_rules`.
    - Preserve `is_rpi`.
    - Preserve option IV/mark/index information.
    - Define derived features such as `tick_direction`.
- **Canonical Rust data model**
    
    - Canonical `Trade`.
    - Canonical `L2Event`.
    - Operations `set/add/subtract`.
    - Instrument metadata passed/resolved using `instrument_id`.
    - Exact numeric representation decision.
- **Historical normalization engine**
    
    - Implement raw Trade parsers.
    - Implement raw L2 parsers.
    - Sequence/integrity validation.
    - Quantity normalization using instrument metadata.
    - L2 reconstruction where required.
    - Normalize timestamps.
    - Handle cross-file continuity.
- **Parquet output**
    
    - Final physical Arrow/Parquet schemas.
    - Partition layout.
    - Trade writer.
    - L2 writer.
    - Option-specific fields.
    - Validation of generated Parquet.
- **Historical pipeline**
    
    - Discovery → download → validate → normalize → Parquet.
    - Python orchestration around the Rust engine.
    - CLI commands.
    - Incremental/restartable operation.
- **Rolling PostgreSQL market-data store**
    
    - Recent canonical trades.
    - Recent L2/bootstrap representation.
    - Approximately 24-hour retention.
    - Efficient indexes/partition strategy.
    - Snapshot + replay bootstrap logic.
- **Rust live market-data service**
    
    - Reuse/mirror WebSocket infrastructure from your previous project.
    - Exchange subscriptions.
    - Reconnection.
    - Sequence handling.
    - Live normalization.
    - In-memory L2 reconstruction.
    - Async PostgreSQL persistence.
- **Low-latency IPC**
    
    - Rust → local trading software.
    - Compact binary canonical messages.
    - Numeric `instrument_id`.
    - Start with Unix-domain sockets.
    - Benchmark before considering shared memory.
- **Bootstrap → live handoff**
    
    - Load recent PostgreSQL history.
    - Reconstruct required state.
    - Buffer concurrent live events.
    - Establish exact handoff point.
    - Apply buffered events.
    - Continue from live IPC without gaps/duplicates.
- **Merging**
    
    - Trade-only merge.
    - L2-only merge.
    - Trade + L2 merge.
    - Cross-exchange synchronized merge.
    - Feed directly into `mlfindgen`.
- **Testing and benchmarking**
    
    - Unit tests.
    - Fixture tests using all the raw formats we inspected.
    - Integration tests.
    - Live guarded tests.
    - Historical ↔ live equivalence tests.
    - Throughput and latency benchmarks.
    - IPC `p50/p95/p99/p99.9`.
    - PostgreSQL ingestion/bootstrap benchmarks.