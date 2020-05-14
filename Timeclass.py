import time
from datetime import date


def clock():
    while True:
        # Returns time in hours-minutes-seconds
        current_time = time.strftime("%H:%M:%S", time.localtime(time.time()))
        return current_time


def get_date():
    while True:
        current_date = date.strftime(date.today(), "%d-%b-%Y")
        return current_date
