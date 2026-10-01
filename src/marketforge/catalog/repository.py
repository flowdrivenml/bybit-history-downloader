from __future__ import annotations

from datetime import datetime
from typing import Any

from psycopg import Connection
from psycopg.types.json import Jsonb

from .models import Exchange, Instrument, InstrumentSpec


class CatalogRepository:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    # ------------------------------------------------------------------
    # Exchanges
    # ------------------------------------------------------------------

    def get_exchange(self, code: str) -> Exchange | None:
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    code,
                    name
                FROM catalog.exchanges
                WHERE code = %s
                """,
                (code,),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return Exchange(
            id=row["id"],
            code=row["code"],
            name=row["name"],
        )

    # ------------------------------------------------------------------
    # Instruments
    # ------------------------------------------------------------------

    def upsert_instrument(self, instrument: Instrument) -> int:
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO catalog.instruments (
                    exchange_id,
                    symbol,
                    instrument_type,
                    market_category,
                    base_asset,
                    quote_asset,
                    settlement_asset,
                    launch_time_ns,
                    expiry_ns,
                    strike,
                    option_type,
                    status
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s
                )
                ON CONFLICT (
                    exchange_id,
                    instrument_type,
                    market_category,
                    symbol
                )
                DO UPDATE SET
                    base_asset = EXCLUDED.base_asset,
                    quote_asset = EXCLUDED.quote_asset,
                    settlement_asset = EXCLUDED.settlement_asset,
                    launch_time_ns = EXCLUDED.launch_time_ns,
                    expiry_ns = EXCLUDED.expiry_ns,
                    strike = EXCLUDED.strike,
                    option_type = EXCLUDED.option_type,
                    status = EXCLUDED.status,
                    updated_at = NOW()
                RETURNING id
                """,
                (
                    instrument.exchange_id,
                    instrument.symbol,
                    instrument.instrument_type,
                    instrument.market_category,
                    instrument.base_asset,
                    instrument.quote_asset,
                    instrument.settlement_asset,
                    instrument.launch_time_ns,
                    instrument.expiry_ns,
                    instrument.strike,
                    instrument.option_type,
                    instrument.status,
                ),
            )

            row = cursor.fetchone()

        if row is None:
            raise RuntimeError(f"Failed to upsert instrument: {instrument.symbol}")

        return int(row["id"])

    def get_instrument(
        self,
        *,
        exchange_id: int,
        instrument_type: str,
        market_category: str,
        symbol: str,
    ) -> Instrument | None:
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    exchange_id,
                    symbol,
                    instrument_type,
                    market_category,
                    base_asset,
                    quote_asset,
                    settlement_asset,
                    launch_time_ns,
                    expiry_ns,
                    strike,
                    option_type,
                    status
                FROM catalog.instruments
                WHERE exchange_id = %s
                  AND instrument_type = %s
                  AND market_category = %s
                  AND symbol = %s
                """,
                (
                    exchange_id,
                    instrument_type,
                    market_category,
                    symbol,
                ),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return Instrument(
            id=row["id"],
            exchange_id=row["exchange_id"],
            symbol=row["symbol"],
            instrument_type=row["instrument_type"],
            market_category=row["market_category"],
            base_asset=row["base_asset"],
            quote_asset=row["quote_asset"],
            settlement_asset=row["settlement_asset"],
            launch_time_ns=row["launch_time_ns"],
            expiry_ns=row["expiry_ns"],
            strike=row["strike"],
            option_type=row["option_type"],
            status=row["status"],
        )

    # ------------------------------------------------------------------
    # Instrument specifications
    # ------------------------------------------------------------------

    def upsert_instrument_spec(
        self,
        spec: InstrumentSpec,
    ) -> None:
        if spec.instrument_id is None:
            raise ValueError(
                "instrument_id is required before persisting InstrumentSpec"
            )

        if spec.fetched_at is None:
            raise ValueError("fetched_at is required before persisting InstrumentSpec")

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO catalog.instrument_specs (
                    instrument_id,
                    quantity_type,
                    contract_value,
                    contract_value_asset,
                    tick_size,
                    qty_step,
                    min_qty,
                    max_qty,
                    min_notional,
                    fetched_at
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (instrument_id)
                DO UPDATE SET
                    quantity_type = EXCLUDED.quantity_type,
                    contract_value = EXCLUDED.contract_value,
                    contract_value_asset = EXCLUDED.contract_value_asset,
                    tick_size = EXCLUDED.tick_size,
                    qty_step = EXCLUDED.qty_step,
                    min_qty = EXCLUDED.min_qty,
                    max_qty = EXCLUDED.max_qty,
                    min_notional = EXCLUDED.min_notional,
                    fetched_at = EXCLUDED.fetched_at
                """,
                (
                    spec.instrument_id,
                    spec.quantity_type,
                    spec.contract_value,
                    spec.contract_value_asset,
                    spec.tick_size,
                    spec.qty_step,
                    spec.min_qty,
                    spec.max_qty,
                    spec.min_notional,
                    spec.fetched_at,
                ),
            )

    def get_instrument_spec(
        self,
        instrument_id: int,
    ) -> InstrumentSpec | None:
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    instrument_id,
                    quantity_type,
                    contract_value,
                    contract_value_asset,
                    tick_size,
                    qty_step,
                    min_qty,
                    max_qty,
                    min_notional,
                    fetched_at
                FROM catalog.instrument_specs
                WHERE instrument_id = %s
                """,
                (instrument_id,),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return InstrumentSpec(
            instrument_id=row["instrument_id"],
            quantity_type=row["quantity_type"],
            contract_value=row["contract_value"],
            contract_value_asset=row["contract_value_asset"],
            tick_size=row["tick_size"],
            qty_step=row["qty_step"],
            min_qty=row["min_qty"],
            max_qty=row["max_qty"],
            min_notional=row["min_notional"],
            fetched_at=row["fetched_at"],
        )

    # ------------------------------------------------------------------
    # Raw exchange metadata
    # ------------------------------------------------------------------

    def store_raw_instrument_metadata(
        self,
        *,
        instrument_id: int,
        fetched_at: datetime,
        data: dict[str, Any],
    ) -> int:
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO catalog.instrument_api_raw (
                    instrument_id,
                    fetched_at,
                    raw_json
                )
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (
                    instrument_id,
                    fetched_at,
                    Jsonb(data),
                ),
            )

            row = cursor.fetchone()

        if row is None:
            raise RuntimeError("Failed to store raw instrument metadata")

        return int(row["id"])
