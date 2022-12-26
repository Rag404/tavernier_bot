from datetime import datetime


def log(*values: object, **kwargs):
    """A rewrite of the print() method to show the date and time"""
    print(datetime.now().strftime('%d/%m %H:%M'), "-", *values, **kwargs)