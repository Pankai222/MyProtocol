import time


def clock():
    while True:
        now = time.strftime("%H:%M", time.localtime(time.time()))
        return now
