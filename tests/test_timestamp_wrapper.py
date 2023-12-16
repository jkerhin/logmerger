"""Initial suite of timestamp parsing tests"""
from pathlib import Path
from datetime import datetime

from freezegun import freeze_time
import pytest

from logmerger.timestamp_wrapper import TimestampedLineTransformer


EXPECTED_DATETIME = datetime(
    year=2023, month=7, day=14, hour=14, minute=13, second=0, microsecond=100_000
)


@pytest.mark.parametrize(
    "line_in,expected",
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
    ],
)
def test_transformer_naive(line_in, expected):
    transformer = TimestampedLineTransformer.make_transformer_from_sample_line(line_in)
    timestamp, _ = transformer(line_in)
    assert timestamp == expected


@pytest.mark.parametrize(
    "line_in,expected",
    [
        ("1689343980.100 message", EXPECTED_DATETIME),
        ("1689343980.100000 message", EXPECTED_DATETIME),
        ("1689343980100 message", EXPECTED_DATETIME),
        ("1689343980 message", EXPECTED_DATETIME.replace(microsecond=0)),
    ],
)
@freeze_time(tz_offset=0)
def test_transformer_timestamp(line_in, expected):
    transformer = TimestampedLineTransformer.make_transformer_from_sample_line(line_in)
    timestamp, _ = transformer(line_in)
    assert timestamp == expected


@pytest.mark.parametrize(
    "line_in,expected",
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
        (
            "2023-07-14T14:13:00.100+0000 message",
            EXPECTED_DATETIME,
        ),
        (
            "2023-07-14T14:13:00.100+00 message",
            EXPECTED_DATETIME,
        ),
        ("2023-07-14 14:13:00Z message", EXPECTED_DATETIME.replace(microsecond=0)),
        ("2023-07-14 14:13:00+00:00 message", EXPECTED_DATETIME.replace(microsecond=0)),
        ("2023-07-14 14:13:00+0000 message", EXPECTED_DATETIME.replace(microsecond=0)),
        ("2023-07-14T14:13:00Z message", EXPECTED_DATETIME.replace(microsecond=0)),
        ("2023-07-14T14:13:00+00:00 message", EXPECTED_DATETIME.replace(microsecond=0)),
        ("2023-07-14T14:13:00+0000 message", EXPECTED_DATETIME.replace(microsecond=0)),
    ],
)
def test_transformer_aware(line_in, expected):
    transformer = TimestampedLineTransformer.make_transformer_from_sample_line(line_in)
    timestamp, _ = transformer(line_in)
    assert timestamp == expected


def test_syslog(test_data_root: Path):
    """The 'BDHS' parser (syslog) depends on having a file (not just a text stream)

    The file info is used to populate the timestamp year, as the year isn't populated in
    the default syslog output.

    """
    syslog_file = test_data_root / "syslog1.txt"
    with syslog_file.open("r") as hdl:
        first_line = hdl.readline()

    transformer = TimestampedLineTransformer.make_transformer_from_file(syslog_file)
    timestamp, _ = transformer(first_line)
    assert timestamp == datetime(
        year=2023, month=7, day=14, hour=8, minute=0, second=2, microsecond=0
    )


def test_accesslog():
    lines_in = """91.194.60.14 - - [14/Jul/2023:14:13:00 +0000] "GET /python_nutshell_app_a_search HTTP/1.1" 200 1027 "-"
      "http.rb/5.1.1 (Mastodon/4.1.3; +https://mamot.fr/) Bot" "91.194.60.14" response-time=0.002"""
    transformer = TimestampedLineTransformer.make_transformer_from_sample_line(lines_in)
    timestamp, _ = transformer(lines_in)
    assert timestamp == EXPECTED_DATETIME.replace(microsecond=0)
