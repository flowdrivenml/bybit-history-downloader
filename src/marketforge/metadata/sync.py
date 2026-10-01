from __future__ import annotations

from dataclasses import replace

from marketforge.catalog.repository import CatalogRepository
from marketforge.providers.binance.inverse import (
    get_inverse_metadata as get_binance_inverse_metadata,
)
from marketforge.providers.binance.linear import (
    get_linear_metadata as get_binance_linear_metadata,
)
from marketforge.providers.binance.spot import (
    get_spot_metadata as get_binance_spot_metadata,
)
from marketforge.providers.bybit.inverse import get_inverse_metadata
from marketforge.providers.bybit.linear import get_linear_metadata
from marketforge.providers.bybit.option import get_option_metadata
from marketforge.providers.bybit.spot import get_spot_metadata
from marketforge.providers.okx.futures import (
    get_futures_metadata as get_okx_futures_metadata,
)
from marketforge.providers.okx.option import (
    get_option_metadata as get_okx_option_metadata,
)
from marketforge.providers.okx.spot import get_spot_metadata as get_okx_spot_metadata
from marketforge.providers.okx.swap import get_swap_metadata as get_okx_swap_metadata


def sync_bybit_spot(
    repo: CatalogRepository,
) -> int:
    exchange = repo.get_exchange("bybit")

    if exchange is None or exchange.id is None:
        raise RuntimeError(
            "Bybit is not present in catalog.exchanges. "
            "Initialize and seed the database first."
        )

    metadata = get_spot_metadata(
        exchange_id=exchange.id,
    )

    for item in metadata:
        instrument_id = repo.upsert_instrument(item.instrument)

        spec = replace(
            item.spec,
            instrument_id=instrument_id,
        )

        repo.upsert_instrument_spec(spec)

        if spec.fetched_at is None:
            raise RuntimeError("Bybit instrument metadata has no fetched_at timestamp.")

        repo.store_raw_instrument_metadata(
            instrument_id=instrument_id,
            fetched_at=spec.fetched_at,
            data=item.raw,
        )

    return len(metadata)


def sync_bybit_linear(
    repo: CatalogRepository,
) -> int:
    exchange = repo.get_exchange("bybit")

    if exchange is None or exchange.id is None:
        raise RuntimeError(
            "Bybit is not present in catalog.exchanges. "
            "Initialize and seed the database first."
        )

    metadata = get_linear_metadata(
        exchange_id=exchange.id,
    )

    for item in metadata:
        instrument_id = repo.upsert_instrument(item.instrument)

        spec = replace(
            item.spec,
            instrument_id=instrument_id,
        )

        repo.upsert_instrument_spec(spec)

        if spec.fetched_at is None:
            raise RuntimeError("Bybit instrument metadata has no fetched_at timestamp.")

        repo.store_raw_instrument_metadata(
            instrument_id=instrument_id,
            fetched_at=spec.fetched_at,
            data=item.raw,
        )

    return len(metadata)


def sync_bybit_inverse(
    repo: CatalogRepository,
) -> int:
    exchange = repo.get_exchange("bybit")

    if exchange is None or exchange.id is None:
        raise RuntimeError(
            "Bybit is not present in catalog.exchanges. "
            "Initialize and seed the database first."
        )

    metadata = get_inverse_metadata(
        exchange_id=exchange.id,
    )

    for item in metadata:
        instrument_id = repo.upsert_instrument(item.instrument)

        spec = replace(
            item.spec,
            instrument_id=instrument_id,
        )

        repo.upsert_instrument_spec(spec)

        if spec.fetched_at is None:
            raise RuntimeError("Bybit instrument metadata has no fetched_at timestamp.")

        repo.store_raw_instrument_metadata(
            instrument_id=instrument_id,
            fetched_at=spec.fetched_at,
            data=item.raw,
        )

    return len(metadata)


def sync_bybit_options(
    repo: CatalogRepository,
) -> int:
    exchange = repo.get_exchange("bybit")

    if exchange is None or exchange.id is None:
        raise RuntimeError(
            "Bybit is not present in catalog.exchanges. "
            "Initialize and seed the database first."
        )

    metadata = get_option_metadata(
        exchange_id=exchange.id,
    )

    for item in metadata:
        instrument_id = repo.upsert_instrument(item.instrument)

        spec = replace(
            item.spec,
            instrument_id=instrument_id,
        )

        repo.upsert_instrument_spec(spec)

        if spec.fetched_at is None:
            raise RuntimeError("Bybit instrument metadata has no fetched_at timestamp.")

        repo.store_raw_instrument_metadata(
            instrument_id=instrument_id,
            fetched_at=spec.fetched_at,
            data=item.raw,
        )

    return len(metadata)


def sync_okx_spot(
    repo: CatalogRepository,
) -> int:
    exchange = repo.get_exchange("okx")

    if exchange is None or exchange.id is None:
        raise RuntimeError(
            "OKX is not present in catalog.exchanges. "
            "Initialize and seed the database first."
        )

    metadata = get_okx_spot_metadata(
        exchange_id=exchange.id,
    )

    for item in metadata:
        instrument_id = repo.upsert_instrument(item.instrument)

        spec = replace(
            item.spec,
            instrument_id=instrument_id,
        )

        repo.upsert_instrument_spec(spec)

        if spec.fetched_at is None:
            raise RuntimeError("OKX instrument metadata has no fetched_at timestamp.")

        repo.store_raw_instrument_metadata(
            instrument_id=instrument_id,
            fetched_at=spec.fetched_at,
            data=item.raw,
        )

    return len(metadata)


