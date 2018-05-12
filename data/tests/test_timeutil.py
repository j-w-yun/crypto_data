import timeutil

if __name__ == '__main__':
    unix = 1500000000

    # unix to ...
    iso = timeutil.unix_to_iso(unix)
    utc_date = timeutil.unix_to_utc_date(unix)
    local_date = timeutil.unix_to_local_date(unix)
    print('unix conversion:', iso)
    print('unix conversion:', utc_date)
    print('unix conversion:', local_date)

    # iso to ...
    unix_1 = timeutil.iso_to_unix(iso)
    utc_date_1 = timeutil.iso_to_utc_date(iso)
    local_date_1 = timeutil.iso_to_local_date(iso)
    print('iso conversion:', unix_1)
    print('iso conversion:', utc_date_1)
    print('iso conversion:', local_date_1)

    # utc_date to ...
    unix_2 = timeutil.utc_date_to_unix(utc_date)
    iso_2 = timeutil.utc_date_to_iso(utc_date)
    local_date_2 = timeutil.utc_date_to_local_date(utc_date)
    print('utc_date conversion:', unix_2)
    print('utc_date conversion:', iso_2)
    print('utc_date conversion:', local_date_2)

    # local_date to ...
    unix_3 = timeutil.local_date_to_unix(local_date)
    iso_3 = timeutil.local_date_to_iso(local_date)
    utc_date_3 = timeutil.local_date_to_utc_date(local_date)
    print('local_date conversion:', unix_3)
    print('local_date conversion:', iso_3)
    print('local_date conversion:', utc_date_3)

    # date_dict to ...
    date_dict = {
        'year': 2017,
        'month': 7,
        'day': 14,
        'hour': 2,
        'minute': 40
    }
    unix_4 = timeutil.date_dict_to_unix(date_dict)
    iso_4 = timeutil.date_dict_to_iso(date_dict)
    utc_date = timeutil.date_dict_to_utc_date(date_dict)
    local_date = timeutil.date_dict_to_local_date(date_dict)
    print('date_dict conversion:', unix_4)
    print('date_dict conversion:', iso_4)
    print('date_dict conversion:', utc_date)
    print('date_dict conversion:', local_date)
