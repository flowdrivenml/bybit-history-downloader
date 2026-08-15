import pytest

from bybit_history import BybitHistoryClient


@pytest.mark.asyncio
async def test_client_context_manager():
    client = BybitHistoryClient(
        headless=True,
        browser_name="chromium",
    )

    assert client.headless is True
    assert client.browser_name == "chromium"
    assert client.page is None


def test_client_default_settings():
    client = BybitHistoryClient()

    assert client.headless is True
    assert client.browser_name == "firefox"


@pytest.mark.parametrize(
    ("margin", "data_type", "expected"),
    [
        ("Contract", "Trades", 1),
        ("Spot", "Trades", 3),
        ("Contract", "L2Book", 4),
        ("Spot", "L2Book", 4),
    ],
)
def test_get_nth(margin, data_type, expected):
    client = BybitHistoryClient()

    assert (
        client._get_nth(
            margin=margin,
            data_type=data_type,
        )
        == expected
    )


@pytest.mark.asyncio
async def test_invalid_chunk_days():
    client = BybitHistoryClient()

    with pytest.raises(ValueError):
        await client.download_data(
            margin="Spot",
            data_type="Trades",
            symbol="BTCUSDT",
            start_date="2025-01-01",
            end_date="2025-01-05",
            final_path="./data",
            chunk_days=0,
        )

    with pytest.raises(ValueError):
        await client.download_data(
            margin="Spot",
            data_type="Trades",
            symbol="BTCUSDT",
            start_date="2025-01-01",
            end_date="2025-01-05",
            final_path="./data",
            chunk_days=6,
        )
