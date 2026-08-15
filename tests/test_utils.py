import pytest

from bybit_history.utils import split_date_range


def test_split_date_range():
    result = split_date_range(
        "2025-01-01",
        "2025-01-12",
        5,
    )

    assert result == [
        ("2025-01-01", "2025-01-05"),
        ("2025-01-06", "2025-01-10"),
        ("2025-01-11", "2025-01-12"),
    ]


def test_split_single_day():
    result = split_date_range(
        "2025-01-01",
        "2025-01-01",
        5,
    )

    assert result == [
        ("2025-01-01", "2025-01-01"),
    ]


def test_invalid_date_order():
    with pytest.raises(ValueError):
        split_date_range(
            "2025-01-10",
            "2025-01-01",
            5,
        )


def test_invalid_chunk_size():
    with pytest.raises(ValueError):
        split_date_range(
            "2025-01-01",
            "2025-01-10",
            0,
        )


def test_invalid_date_format():
    with pytest.raises(ValueError):
        split_date_range(
            "01-01-2025",
            "2025-01-10",
            5,
        )
