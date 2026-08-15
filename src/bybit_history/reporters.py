from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from .ui import console


class DownloadProgress:
    def __init__(
        self,
        *,
        desc: str,
    ):
        self.desc = desc

        self._progress: Progress | None = None
        self._task_id: int | None = None
        self._poll_task: asyncio.Task | None = None

        self._done = asyncio.Event()
        self._last_bytes = 0

    async def start(
        self,
        download,
    ) -> None:
        try:
            total = await download.total_bytes()
        except Exception:
            total = None

        self._progress = Progress(
            SpinnerColumn(
                style="cyan",
            ),
            TextColumn("[bold]{task.description}"),
            BarColumn(
                bar_width=36,
            ),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        )

        self._progress.start()

        self._task_id = self._progress.add_task(
            self.desc,
            total=total,
        )

        self._done.clear()
        self._last_bytes = 0

        async def poll() -> None:
            while not self._done.is_set():
                try:
                    info = await download.progress()

                    current = int(info.get("bytes", 0) or 0)

                except Exception:
                    current = self._last_bytes

                self._last_bytes = current

                if self._progress is not None and self._task_id is not None:
                    self._progress.update(
                        self._task_id,
                        completed=current,
                    )

                await asyncio.sleep(0.15)

        self._poll_task = asyncio.create_task(poll())

    async def stop(
        self,
        *,
        final_path: str | Path | None = None,
    ) -> None:
        self._done.set()

        if self._poll_task is not None:
            self._poll_task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await self._poll_task

            self._poll_task = None

        if self._progress is not None and self._task_id is not None:
            if final_path is not None:
                path = Path(final_path)

                try:
                    size = path.stat().st_size

                    self._progress.update(
                        self._task_id,
                        total=size,
                        completed=size,
                    )

                except OSError:
                    pass

            self._progress.stop()

        self._progress = None
        self._task_id = None

