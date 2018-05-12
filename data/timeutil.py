from datetime import datetime
from dateutil import parser
from dateutil import tz


def unix_to_iso(unix):
    return utc_date_to_iso(unix_to_utc_date(unix))


def unix_to_utc_date(unix):
    return datetime.utcfromtimestamp(unix)


def unix_to_local_date(unix):
    return utc_date_to_local_date(unix_to_utc_date(unix))


def iso_to_unix(iso):
    return int(iso_to_utc_date(iso).timestamp())


def iso_to_utc_date(iso):
    return parser.parse(iso).replace(tzinfo=tz.tzutc())


def iso_to_local_date(iso):
    return utc_date_to_local_date(iso_to_utc_date(iso))


def utc_date_to_unix(utc_date):
    utc_date = utc_date.replace(tzinfo=tz.tzutc())
    return int(utc_date.timestamp())


def utc_date_to_iso(utc_date):
    return utc_date.isoformat()


def utc_date_to_local_date(utc_date):
    utc_date = utc_date.replace(tzinfo=tz.tzutc())
    return utc_date.astimezone(tz.tzlocal())


def local_date_to_unix(local_date):
    return utc_date_to_unix(local_date_to_utc_date(local_date))


def local_date_to_iso(local_date):
    return utc_date_to_iso(local_date_to_utc_date(local_date))


def local_date_to_utc_date(local_date):
    local_date = local_date.replace(tzinfo=tz.tzlocal())
    return local_date.astimezone(tz.tzutc())


def date_dict_to_unix(date_dict):
    return utc_date_to_unix(date_dict_to_utc_date(date_dict))


def date_dict_to_iso(date_dict):
    return utc_date_to_iso(date_dict_to_utc_date(date_dict))


def date_dict_to_utc_date(date_dict):
    local_date = datetime(
        year=date_dict['year'],
        month=date_dict['month'],
        day=date_dict['day'],
        hour=date_dict['hour'],
        minute=date_dict['minute'],
        tzinfo=tz.tzutc())
    return local_date


def date_dict_to_local_date(date_dict):
    local_date = datetime(
        year=date_dict['year'],
        month=date_dict['month'],
        day=date_dict['day'],
        hour=date_dict['hour'],
        minute=date_dict['minute'],
        tzinfo=tz.tzlocal())
    return local_date
