from datetime import datetime, timezone

import dateutil.tz

import dateutil.parser as dp


def unix_to_utc(unix):
    return datetime.utcfromtimestamp(unix)


def utc_to_iso(utc):
    return utc.isoformat()


def unix_to_iso(unix):
    return utc_to_iso(unix_to_utc(unix))


def iso_to_unix(iso):
    return int(dp.parse(iso).replace(tzinfo=timezone.utc).timestamp())


def utc_date_to_unix(utc_date):
    return int(utc_date.replace(tzinfo=timezone.utc).timestamp())


def local_date_to_utc_date(local_date):
    return local_date.astimezone(dateutil.tz.tzutc())


def local_date_to_unix(local_date):
    utc_date = local_date_to_utc_date(local_date)
    return utc_date_to_unix(utc_date)


def dict_to_local_date(date_dict):
    local_date = datetime(
        year=date_dict['year'],
        month=date_dict['month'],
        day=date_dict['day'],
        hour=date_dict['hour'],
        minute=date_dict['minute'],
        tzinfo=dateutil.tz.tzlocal())
    return local_date


def dict_to_utc_date(date_dict):
    local_date = datetime(
        year=date_dict['year'],
        month=date_dict['month'],
        day=date_dict['day'],
        hour=date_dict['hour'],
        minute=date_dict['minute'],
        tzinfo=dateutil.tz.tzutc())
    return local_date
