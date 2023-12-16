from __future__ import annotations

import os
import sys
import string
from datetime import datetime
from functools import partial
from pathlib import Path
import re
from typing import Callable, TypeVar, Union

if sys.version_info.minor < 11:
    from dateutil.parser import isoparse as fromisoformat
else:
    fromisoformat = datetime.fromisoformat

T = TypeVar("T")
TimestampFormatter = Union[Union[str, Callable[[str], datetime]]]

strip_escape_sequences = partial(re.compile("\x1b" + r"\[\d+(;\d+)*m").sub, "")


class TimestampedLineTransformer:
    """
    Class to detect timestamp formats, and auto-transform lines that start with that timestamp into
    (timestamp, rest of the line) tuples.
    """
    pattern = ""
    timestamp_pattern = ""
    timestamp_match_group = 2
    sub_repl = ""
    strptime_format = ""
    match = lambda s: False
    has_timezone = False

    custom_transformers = []
    custom_transformer_suffixes = iter(string.ascii_uppercase)

    def __init_subclass__(cls):
        cls.match = re.compile(cls.pattern, re.VERBOSE).match

    @staticmethod
    def _get_first_line_of_file(file_ref) -> str:
        if isinstance(file_ref, (str, Path)):
            with open(file_ref) as log_file:
                first_line = log_file.readline()
        else:
            first_line = file_ref.readline()
        return first_line

    @classmethod
    def make_transformer_from_file(cls, file_ref) -> TimestampedLineTransformer:
        first_line = cls._get_first_line_of_file(file_ref)
        xformer = cls.make_transformer_from_sample_line(first_line)
        xformer.add_file_info(Path(file_ref))
        return xformer

    @classmethod
    def make_transformer_from_sample_line(cls, s: str) -> TimestampedLineTransformer:
        for subcls in cls.__subclasses__():
            if subcls.match(s):
                return subcls()
        raise ValueError(f"no match for any timestamp pattern in {s!r}")

    @classmethod
    def make_custom_transformers(cls, custom_timestamp: str) -> None:
        r"""
        Given an input string template with ... placeholder for the timestamp format,
        create TimestampedLineTransformer subclasses that match the template and
        preserve leading text if desired.

        String templates are regular expressions, with the exception that in place of
        the regex for the actual timestamp, the template should contain "(...)". This
        function will use the existing subclasses of TimestampedLineTransformer to
        capture timestamp format regex and their corresponding strptime strings.

        The template will have the form of:

            ((...)x)
        or
            (leading)((...)x)
        where `x` can be any trailing space or delimiter that follows the timestamp, and
        `leading` can be a regex fragment for any leading text that comes before the timestamp.
        The template performs 3 functions:
        - (...) will create a capture group containing the actual timestamp value
        - ((...)x) will define a capture group for text that will be removed from the log line
          before adding it to the table (so that timestamps do not get duplicated in the
          timestamp column _and_ in the log text itself
        - (leading) defines a capture group that comes before the timestamp, and which should
          be preserved in the presented log line

        Here are some example log lines and suggested format templates:

            Log line                                  Template
            INFO - 2022-01-01 12:34:56 log message    (\w+ - )((...) )
            [INFO] 2022-01-01 12:34:56 log message    (\[\w+\] )((...) )
            [2022-01-01 12:34:56|INFO] log message    (\[)((...)|)

        """

        # template must include "(...)" placeholder somewhere
        if "(...)" not in custom_timestamp:
            raise ValueError(f"custom timestamp format '{custom_timestamp}' must contain '(...)' placeholder")

        has_initial_content = "..." not in custom_timestamp[:custom_timestamp.find(")")]
        for subcls in TimestampedLineTransformer.__subclasses__():
            if subcls in TimestampedLineTransformer.custom_transformers:
                continue

            custom_timestamp_pattern = custom_timestamp.replace("...", subcls.timestamp_pattern)
            class_properties = {
                "pattern": custom_timestamp_pattern,
                "timestamp_pattern": subcls.pattern,
                "timestamp_match_group": 3 if has_initial_content else 2,
                "sub_repl": r"\1" if has_initial_content else "",
                "strptime_format": subcls.strptime_format,
            }

            name_suffix = next(cls.custom_transformer_suffixes)
            TimestampedLineTransformer.custom_transformers.append(
                type(
                    f"Custom{subcls.__name__}_{name_suffix}",
                    (subcls, TimestampedLineTransformer,),
                    class_properties
                )
            )

    def __init__(self, pattern: str, strptime_formatter: TimestampFormatter):
        self._re_pattern_match = re.compile(pattern, re.VERBOSE).match
        self._re_pattern_sub = partial(re.compile(pattern, re.VERBOSE).sub, count=1)
        self.pattern: str = pattern

        if isinstance(strptime_formatter, str):
            self.str_to_time = lambda s: datetime.strptime(s, strptime_formatter)
        else:
            self.str_to_time = strptime_formatter

        self.file_info: Path = None  # noqa
        self.file_stat: os.stat_result = None  # noqa

    def add_file_info(self, file_info: Path):
        self.file_info = file_info
        self.file_stat = file_info.stat()
        return self

    def __call__(self, obj: T) -> tuple[datetime | None, T]:
        m = self._re_pattern_match(obj)
        if m:
            # create (datetime, str) tuple - clip leading datetime string from
            # the log string, so that it doesn't duplicate when presented
            trimmed_obj = self._re_pattern_sub(self.sub_repl, obj).rstrip()
            ret = self.str_to_time(m[self.timestamp_match_group]), trimmed_obj
        else:
            # no leading timestamp, just return None and the original string
            ret = None, f" {obj}"

        # remove escape sequences, which throw off the tabularization of output
        # (consider replacing with rich tags)
        if self.has_timezone and ret[0] is not None:
            return ret[0].replace(tzinfo=None), strip_escape_sequences(ret[1]).rstrip()
        else:
            return ret[0], strip_escape_sequences(ret[1]).rstrip()


