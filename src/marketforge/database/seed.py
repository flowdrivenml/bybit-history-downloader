from __future__ import annotations

from psycopg import Connection

EXCHANGES = (
    ("bybit", "Bybit"),
    ("binance", "Binance"),
    ("okx", "OKX"),
    ("bitget", "Bitget"),
    ("gateio", "Gate.io"),
)


def seed_exchanges(conn: Connection) -> None:
    """
    Insert the exchanges supported by MarketForge.

    Safe to run repeatedly.
    """
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO catalog.exchanges (
                code,
                name
            )
            VALUES (%s, %s)
            ON CONFLICT (code)
            DO UPDATE SET
                name = EXCLUDED.name
            """,
            EXCHANGES,
        )


def seed_database(conn: Connection) -> None:
    """
    Seed static MarketForge-owned database data.
    """
    seed_exchanges(conn)
