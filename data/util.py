from datetime import datetime, timezone
import dateutil.parser as dp


def unix_to_utc(unix):
    return datetime.utcfromtimestamp(unix)


def utc_to_iso(utc):
    return utc.isoformat()


def unix_to_iso(unix):
    return utc_to_iso(unix_to_utc(unix))


def iso_to_unix(iso):
    return int(dp.parse(iso).replace(tzinfo=timezone.utc).timestamp())


def date_to_unix(date):
    return int(date.replace(tzinfo=timezone.utc).timestamp())