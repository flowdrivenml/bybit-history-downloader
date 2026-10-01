from __future__ import annotations

from psycopg import Connection

SCHEMA_VERSION = 1


DDL = """
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS live;


CREATE TABLE IF NOT EXISTS catalog.schema_meta (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS catalog.exchanges (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS catalog.instruments (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    exchange_id         BIGINT NOT NULL
                            REFERENCES catalog.exchanges(id),

    symbol              TEXT NOT NULL,

    instrument_type     TEXT NOT NULL,
    market_category     TEXT NOT NULL,

    base_asset          TEXT,
    quote_asset         TEXT,
    settlement_asset    TEXT,

    launch_time_ns      BIGINT,
    expiry_ns           BIGINT,

    strike              NUMERIC,
    option_type         TEXT,

    status              TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (
        exchange_id,
        instrument_type,
        market_category,
        symbol
    )
);


CREATE TABLE IF NOT EXISTS catalog.instrument_specs (
    instrument_id          BIGINT PRIMARY KEY
                               REFERENCES catalog.instruments(id)
                               ON DELETE CASCADE,

    quantity_type          TEXT NOT NULL,

    contract_value         NUMERIC,
    contract_value_asset   TEXT,

    tick_size              NUMERIC,
    qty_step               NUMERIC,
    min_qty                NUMERIC,
    max_qty                NUMERIC,
    min_notional           NUMERIC,

    fetched_at             TIMESTAMPTZ NOT NULL
);


CREATE TABLE IF NOT EXISTS catalog.instrument_api_raw (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    instrument_id   BIGINT NOT NULL
                        REFERENCES catalog.instruments(id)
                        ON DELETE CASCADE,

    fetched_at      TIMESTAMPTZ NOT NULL,
    raw_json        JSONB NOT NULL
);


CREATE INDEX IF NOT EXISTS idx_instruments_exchange
    ON catalog.instruments(exchange_id);


CREATE INDEX IF NOT EXISTS idx_instruments_symbol
    ON catalog.instruments(symbol);


CREATE INDEX IF NOT EXISTS idx_instrument_api_raw_instrument
    ON catalog.instrument_api_raw(instrument_id);


CREATE INDEX IF NOT EXISTS idx_instrument_api_raw_fetched
    ON catalog.instrument_api_raw(instrument_id, fetched_at DESC);
"""


def initialize_schema(conn: Connection) -> None:
    """
    Create the MarketForge PostgreSQL schemas and tables.

    The current schema version is recorded in catalog.schema_meta.
    """
    with conn.cursor() as cursor:
        cursor.execute(DDL)

        cursor.execute("""
            SELECT value
            FROM catalog.schema_meta
            WHERE key = 'schema_version'
            """)

        row = cursor.fetchone()

        if row is None:
            cursor.execute(
                """
                INSERT INTO catalog.schema_meta (key, value)
                VALUES ('schema_version', %s)
                """,
                (str(SCHEMA_VERSION),),
            )
            return

        version = int(row["value"])

        if version != SCHEMA_VERSION:
            raise RuntimeError(
                "Unsupported MarketForge database schema version: "
                f"{version}; expected {SCHEMA_VERSION}"
            )
