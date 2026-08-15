import asyncio
import re
import zipfile

from pathlib import Path
from typing import List, Literal, Set

from playwright.async_api import Locator, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright, expect
from .reporters import DownloadProgress

from .utils import gunzip_file, split_date_range

from time import perf_counter

from .ui import (
    action,
    console,
    show_complete,
    show_job,
    step,
)


class BybitHistoryClient:
    """
    Client for downloading historical market data from Bybit's
    public history-data interface.
    """

    BASE_HISTORY_URL = "https://www.bybit.com/en/derivative-activity/history-data/"

    def __init__(
        self,
        headless: bool = True,
        browser_name: str = "firefox",
    ):
        self.headless = headless
        self.browser_name = browser_name

        self._pw = None
        self._browser = None
        self._context = None
        self.page: Page | None = None

    async def __aenter__(self):
        self._pw = await async_playwright().start()

        browser_type = getattr(
            self._pw,
            self.browser_name,
        )

        if self.browser_name == "chromium" and self.headless:
            self._browser = await browser_type.launch(
                headless=True,
                channel="chromium",
            )
        else:
            self._browser = await browser_type.launch(
                headless=self.headless,
            )

        self._context = await self._browser.new_context(accept_downloads=True)

        self.page = await self._context.new_page()

        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        if self._context:
            await self._context.close()

        if self._browser:
            await self._browser.close()

        if self._pw:
            await self._pw.stop()

    async def show_spot_symbols(self):
        """Display available Spot symbols."""
        symbols = await self._get_symbols("Spot")
        self._print_symbols("SPOT", symbols)

    async def show_contract_symbols(self):
        """Display available Contract symbols."""
        symbols = await self._get_symbols("Contract")
        self._print_symbols("CONTRACT", symbols)

    async def download_data(
        self,
        margin: Literal["Spot", "Contract"],
        data_type: Literal["Trades", "L2Book"],
        symbol: str,
        start_date: str,
        end_date: str,
        final_path: str,
        *,
        chunk_days: int = 5,
    ):
        """
        Download historical data over a date range.

        Longer ranges are automatically split into smaller chunks.
        """

        if chunk_days <= 0 or chunk_days >= 6:
            raise ValueError("chunk_days must be greater than 0 and smaller than 6")

        ranges = split_date_range(
            start_date,
            end_date,
            chunk_days,
        )

        show_job(
            symbol=symbol,
            margin=margin,
            data_type=data_type,
            start_date=start_date,
            end_date=end_date,
            output_dir=final_path,
            chunks=len(ranges),
        )

        started = perf_counter()

        all_paths: list[Path] = []

        for index, (start, end) in enumerate(
            ranges,
            start=1,
        ):
            action(f"Chunk {index}/{len(ranges)}  {start} → {end}")

            produced = await self._download_data_helper(
                margin=margin,
                data_type=data_type,
                symbol=symbol,
                start_date=start,
                end_date=end,
                final_path=final_path,
            )

            if produced:
                all_paths.extend(produced)

            step(f"Chunk {index}/{len(ranges)} complete")

        elapsed = perf_counter() - started

        show_complete(
            all_paths,
            elapsed=elapsed,
            output_dir=final_path,
        )

        return all_paths

    async def _download_data_helper(
        self,
        margin: Literal["Spot", "Contract"],
        data_type: Literal["Trades", "L2Book"],
        symbol: str,
        start_date: str,
        end_date: str,
        final_path: str,
    ):
        page = await self._walk_over_site(
            margin=margin,
            data_type=data_type,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )

        return await self._click_and_save_download(
            page=page,
            save_dir=final_path,
            click_locator="Download",
        )

    async def _walk_over_site(
        self,
        margin: Literal["Spot", "Contract"],
        data_type: Literal["Trades", "L2Book"],
        symbol: str,
        start_date: str,
        end_date: str,
    ):
        if self.page is None:
            raise RuntimeError(
                "Client not started. Use: async with BybitHistoryClient(...) as client:"
            )

        page = self.page

        # First navigation
        await page.goto(
            self.BASE_HISTORY_URL,
            timeout=100_000,
            wait_until="domcontentloaded",
        )

        await page.wait_for_timeout(2500)

        # Bybit sometimes redirects Playwright to the EU homepage.
        # Navigating to the history page again after the redirect
        # currently gets us to the correct page.
        if page.url != self.BASE_HISTORY_URL:
            await page.goto(
                self.BASE_HISTORY_URL,
                timeout=100_000,
                wait_until="domcontentloaded",
            )

            await page.wait_for_timeout(2500)

        await page.wait_for_load_state(
            "networkidle",
            timeout=60_000,
        )

        # ---------------------------------------------------------
        # Select Trades / OrderBook section and Spot / Contract
        # ---------------------------------------------------------

        hover_element = (
            "Public Trading History" if data_type == "Trades" else "OrderBook"
        )

        await self._hover(
            page,
            element=hover_element,
        )

        await self._attempt_click_visible_element(
            page=page,
            margin=margin,
            nth=self._get_nth(
                margin=margin,
                data_type=data_type,
            ),
        )

        await page.wait_for_timeout(500)

        # ---------------------------------------------------------
        # Select symbol
        # ---------------------------------------------------------

        await self._antd_select_option(
            page,
            symbol=symbol,
        )

        # Close symbol dropdown
        await page.mouse.click(20, 20)
        await page.wait_for_timeout(300)

        # ---------------------------------------------------------
        # Select frequency / cycle
        # ---------------------------------------------------------

        selectors = page.get_by_text(
            "please select",
            exact=True,
        )

        frequency_selector = None

        for i in range(await selectors.count()):
            candidate = selectors.nth(i)

            if await candidate.is_visible():
                frequency_selector = candidate
                break

        if frequency_selector is None:
            raise RuntimeError("Could not find frequency selector")

        await frequency_selector.click()
        await page.wait_for_timeout(300)

        everyday_options = page.get_by_text(
            "Everyday",
            exact=True,
        )

        for i in range(await everyday_options.count()):
            everyday = everyday_options.nth(i)

            if await everyday.is_visible():
                await everyday.click()
                break
        else:
            raise RuntimeError("Could not find visible 'Everyday' option")

        # Close frequency dropdown
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)

        # ---------------------------------------------------------
        # Dates
        # ---------------------------------------------------------

        start = page.locator('input[placeholder="Start date"]')

        await start.wait_for(
            state="visible",
            timeout=10_000,
        )

        await start.click()
        await start.fill(start_date)
        await start.press("Enter")

        end = page.locator('input[placeholder="End date"]')

        await end.wait_for(
            state="visible",
            timeout=10_000,
        )

        await end.click()
        await end.fill(end_date)
        await end.press("Enter")

        # ---------------------------------------------------------
        # Confirm
        # ---------------------------------------------------------

        confirm = page.locator(".download-modal__confirm")

        await confirm.wait_for(
            state="visible",
            timeout=10_000,
        )

        await confirm.click()

        await page.wait_for_timeout(500)

        return page

    @classmethod
    async def _click_and_save_download(
        cls,
        page,
        save_dir,
        click_locator="Download",
        prefix: str = "",
        *,
        collect_window_ms: int = 1200,
        poll_ms: int = 100,
    ):
        save_dir = Path(save_dir)

        save_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        button = page.locator(".download-list-modal-btn-confirm")

        await button.wait_for(state="visible")

        await button.scroll_into_view_if_needed()

        downloads = []

        def _on_download(download):
            downloads.append(download)

        page.on(
            "download",
            _on_download,
        )

        try:
            async with page.expect_download(timeout=30_000):
                await button.click()

            idle_ms = 0
            last_count = len(downloads)
            waited = 0

            while waited < collect_window_ms:
                await asyncio.sleep(poll_ms / 1000)

                waited += poll_ms

                if len(downloads) != last_count:
                    last_count = len(downloads)
                    idle_ms = 0

                else:
                    idle_ms += poll_ms

                    if idle_ms >= collect_window_ms:
                        break

        finally:
            page.remove_listener(
                "download",
                _on_download,
            )

        if not downloads:
            return []

        out_paths: list[Path] = []

        for index, download in enumerate(
            downloads,
            start=1,
        ):
            suggested = download.suggested_filename or f"download_{index}.bin"

            filename = f"{prefix}_{suggested}" if prefix else suggested

            out_path = save_dir / filename

            bar = DownloadProgress(desc=out_path.name)

            await bar.start(download)

            try:
                await download.save_as(str(out_path))

            finally:
                await bar.stop(final_path=out_path)

            produced: list[Path] = [out_path]

            if out_path.suffix.lower() == ".zip":
                extracted = []

                with zipfile.ZipFile(
                    out_path,
                    "r",
                ) as archive:
                    for name in archive.namelist():
                        archive.extract(
                            name,
                            path=save_dir,
                        )

                        extracted.append(save_dir / name)

                out_path.unlink(missing_ok=True)

                final_extracted: list[Path] = []

                for path in extracted:
                    if path.suffix.lower() == ".gz":
                        final_extracted.append(
                            gunzip_file(
                                path,
                                delete_original=True,
                            )
                        )
                    else:
                        final_extracted.append(path)

                produced = final_extracted

            elif out_path.suffix.lower() == ".gz":
                produced = [
                    gunzip_file(
                        out_path,
                        delete_original=True,
                    )
                ]

            out_paths.extend(produced)

        return out_paths

    def _get_nth(
        self,
        margin: Literal["Spot", "Contract"],
        data_type: Literal["Trades", "L2Book"],
    ):
        element = "Public Trading History" if data_type == "Trades" else "OrderBook"

        if margin == "Contract" and element == "Public Trading History":
            return 1

        if margin == "Spot" and element == "Public Trading History":
            return 3

        if margin == "Contract" and element == "OrderBook":
            return 4

        if margin == "Spot" and element == "OrderBook":
            return 4

        raise ValueError(f"Unsupported combination: {margin} / {data_type}")

    async def _get_symbols(
        self,
        market_type: Literal["Contract", "Spot"],
    ) -> List[str]:
        if self.page is None:
            raise RuntimeError(
                "Client not started. Use: async with BybitHistoryClient(...) as client:"
            )

        action("Finding available symbols — this may take a moment...")

        page = self.page

        # Open history page
        await page.goto(
            self.BASE_HISTORY_URL,
            timeout=100_000,
            wait_until="domcontentloaded",
        )

        await page.wait_for_timeout(2500)

        # Same redirect workaround used by downloads
        if page.url != self.BASE_HISTORY_URL:
            await page.goto(
                self.BASE_HISTORY_URL,
                timeout=100_000,
                wait_until="domcontentloaded",
            )

            await page.wait_for_timeout(2500)

        await page.wait_for_load_state(
            "networkidle",
            timeout=60_000,
        )

        # Select Spot / Contract exactly like download flow
        await self._hover(
            page,
            element="Public Trading History",
        )

        await self._attempt_click_visible_element(
            page=page,
            margin=market_type,
            nth=self._get_nth(
                margin=market_type,
                data_type="Trades",
            ),
        )

        await page.wait_for_timeout(500)

        # Open symbol dropdown using the NEW UI
        selectors = page.get_by_text(
            "please select",
            exact=True,
        )

        visible_selector = None

        for i in range(await selectors.count()):
            candidate = selectors.nth(i)

            if await candidate.is_visible():
                visible_selector = candidate
                await candidate.click()
                break

        if visible_selector is None:
            raise RuntimeError("Could not find symbol selector")

        await page.wait_for_timeout(500)

        return await self._collect_symbol_options(
            page,
            visible_selector,
        )

    @classmethod
    async def _hover(
        cls,
        page,
        element: str = "Public Trading History",
    ):
        target = page.get_by_text(
            element,
            exact=True,
        )

        box = await target.bounding_box()

        if box:
            await page.mouse.move(
                box["x"] + box["width"] * 0.5,
                box["y"] + box["height"] * 0.5,
            )

        await page.wait_for_timeout(400)

    @classmethod
    async def _attempt_click_visible_element(
        cls,
        page,
        nth,
        *,
        max_attempts: int = 20,
        delay_ms: int = 3000,
        margin: Literal["Spot", "Contract"],
    ):
        for attempt in range(
            1,
            max_attempts + 1,
        ):
            button = page.get_by_text(margin).nth(nth)

            try:
                if not await button.is_visible():
                    continue

                await button.click(timeout=2_000)

                return

            except Exception:
                print(f"[attempt {attempt}] click failed on #{nth}, retrying...")

            await page.wait_for_timeout(delay_ms)

        raise RuntimeError(f"Failed to click a visible {margin} button after retries")

    async def _collect_symbol_options(
        self,
        page,
        selector,
        max_tries: int = 300,
    ) -> List[str]:
        box = await selector.bounding_box()

        if box is None:
            raise RuntimeError("Could not determine symbol selector position")

        # Same mouse position that already works for downloading.
        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] + 150

        await page.mouse.move(
            x,
            y,
        )

        symbols: set[str] = set()
        no_new_symbols = 0

        for _ in range(max_tries):
            # Find the scrollable dropdown underneath the mouse and
            # collect text from its currently rendered option elements.
            visible_texts = await page.evaluate(
                """
                ({x, y}) => {
                    let element = document.elementFromPoint(x, y);

                    if (!element) {
                        return [];
                    }

                    let node = element;
                    let scrollable = null;

                    while (node && node !== document.body) {
                        if (
                            node.scrollHeight >
                            node.clientHeight + 5
                        ) {
                            scrollable = node;
                            break;
                        }

                        node = node.parentElement;
                    }

                    const root =
                        scrollable ||
                        element.parentElement;

                    if (!root) {
                        return [];
                    }

                    return Array.from(
                        root.querySelectorAll("*")
                    )
                        .filter(el => {
                            const rect =
                                el.getBoundingClientRect();

                            return (
                                rect.width > 0 &&
                                rect.height > 0 &&
                                el.children.length === 0
                            );
                        })
                        .map(el =>
                            (el.textContent || "").trim()
                        )
                        .filter(Boolean);
                }
                """,
                {
                    "x": x,
                    "y": y,
                },
            )

            before = len(symbols)

            for text in visible_texts:
                for value in text.splitlines():
                    value = value.strip()

                    # Symbols are uppercase market identifiers such as
                    # BTCUSDT, ETHUSDT, 1000PEPEUSDT, BTCUSD, etc.
                    if re.fullmatch(
                        r"[A-Z0-9][A-Z0-9._-]{3,30}",
                        value,
                    ):
                        symbols.add(value)

            if len(symbols) == before:
                no_new_symbols += 1
            else:
                no_new_symbols = 0

            # Enough consecutive scans without anything new usually
            # means we have reached the bottom.
            if no_new_symbols >= 20:
                break

            # IMPORTANT: same scrolling mechanism that works
            # in your download flow.
            await page.mouse.wheel(
                0,
                60,
            )

            await page.wait_for_timeout(150)

        ignored = {
            "SPOT",
            "CONTRACT",
            "TRADES",
            "ORDERBOOK",
            "EVERYDAY",
            "DOWNLOAD",
            "PUBLIC",
            "TRADING",
            "HISTORY",
        }

        return sorted(symbol for symbol in symbols if symbol not in ignored)

    async def _antd_select_option(
        self,
        page,
        *,
        symbol: str,
    ):
        selectors = page.get_by_text(
            "please select",
            exact=True,
        )

        count = await selectors.count()

        for i in range(count):
            selector = selectors.nth(i)

            if await selector.is_visible():
                await selector.click()
                break
        else:
            raise RuntimeError("Could not find a visible symbol dropdown")

        await page.wait_for_timeout(500)

        action(f"Finding {symbol} — this may take a moment...")

        found = await self._select_virtual_option(
            page,
            symbol,
        )

        if not found:
            raise RuntimeError(f"Could not find symbol after scrolling: {symbol}")

        print(f"Selected symbol: {symbol}")

        return page

    async def _select_virtual_option(
        self,
        page,
        text: str,
        max_tries: int = 100,
    ):
        for _ in range(max_tries):
            options = page.get_by_text(
                text,
                exact=True,
            )

            count = await options.count()

            for i in range(count):
                option = options.nth(i)

                if await option.is_visible():
                    await option.click()
                    return True

            # Find the visible "please select" control.
            # Its dropdown should now be open somewhere below it.
            selector = page.get_by_text(
                "please select",
                exact=True,
            )

            visible_selector = None

            for i in range(await selector.count()):
                candidate = selector.nth(i)

                if await candidate.is_visible():
                    visible_selector = candidate
                    break

            if visible_selector is None:
                raise RuntimeError("Symbol selector is no longer visible")

            box = await visible_selector.bounding_box()

            if box is None:
                raise RuntimeError("Could not determine symbol selector position")

            # Move the mouse into the open dropdown.
            x = box["x"] + box["width"] / 2
            y = box["y"] + box["height"] + 150

            await page.mouse.move(
                x,
                y,
            )

            # IMPORTANT: this is the working scrolling mechanism.
            await page.mouse.wheel(
                0,
                60,
            )

            await page.wait_for_timeout(150)

        return False

    def _print_symbols(
        self,
        label: str,
        symbols: list[str],
    ):
        from rich import box
        from rich.panel import Panel
        from rich.table import Table

        symbols = sorted(symbols)

        console.print()

        console.print(
            Panel(
                f"[bold cyan]{len(symbols)}[/bold cyan] markets available",
                title=f"[bold cyan] {label} SYMBOLS [/bold cyan]",
                border_style="cyan",
                padding=(0, 2),
            )
        )

        console.print()

        table = Table(
            box=None,
            show_header=False,
            padding=(0, 3),
            expand=True,
        )

        columns = 4

        for _ in range(columns):
            table.add_column(
                style="bold",
                no_wrap=True,
            )

        for i in range(
            0,
            len(symbols),
            columns,
        ):
            row = symbols[i : i + columns]

            while len(row) < columns:
                row.append("")

            table.add_row(*row)

        console.print(table)

        console.print(f"\n[dim]{'─' * 60}[/dim]")

        console.print(
            f"[dim]{len(symbols)} symbols[/dim] [cyan]•[/cyan] [bold]{label}[/bold]"
        )

        console.print()
