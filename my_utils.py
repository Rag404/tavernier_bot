from datetime import datetime


def log(*args):
    text = ' '.join(map(str, args))
    print(datetime.now().strftime('%d/%m %H:%M'), "-", text)