def sync_okx_swap(
    repo: CatalogRepository,
) -> int:
    exchange = repo.get_exchange("okx")

    if exchange is None or exchange.id is None:
        raise RuntimeError(
            "OKX is not present in catalog.exchanges. "
            "Initialize and seed the database first."
        )

    metadata = get_okx_swap_metadata(
        exchange_id=exchange.id,
    )

    for item in metadata:
        instrument_id = repo.upsert_instrument(item.instrument)

        spec = replace(
            item.spec,
            instrument_id=instrument_id,
        )

        repo.upsert_instrument_spec(spec)

        if spec.fetched_at is None:
            raise RuntimeError("OKX instrument metadata has no fetched_at timestamp.")

        repo.store_raw_instrument_metadata(
            instrument_id=instrument_id,
            fetched_at=spec.fetched_at,
            data=item.raw,
        )

    return len(metadata)


def sync_okx_futures(
    repo: CatalogRepository,
) -> int:
    exchange = repo.get_exchange("okx")

    if exchange is None or exchange.id is None:
        raise RuntimeError(
            "OKX is not present in catalog.exchanges. "
            "Initialize and seed the database first."
        )

    metadata = get_okx_futures_metadata(
        exchange_id=exchange.id,
    )

    for item in metadata:
        instrument_id = repo.upsert_instrument(item.instrument)

        spec = replace(
            item.spec,
            instrument_id=instrument_id,
        )

        repo.upsert_instrument_spec(spec)

        if spec.fetched_at is None:
            raise RuntimeError("OKX instrument metadata has no fetched_at timestamp.")

        repo.store_raw_instrument_metadata(
            instrument_id=instrument_id,
            fetched_at=spec.fetched_at,
            data=item.raw,
        )

    return len(metadata)


def sync_okx_options(
    repo: CatalogRepository,
) -> int:
    exchange = repo.get_exchange("okx")

    if exchange is None or exchange.id is None:
        raise RuntimeError(
            "OKX is not present in catalog.exchanges. "
            "Initialize and seed the database first."
        )

    metadata = get_okx_option_metadata(
        exchange_id=exchange.id,
    )

    for item in metadata:
        instrument_id = repo.upsert_instrument(item.instrument)

        spec = replace(
            item.spec,
            instrument_id=instrument_id,
        )

        repo.upsert_instrument_spec(spec)

        if spec.fetched_at is None:
            raise RuntimeError("OKX instrument metadata has no fetched_at timestamp.")

        repo.store_raw_instrument_metadata(
            instrument_id=instrument_id,
            fetched_at=spec.fetched_at,
            data=item.raw,
        )

    return len(metadata)


def sync_binance_spot(
    repo: CatalogRepository,
) -> int:
    exchange = repo.get_exchange("binance")

    if exchange is None or exchange.id is None:
        raise RuntimeError(
            "Binance is not present in catalog.exchanges. "
            "Initialize and seed the database first."
        )

    metadata = get_binance_spot_metadata(
        exchange_id=exchange.id,
    )

    for item in metadata:
        instrument_id = repo.upsert_instrument(item.instrument)

        spec = replace(
            item.spec,
            instrument_id=instrument_id,
        )

        repo.upsert_instrument_spec(spec)

        if spec.fetched_at is None:
            raise RuntimeError(
                "Binance instrument metadata has no fetched_at timestamp."
            )

        repo.store_raw_instrument_metadata(
            instrument_id=instrument_id,
            fetched_at=spec.fetched_at,
            data=item.raw,
        )

    return len(metadata)


def sync_binance_linear(
    repo: CatalogRepository,
) -> int:
    exchange = repo.get_exchange("binance")

    if exchange is None or exchange.id is None:
        raise RuntimeError(
            "Binance is not present in catalog.exchanges. "
            "Initialize and seed the database first."
        )

    metadata = get_binance_linear_metadata(
        exchange_id=exchange.id,
    )

    for item in metadata:
        instrument_id = repo.upsert_instrument(item.instrument)

        spec = replace(
            item.spec,
            instrument_id=instrument_id,
        )

        repo.upsert_instrument_spec(spec)

        if spec.fetched_at is None:
            raise RuntimeError(
                "Binance instrument metadata has no " "fetched_at timestamp."
            )

        repo.store_raw_instrument_metadata(
            instrument_id=instrument_id,
            fetched_at=spec.fetched_at,
            data=item.raw,
        )

    return len(metadata)


def sync_binance_inverse(
    repo: CatalogRepository,
) -> int:
    exchange = repo.get_exchange("binance")

    if exchange is None or exchange.id is None:
        raise RuntimeError(
            "Binance is not present in catalog.exchanges. "
            "Initialize and seed the database first."
        )

    metadata = get_binance_inverse_metadata(
        exchange_id=exchange.id,
    )

    for item in metadata:
        instrument_id = repo.upsert_instrument(item.instrument)

        spec = replace(
            item.spec,
            instrument_id=instrument_id,
        )

        repo.upsert_instrument_spec(spec)

        if spec.fetched_at is None:
            raise RuntimeError(
                "Binance instrument metadata has no " "fetched_at timestamp."
            )

        repo.store_raw_instrument_metadata(
            instrument_id=instrument_id,
            fetched_at=spec.fetched_at,
            data=item.raw,
        )

    return len(metadata)
