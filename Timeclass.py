import time


def clock():
    while True:
        # Returns time in hours-minutes-seconds
        now = time.strftime("%H:%M:%S", time.localtime(time.time()))
        return now
