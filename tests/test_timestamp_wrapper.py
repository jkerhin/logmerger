"""Initial suite of timestamp parsing tests

TODO: `BDHMS` requires a file that populates `stat` attributes...
"""
from datetime import datetime

import pytest

from logmerger.timestamp_wrapper import TimestampedLineTransformer


EXPECTED_DATETIME = datetime(
    year=2023, month=7, day=14, hour=14, minute=13, second=0, microsecond=100_000
)


@pytest.mark.parametrize(
    "input,expected",
    [
        ("2023-07-14 14:13:00,100 message", EXPECTED_DATETIME),
        ("2023-07-14T14:13:00,100 message", EXPECTED_DATETIME),
        ("2023-07-14 14:13:00.100 message", EXPECTED_DATETIME),
        ("2023-07-14T14:13:00.100 message", EXPECTED_DATETIME),
        ("2023-07-14 14:13:00 message", EXPECTED_DATETIME.replace(microsecond=0)),
        ("2023-07-14T14:13:00 message", EXPECTED_DATETIME.replace(microsecond=0)),
        (
            '::1 - - [14/Jul/2023 14:13:00] "GET /log1.txt HTTP/1.1" 200 -',
            EXPECTED_DATETIME.replace(microsecond=0),
        ),
        ("1689343980.100 message", EXPECTED_DATETIME),
        ("1689343980.100000 message", EXPECTED_DATETIME),
        ("1689343980100 message", EXPECTED_DATETIME),
        ("1689343980 message", EXPECTED_DATETIME.replace(microsecond=0)),
    ],
)
def test_transformer_naive(input, expected):
    transformer = TimestampedLineTransformer.make_transformer_from_sample_line(input)
    timestamp, _ = transformer(input)
    assert timestamp == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        (
            "2023-07-14 14:13:00,100Z message",
            EXPECTED_DATETIME,
        ),
        (
            "2023-07-14 14:13:00,100+00:00 message",
            EXPECTED_DATETIME,
        ),
        (
            "2023-07-14T14:13:00,100Z message",
            EXPECTED_DATETIME,
        ),
        (
            "2023-07-14T14:13:00,100+00:00 message",
            EXPECTED_DATETIME,
        ),
        (
            "2023-07-14 14:13:00.100Z message",
            EXPECTED_DATETIME,
        ),
        (
            "2023-07-14 14:13:00.100+00:00 message",
            EXPECTED_DATETIME,
        ),
        (
            "2023-07-14T14:13:00.100Z message",
            EXPECTED_DATETIME,
        ),
        (
            "2023-07-14T14:13:00.100+00:00 message",
            EXPECTED_DATETIME,
        ),
        ("2023-07-14 14:13:00Z message", EXPECTED_DATETIME.replace(microsecond=0)),
        ("2023-07-14 14:13:00+00:00 message", EXPECTED_DATETIME.replace(microsecond=0)),
        ("2023-07-14 14:13:00+0000 message", EXPECTED_DATETIME.replace(microsecond=0)),
        ("2023-07-14T14:13:00Z message", EXPECTED_DATETIME.replace(microsecond=0)),
        ("2023-07-14T14:13:00+00:00 message", EXPECTED_DATETIME.replace(microsecond=0)),
        ("2023-07-14T14:13:00+0000 message", EXPECTED_DATETIME.replace(microsecond=0)),
        # (
        #     '91.194.60.14 - - [14/Jul/2023 14:13:00 +0000] "GET /python_nutshell_app_a_search HTTP/1.1" 200 1027 "-"',
        #     EXPECTED_DATETIME.replace(microsecond=0)
        #  )
    ],
)
def test_transformer_aware(input, expected):
    transformer = TimestampedLineTransformer.make_transformer_from_sample_line(input)
    timestamp, _ = transformer(input)
    assert timestamp == expected