class ISOFormat(TimestampedLineTransformer):
    """Valid ISO-8601 formatted timestamps

    Note that because all timestamps are being cast to naive datetimes, we can force
    'has_timezone' to true with no detrimental effects

    Note also that this regex will not reject invalid datetimes - it will match on invalid
    dates/times like "2023-23-99 55:99:88"
    """
    pattern = r"""(  # Begin timestamp + message group
        (      # Begin timestamp capture group
        \d{4}  # Year
        -?     # Optional separator
        \d{2}  # Month
        -?     # Optional separator
        \d{2}  # Day
        [T\s]? # Optional separator
        \d{2}  # Hour
        :?     # Optional separator
        \d{2}  # Minute
        :?     # Optional separator
        \d{2}  # Second
        (?:[,.]\d+)?  # Optionally, include sub-second precision and separator
        (?:Z|[+-]\d{2}:?(?:\d{2})?)?  # Optionally, timezone offset
        )      # End timestamp capture group
    \s) # End timestamp + message group"""
    strptime_format = fromisoformat
    has_timezone = True

    def __init__(self):
        super().__init__(self.pattern, self.strptime_format)


class BDHMS(TimestampedLineTransformer):
    # syslog files with timestamp "mon day hh:mm:ss"
    # (note, year is omitted so let's guess from the log file's create date)
    timestamp_pattern = r"[JFMASOND][a-z]{2}\s(\s|\d)\d\s\d{2}:\d{2}:\d{2}"
    pattern = fr"(({timestamp_pattern})\s)"
    strptime_format = "%b %d %H:%M:%S"

    def __init__(self):
        super().__init__(self.pattern, self.strptime_format)

    def __call__(self, obj: T) -> tuple[datetime | None, T]:
        # this format does not have a year so assume the file's create time year
        if self.file_stat is not None and self.file_stat.st_ctime:
            date_year = datetime.fromtimestamp(self.file_stat.st_ctime).year
        else:
            date_year = datetime.now().year

        dt, obj = super().__call__(obj)
        if dt is not None:
            dt = dt.replace(year=date_year)
        return dt, obj


class PythonHttpServerLog(TimestampedLineTransformer):
    # ::1 - - [22/Sep/2023 21:58:40] "GET /log1.txt HTTP/1.1" 200 -
    timestamp_pattern = r"\d{2}\/\w+\/\d{4}\s\d{2}:\d{2}:\d{2}"
    pattern = fr"(.*)(-\s\[({timestamp_pattern})\]\s)"
    strptime_format = "%d/%b/%Y %H:%M:%S"
    timestamp_match_group = 3
    sub_repl = r"\1"

    def __init__(self):
        super().__init__(self.pattern, self.strptime_format)


class HttpServerAccessLog(TimestampedLineTransformer):
    # 91.194.60.14 - - [16/Sep/2023:19:05:06 +0000] "GET /python_nutshell_app_a_search HTTP/1.1" 200 1027 "-"
    #   "http.rb/5.1.1 (Mastodon/4.1.3; +https://mamot.fr/) Bot" "91.194.60.14" response-time=0.002
    timestamp_pattern = r"\d{2}\/\w+\/\d{4}:\d{2}:\d{2}:\d{2}\s[+-]\d{4}"
    pattern = fr"(.*)(-\s\[({timestamp_pattern})\]\s)"
    strptime_format = "%d/%b/%Y:%H:%M:%S %z"
    timestamp_match_group = 3
    sub_repl = r"\1"

    def __init__(self):
        super().__init__(
            self.pattern,
            lambda s: datetime.strptime(s, self.strptime_format).replace(tzinfo=None)
        )


class FloatSecondsSinceEpoch(TimestampedLineTransformer):
    # log files with timestamp "1694561169.550987" or "1694561169.550"
    timestamp_pattern = r"\d{10}\.\d+"
    pattern = fr"(({timestamp_pattern})\s)"

    def __init__(self):
        super().__init__(self.pattern, lambda s: datetime.fromtimestamp(float(s)))


class MilliSecondsSinceEpoch(TimestampedLineTransformer):
    # log files with 13-digit timestamp "1694561169550"
    timestamp_pattern = r"\d{13}"
    pattern = fr"(({timestamp_pattern})\s)"

    def __init__(self):
        super().__init__(self.pattern, lambda s: datetime.fromtimestamp(int(s) / 1000))


class SecondsSinceEpoch(TimestampedLineTransformer):
    # log files with 10-digit timestamp "1694561169"
    timestamp_pattern = r"\d{10}"
    pattern = fr"(({timestamp_pattern})\s)"

    def __init__(self):
        super().__init__(self.pattern, lambda s: datetime.fromtimestamp(int(s)))


if __name__ == '__main__':
    files = "log1.txt log3.txt syslog1.txt".split()
    file_dir = Path(__file__).parent.parent / "files"
    xformers = [TimestampedLineTransformer.make_transformer_from_file(file_dir / f) for f in files]
    for fname, xform in zip(files, xformers):
        log_lines = (file_dir / fname).read_text().splitlines()
        for ln in log_lines[:3]:
            print(xform(ln))
