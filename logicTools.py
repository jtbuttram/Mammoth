from datetime import datetime
from calendar import weekday


def isWeekday(addDays=0):
    if (weekday(datetime.today().year,
                datetime.today().month,
                datetime.today().day) + (addDays % 7)) < 5:
        return True
    else:
        return False


def secondsTilOpen():
    # returns seconds until 9:30am on next weekday
    sec = 0
    sec += (23 - datetime.now().hour) * 3600
    sec += (59 - datetime.now().minute) * 60
    sec += (59 - datetime.now().second)
#    sec += (1000000 - datetime.now().microsecond) / 1000000
    sec += (9.5 * 3600)  # seconds until 9:30am tomorrow
    wd = weekday(datetime.today().year,
                 datetime.today().month,
                 datetime.today().day)
    if wd > 3:
        sec += (6 - wd) * 24 * 3600
    return sec
