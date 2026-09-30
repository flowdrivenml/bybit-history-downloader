Availability discovery can have two forms:

```text
DIRECT
→ complete availability exposed in one/few requests
→ e.g. browsable Bybit Spot / Linear / Inverse archives

SCAN
→ availability must be reconstructed through repeated requests
→ e.g. Bybit Options, potentially OKX / Gate.io / Bitget
```

For scanned availability, MarketForge should **estimate the cost before execution**:

```text
requested range
→ calculate required request windows
→ apply RequestPolicy interval
→ estimate minimum execution time
```

Example:

```text
372 days / 7-day windows ≈ 54 requests

Request interval: 2 s
Estimated minimum: (54 - 1) × 2 ≈ 106 s
```

CLI should expose:

```text
Strategy
Number of requests
Request interval
Estimated time
```

Exchange adapters define conservative default `RequestPolicy` values, while the CLI may allow users to override them.

> Availability discovery should remain separate from downloading: it discovers **what exists and where**, without downloading market data.
