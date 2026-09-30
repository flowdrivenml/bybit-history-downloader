## Historical Data Sources

## Quick Navigation

- [Bybit](#Bybit Historical Data Acquisition)
- [Binance](#binance)
- [OKX](#okx)
- [Gateio](#gateio)
- [Bitget](#bitget)

## Bybit Historical Data Acquisition
## Trades

### Spot

Archive root:

```text
https://public.bybit.com/spot/
```

Pattern:

```text
https://public.bybit.com/spot/{SYMBOL}/{SYMBOL}_{YYYY-MM-DD}.csv.gz
```

The root is browsable, so MarketForge can discover symbols and then enumerate the files available for each symbol.

### Futures and Perpetuals

Archive root:

```text
https://public.bybit.com/trading/
```

Pattern:

```text
https://public.bybit.com/trading/{SYMBOL}/
```

The archive is browsable and exposes the symbols and historical trade files.

### Options

Pattern:

```text
https://public.bybit.com/trade/option/{BASE}/{DATE}_{BASE}_{QUOTE}.trades.csv.zip
```

Example:

```text
https://public.bybit.com/trade/option/BTC/2026-09-21_BTC_USDT.trades.csv.zip
```

Option directories are not conveniently browsable, so availability should be discovered through Bybit's historical-file endpoint.

## Depth

### Spot

```text
https://quote-saver.bycsi.com/orderbook/spot/
```

### Linear

```text
https://quote-saver.bycsi.com/orderbook/linear/
```

### Inverse

```text
https://quote-saver.bycsi.com/orderbook/inverse/
```

These roots are browsable and can be used to discover instruments and historical depth files.

### Options

Pattern:

```text
https://quote-saver.bycsi.com/orderbook/option/{BASE}/{DATE}_{BASE}_{QUOTE}.ob25.zip
```

Example:

```text
https://quote-saver.bycsi.com/orderbook/option/BTC/2026-09-24_BTC_USDT.ob25.zip
```

As with option trades, use API-based historical-file discovery rather than relying on directory browsing.

## Instrument Discovery

Use Bybit's official market APIs for current instrument metadata.

Spot:

```text
GET https://api.bybit.com/v5/market/instruments-info?category=spot
```

Linear:

```text
GET https://api.bybit.com/v5/market/instruments-info?category=linear&limit=1000
```

Inverse:

```text
GET https://api.bybit.com/v5/market/instruments-info?category=inverse&limit=1000
```

Options base coins:

```text
GET https://api.bybit.com/v5/market/option-base-coins
```

All option contracts:

```text
GET https://api.bybit.com/v5/market/instruments-info?category=option&baseCoin=All&limit=1000
```

Use `nextPageCursor` where pagination is required.

## Historical Availability

For browsable Spot, Futures and Depth archives:

```text
archive root
    ↓
symbol directory
    ↓
available files
```

For Options, use:

```text
GET https://www.bybit.com/x-api/quote/public/support/download/list-files
```

Example:

```text
https://www.bybit.com/x-api/quote/public/support/download/list-files?bizType=option&productId=trade&symbols=BTC&interval=daily&periods=&startDay=2026-09-22&endDay=2026-09-28
```

The endpoint supports a **maximum 7-day interval** per request.

For longer historical ranges, MarketForge should:

```text
split requested range into ≤7-day windows
        ↓
call list-files iteratively
        ↓
respect rate limits and retry/backoff rules
        ↓
collect returned file URLs
        ↓
deduplicate and concatenate results
        ↓
reconstruct complete historical availability
```

This allows MarketForge to discover exactly which option archives exist without brute-forcing individual file URLs.

### Archive Directory Structure

For browsable Spot and Futures trade/depth archives, each instrument directory contains both **daily** and **monthly** files.

Example:

```
https://public.bybit.com/spot/BTCUSDT/

BTCUSDT-2026-05.csv.gz        # monthly
BTCUSDT-2026-06.csv.gz        # monthly
BTCUSDT_2022-11-10.csv.gz     # daily
BTCUSDT_2022-11-11.csv.gz     # daily
...
```

MarketForge will use **daily files only** and ignore monthly archives to keep acquisition, validation, partitioning, and deduplication consistent.

These archive pages expose their contents as ordinary HTML lists (`<ul>` / `<li>` with links), so symbol and file discovery does not require browser automation. A lightweight HTML parser such as **Beautiful Soup** is sufficient:

```
archive root
    ↓
parse HTML
    ↓
extract directory/file links
    ↓
filter daily archives
    ↓
build availability map
```

This same approach can be used for the browsable Bybit Spot and Futures trade/depth directories.


---

## Binance Historical Data Acquisition


Main historical-data archive:

```text
https://data.binance.vision/
```

Binance uses:

```text
UM = USDⓈ-M futures  → linear
CM = COIN-M futures  → inverse
```

### Spot Trades

Archive root:

```text
https://data.binance.vision/?prefix=data/spot/daily/trades/
```

Structure:

```text
data/spot/daily/trades/{SYMBOL}/
```

### Linear Futures Trades

Binance calls these **USDⓈ-M (`um`) futures**.

Archive root:

```text
https://data.binance.vision/?prefix=data/futures/um/daily/trades/
```

Structure:

```text
data/futures/um/daily/trades/{SYMBOL}/
```

### Inverse Futures Trades

Binance calls these **COIN-M (`cm`) futures**.

Archive root:

```text
https://data.binance.vision/?prefix=data/futures/cm/daily/trades/
```

Example:

```text
https://data.binance.vision/?prefix=data/futures/cm/daily/trades/BTCUSD_PERP/
```

No historical options-trade integration is planned from Binance at this stage.

### Instrument Discovery

Use Binance's public `exchangeInfo` endpoints.

Spot:

```text
GET https://api.binance.com/api/v3/exchangeInfo
```

Linear / USDⓈ-M:

```text
GET https://fapi.binance.com/fapi/v1/exchangeInfo
```

Inverse / COIN-M:

```text
GET https://dapi.binance.com/dapi/v1/exchangeInfo
```

These provide currently known symbols and market metadata.

### Historical Availability

Historical availability should be discovered directly from the Binance archive, using the same logic as the browsable Bybit archives:

```text
archive root
    ↓
parse listed symbol folders
    ↓
open {SYMBOL}/
    ↓
enumerate available daily files
    ↓
build historical availability map
```

For example:

```text
data/spot/daily/trades/
data/futures/um/daily/trades/
data/futures/cm/daily/trades/
```

The archive listings expose the available prefixes/files, so MarketForge can scrape them with a lightweight HTML parser rather than guess dates.

As with Bybit:

```text
exchangeInfo
    ↓
which instruments exist

data.binance.vision
    ↓
which historical files actually exist
```

> Use Binance APIs for instrument metadata, and the archive listings as the source of truth for historical availability.

---

## OKX Historical Data Acquisition

## Endpoint

MarketForge should use the official OKX historical market-data endpoint only:

```text
GET https://www.okx.com/api/v5/public/market-data-history
```

Example for BTC-USDT perpetual tick trades:

```text
GET /api/v5/public/market-data-history?module=1&instType=SWAP&instFamilyList=BTC-USDT&dateAggrType=daily&begin=1756604295000&end=1756777095000
```

Rate limit:

```text
5 requests / 2 seconds / IP
```

The endpoint does **not return the market events directly**. It returns metadata and download URLs for the historical archive files.

## Data Modules

```text
module=1   Tick-by-tick trades
module=2   1-minute candles
module=3   Funding rates
module=4   400-level order book
module=5   5000-level order book
module=6   50-level order book
module=11  Borrowing rates
```

MarketForge's primary microstructure targets are:

```text
1 → trades
4 → 400-level depth
5 → 5000-level depth
```

## Instrument Selection

Market type:

```text
instType=SPOT
instType=FUTURES
instType=SWAP
instType=OPTION
```

For Spot, use `instIdList`:

```text
instType=SPOT
instIdList=BTC-USDT
```

Multiple instruments:

```text
instIdList=BTC-USDT,ETH-USDT
```

Maximum:

```text
10 instruments
```

For Futures, Swaps, and Options, use `instFamilyList`:

```text
instType=SWAP
instFamilyList=BTC-USDT
```

Multiple families:

```text
instFamilyList=BTC-USDT,ETH-USDT
```

Maximum:

```text
10 instrument families
```

For supported modules with daily aggregation, OKX also allows:

```text
instIdList=ANY
```

or:

```text
instFamilyList=ANY
```

This is useful when requesting all available instruments for a period.

## Date Ranges

Aggregation:

```text
dateAggrType=daily
dateAggrType=monthly
```

`begin` and `end` are Unix timestamps in **milliseconds**, both inclusive.

Maximum request range:

```text
daily   → 10 days
monthly → 10 months
```

Example:

```text
begin=1756604295000
end=1756777095000
```

For larger ranges, MarketForge must split the request:

```text
requested range
    ↓
split into ≤10-day windows
    ↓
query sequentially
    ↓
respect 5 requests / 2 seconds
    ↓
concatenate returned file metadata
```

## Response Handling

Successful responses contain:

```text
data[]
    ├── dateAggrType
    ├── totalSizeMB
    └── details[]
            ├── instId
            ├── instFamily
            ├── instType
            ├── dateRangeStart
            ├── dateRangeEnd
            ├── groupSizeMB
            └── groupDetails[]
                    ├── filename
                    ├── dateTs
                    ├── sizeMB
                    └── url
```

Example file metadata:

```json
{
  "dateTs": "1756656000000",
  "filename": "BTC-USDT-SWAP-trades-2025-09-01.zip",
  "sizeMB": "10.82",
  "url": "https://static.okx.com/cdn/okex/traderecords/trades/daily/20250901/BTC-USDT-SWAP-trades-2025-09-01.zip"
}
```

MarketForge should extract:

```text
instrument
date
filename
size
download URL
```

and download the returned `url` directly.

If no historical files exist:

```json
{
  "details": [],
  "totalSizeMB": "0"
}
```

That should be treated as **no available data for that request**, not as an API failure.

> Note: the supplied OKX response example uses `dateTs` inside `groupDetails`, while the parameter table labels the field `dataTs`. The implementation should verify the actual JSON field returned by the API rather than relying only on the table label.

## Historical Availability

Normal MarketForge behavior should query only the range requested by the user:

```text
instrument + dataset + requested dates
        ↓
market-data-history
        ↓
returned historical files
        ↓
download
```

OKX does not provide, in this endpoint, one simple field giving the complete lifetime historical coverage of an instrument.

MarketForge may therefore optionally provide a **full availability scan**:

```text
choose instrument / module
        ↓
walk historical time in valid API windows
        ↓
collect all non-empty responses
        ↓
deduplicate returned files
        ↓
build complete availability map
```

Because this requires repeated API calls, it can take time. Before running such a scan, MarketForge should calculate and show:

```text
required API calls
estimated minimum request time
selected date range
rate-limit constraint
```

The user can then choose between:

```text
1. Query only the desired historical range
2. Scan the full historical availability first
```

> **OKX acquisition is API-driven: request historical metadata through `market-data-history`, then download the archive URLs returned by OKX.**

## Instrument Discovery

Use OKX's public instruments endpoint:

```text
GET https://www.okx.com/api/v5/public/instruments
```

Select the market with `instType`:

```text
SPOT
FUTURES
SWAP
OPTION
```

Examples:

```text
GET /api/v5/public/instruments?instType=SPOT
GET /api/v5/public/instruments?instType=SWAP
GET /api/v5/public/instruments?instType=FUTURES
GET /api/v5/public/instruments?instType=OPTION
```

The response provides the available instruments together with metadata such as:

```text
instId
instType
instFamily
baseCcy
quoteCcy
settleCcy
state
tickSz
lotSz
expTime
```

MarketForge should use this endpoint to build the valid instrument universe before requesting historical files.

Conceptually:

```text
public/instruments
    ↓
available instruments + metadata
    ↓
select instId / instFamily
    ↓
market-data-history
    ↓
historical file metadata
    ↓
download
```

For Spot:

```text
instId
```

is the main identifier used for historical requests.

For Futures, Swaps, and Options:

```text
instFamily
```

is especially important because `market-data-history` uses `instFamilyList` for non-Spot markets.

> **Instrument discovery tells MarketForge what markets exist; `market-data-history` tells it which historical files exist for those instruments and dates.**
---

## Gate.io Historical Data Acquisition
## Instrument Discovery

Use Gate.io public APIs to discover currently available instruments.

Spot:

```text
GET https://api.gateio.ws/api/v4/spot/currency_pairs
```

USDT-settled perpetual futures:

```text
GET https://api.gateio.ws/api/v4/futures/usdt/contracts
```

BTC-settled perpetual futures:

```text
GET https://api.gateio.ws/api/v4/futures/btc/contracts
```

Dated delivery futures can be discovered through the corresponding delivery contract endpoint.

These APIs provide instrument identifiers and metadata. Historical availability is determined separately from the bulk archive.

## Historical Archive

Gate.io historical files use deterministic URLs under:

```text
https://download.gatedata.org/
```

General structure:

```text
https://download.gatedata.org/{market}/{dataset}/{YYYYMM}/{filename}
```

Main market roots include:

```text
spot
futures_usdt
futures_btc
```

## Trades

Spot trades:

```text
https://download.gatedata.org/spot/deals/{YYYYMM}/{SYMBOL}-{YYYYMM}.csv.gz
```

Example:

```text
https://download.gatedata.org/spot/deals/201801/ADA_BTC-201801.csv.gz
```

Futures use the corresponding futures market root and trade dataset path.

## Order Book

Spot order-book files follow deterministic time-based paths.

Example:

```text
https://download.gatedata.org/spot/orderbooks/202609/BTC_USDT-2026092720.csv.gz
```

This represents:

```text
market  = spot
dataset = orderbooks
month   = 202609
symbol  = BTC_USDT
date    = 2026-09-27
hour    = 20
```

Gate also exposes order-book snapshot archives through:

```text
orderbooks_slice
```

## Historical Availability

Gate.io does not need a separate historical-discovery API because the archive URLs are deterministic.

MarketForge can generate the expected URLs for the requested interval and check them using HTTP `HEAD` requests.

Example:

```python
import requests

url = "https://download.gatedata.org/spot/orderbooks/202609/BTC_USDT-2026092720.csv.gz"

response = requests.head(
    url,
    allow_redirects=True,
    timeout=20,
)
```

Interpretation:

```text
200 → file exists
404 → file unavailable
429 → rate limited
other → unknown / retry
```

Because `HEAD` returns only response metadata, the full archive is **not downloaded**.

For a larger period:

```text
generate expected URLs
        ↓
HEAD each URL
        ↓
respect rate limits
        ↓
retry transient failures
        ↓
record available files
        ↓
build historical availability map
```

This allows MarketForge to determine historical coverage cheaply before downloading the actual data.

## Acquisition Logic

```text
Gate API
    ↓
discover instruments

requested date range
    ↓
construct deterministic gatedata URLs
    ↓
HEAD requests
    ↓
available files
    ↓
download selected archives
```

Core rule:

> **Use Gate.io APIs for instrument discovery, and deterministic archive URLs plus `HEAD` requests for historical availability.**

---
## Bitget Historical Data Acquisition

## Endpoints

Symbol discovery:

```text
POST https://www.bitget.com/v1/statistics/public/download/getSymbolList
```

Historical file discovery:

```text
POST https://www.bitget.com/v1/statistics/public/download/getPublicDataV2
```

`getPublicDataV2` returns the actual historical archive URLs, so MarketForge should use those URLs rather than infer Bitget's CDN filename patterns.

## Parameters

Observed meanings:

```text
businessLine = 1  → Spot
businessLine = 2  → Futures

businessType = 2  → Trades
businessType = 3  → Depth

dateType = 1      → Daily

deptType = 2      → Depth configuration used by the download interface
```

## Spot

### Trade Symbols

```json
{
  "displaySymbol": "BTC",
  "businessLine": 1,
  "businessType": 2,
  "languageType": 12
}
```

### Trade Files

```json
{
  "displaySymbol": ["BTC/USDT"],
  "businessLine": 1,
  "businessType": 2,
  "dateType": 1,
  "beginTimeStr": "2026-06-01",
  "endTimeStr": "2026-06-07"
}
```

### Depth Symbols

```json
{
  "displaySymbol": "BTC",
  "businessLine": 1,
  "businessType": 3,
  "languageType": 12
}
```

Depth files use the same `getPublicDataV2` endpoint with:

```text
businessLine = 1
businessType = 3
```

plus the requested dates and required depth parameters.

## Futures

### Trade Symbols

```json
{
  "displaySymbol": "BTC",
  "businessLine": 2,
  "businessType": 2,
  "languageType": 12
}
```

### Trade Files

```json
{
  "displaySymbol": ["BTCUSDC"],
  "businessLine": 2,
  "businessType": 2,
  "dateType": 1,
  "beginTimeStr": "2026-09-23",
  "endTimeStr": "2026-09-28"
}
```

### Depth Symbols

```json
{
  "displaySymbol": "BTC",
  "businessLine": 2,
  "businessType": 3,
  "languageType": 12
}
```

### Depth Files

```json
{
  "displaySymbol": ["BTCUSDT"],
  "businessLine": 2,
  "businessType": 3,
  "dateType": 1,
  "beginTimeStr": "2026-09-02",
  "endTimeStr": "2026-09-08",
  "deptType": 2
}
```

## Historical Availability

Bitget does not currently give us one simple request containing the complete historical lifetime of every symbol.

Normal MarketForge flow:

```text
getSymbolList
    ↓
available symbols
    ↓
user requests date range
    ↓
getPublicDataV2
    ↓
returned historical file URLs
    ↓
download
```

If the user wants to discover the **complete available history**, MarketForge can query successive date windows:

```text
split timeline into request windows
        ↓
call getPublicDataV2 repeatedly
        ↓
respect Bitget rate limits / retry policy
        ↓
collect returned URLs
        ↓
deduplicate and concatenate
        ↓
build complete availability map
```

A full availability scan may require many API calls, so MarketForge should estimate the required number of requests and expected scan time before starting.

> **Use `getSymbolList` to discover instruments and `getPublicDataV2` to discover the actual historical trade/depth archive URLs.**
---

### Rate Limiting

The exact rate limits for Bitget's historical-download endpoints are currently unknown:

```text
POST /v1/statistics/public/download/getSymbolList
POST /v1/statistics/public/download/getPublicDataV2
```

These endpoints appear to be **internal website endpoints used by Bitget's data-download page**, rather than documented public developer APIs.

Because of that:

```text
published rate limit      → unknown
rate-limit headers        → not exposed
Cloudflare protection     → present
```

MarketForge should therefore use conservative throttling and adaptive backoff:

```text
start slowly
    ↓
detect 429 / 403 / transient errors
    ↓
exponential backoff
    ↓
retry safely
```

> **Until a reliable limit is established experimentally, Bitget historical-discovery requests should be treated as fragile internal web calls rather than normal documented API calls.**


---

## Acquisition Summary

| Exchange    | Primary Access Method                                         | Starting Point                              |
| ----------- | ------------------------------------------------------------- | ------------------------------------------- |
| **Bybit**   | Deterministic public files + directories + discovery endpoint | `public.bybit.com`, `quote-saver.bycsi.com` |
| **Binance** | Public archive/files                                          | `data.binance.vision`                       |
| **OKX**     | Historical download-link request / historical API             | OKX historical-data page                    |
| **Gate.io** | Deterministic public downloads                                | Gate historical-quotes page                 |
| **Bitget**  | Public historical download files                              | Bitget data-download page                   |
| **Deribit** | Historical REST API                                           | `history.deribit.com/api/v2/`               |

The next exploration work should therefore focus only on filling the missing acquisition contracts:

```text
Binance  → exact path patterns by market/dataset
OKX      → minimal download-link API request
Gate.io  → exact path patterns
Bitget   → exact download paths/endpoints
Deribit  → exact API methods + pagination
```

Bybit is already the best-understood source in the current notebook.