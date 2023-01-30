from datetime import datetime, timedelta


def log(*values: object, **kwargs):
    """A rewrite of the print() method to show the date and time"""
    print(datetime.now().strftime('%d/%m %H:%M'), "-", *values, **kwargs)


def time2str(time: timedelta):
    values = {}
    values["j"], r = divmod(time.seconds, 86400)
    values["h"], r = divmod(r, 3600)
    values["min"], values["s"] = divmod(r, 60)
    
    return " ".join([str(v) + k for k, v in values.items() if v > 0]) or "0s"