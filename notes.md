Yes, that workflow makes sense. I’d keep the reusable code in the package and use Jupyter to run and inspect individual pieces while we build them. That way a fix you develop in a notebook becomes part of the actual CLI and Python library instead of having to copy it over later.
Suggested structure
The repo already has a src/ layout, which is a good fit for a packaged Python project. Keep it, install the project in editable mode in your notebook environment, and import the code you’re working on. The layout helps ensure you’re exercising the installed package rather than accidentally importing something from the repository root. 
bybit-history-downloader/
├── pyproject.toml
├── README.md
├── notebooks/
│   ├── 00_playwright_sandbox.ipynb
│   └── 01_symbol_selection_debug.ipynb
├── src/
│   └── bybit_history/
│       ├── __init__.py
│       ├── cli.py
│       ├── client.py
│       ├── models.py
│       ├── planning.py
│       ├── errors.py
│       ├── reporting.py
│       ├── browser/
│       │   ├── session.py
│       │   ├── history_page.py
│       │   ├── symbol_selector.py
│       │   └── download_dialog.py
│       └── downloads/
│           ├── collector.py
│           └── archives.py
└── tests/
    ├── unit/
    ├── browser/
    └── live/

Here’s what each part should own:
- client.py stays the small public entry point, preserving BybitHistoryClient and its current methods where practical.
- planning.py handles date validation and chunk creation. It should not need a browser, which makes it quick to test.
- browser/session.py owns Playwright startup and cleanup.
- history_page.py, symbol_selector.py, and download_dialog.py hold the site-specific interactions. The virtualized symbol list deserves its own module because that’s where the DOGEUSDT/XRPUSDT bug appears to be.
- downloads/ saves browser downloads and extracts ZIP/GZIP files.
- reporting.py keeps Rich progress output separate from the downloading logic, so the same client can run quietly in a notebook or with progress in the CLI.
- models.py holds typed request and result objects; errors.py gives failures clear names, such as “symbol not found” or “download timed out.”
Patterns I’d use
The main pattern is a thin client facade: users keep calling BybitHistoryClient, while that class delegates the actual steps to smaller components. This gives us room to rewrite internals without needlessly changing the CLI or library API.
For the browser side, use page objects: each object represents a meaningful part of Bybit’s UI and exposes actions like “choose market” or “select symbol.” Keep selectors and scrolling behavior there, rather than scattering raw Playwright calls throughout the download flow.
For the rest, use a functional core with an imperative shell. Date checks, chunk planning, and output naming can be plain functions. Playwright navigation, clicks, and downloads are the side-effecting shell around them. That division makes fast tests possible without opening a browser for every case.
I wouldn’t add a general plugin or strategy framework yet. If we later add a second way to retrieve data, such as a direct download source, then a small shared interface for download sources could make sense.
How Jupyter fits
Use notebooks to explore the live page, inspect what Playwright sees, and iterate on a specific component. Keep the confirmed implementation in the package modules, then import it from the notebook with editable installation and autoreload:
%pip install -e .%load_ext autoreload%autoreload 2from bybit_history import BybitHistoryClient


Then use top-level await in a notebook cell to run the client. Keep a browser session scoped to an async with block so each run closes its context and browser cleanly; Playwright recommends closing explicitly created contexts before closing the browser. 
For feedback, I’d use three levels:
- Unit tests for date planning, validation, and archive handling.
- Browser tests with a local fixture page for virtualized-list behavior, so the key regression is repeatable.
- Opt-in live tests for real Bybit checks, including symbol selection for DOGEUSDT and XRPUSDT. A notebook can run those interactively while we develop; the test suite can run them when we want a repeatable check against the live site.
I’d build it in this order: first preserve the public CLI/API shape, then extract the pure planning and archive code, then give the browser session and symbol selector their own modules, and finally add the fixture-based regression and live smoke checks. In the browser code, we should also replace arbitrary sleeps where possible with waits for specific UI states; Playwright’s guidance favors its auto-waiting behavior over manual timeouts.
