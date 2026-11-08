"""Convert a strictly formatted, offset-aware timestamp to UTC."""
import argparse
from datetime import datetime, timezone
import re


TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?"
    r"(?:Z|[+-](?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}))"
)


def to_utc(value: str) -> str:
    match = TIMESTAMP.fullmatch(value)
    if not match:
        raise ValueError("use YYYY-MM-DDTHH:MM:SS[.ffffff] with Z or an explicit ±HH:MM offset")
    if match["hour"] is not None and (int(match["hour"]) > 23 or int(match["minute"]) > 59):
        raise ValueError("offset hours must be 00–23 and minutes 00–59")
    try:
        instant = datetime.fromisoformat(value).astimezone(timezone.utc)
    except (ValueError, OverflowError) as exc:
        raise ValueError("timestamp has an invalid date/time or converts outside years 0001–9999") from exc
    precision = "microseconds" if instant.microsecond else "seconds"
    return instant.isoformat(timespec=precision).removesuffix("+00:00") + "Z"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("timestamp", help="YYYY-MM-DDTHH:MM:SS[.ffffff] followed by Z or ±HH:MM")
    args = parser.parse_args(argv)
    try:
        output = to_utc(args.timestamp)
    except ValueError as exc:
        parser.error(str(exc))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
