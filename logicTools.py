from time import sleep
from datetime import datetime, timedelta, date
from calendar import weekday
from numpy import busday_count


def isWeekday(addDays=0):
    if ((weekday(datetime.today().year,
                 datetime.today().month,
                 datetime.today().day) + addDays) % 7) < 5:
        return True
    else:
        return False


def datetimeConverter(date='today'):
    if date == 'today':
        date = datetime.today()
    dateString = date.strftime('%Y%m%d %H:%M:%S %Z')
    return dateString


def dateConverter(date='today'):
    if date == 'today':
        date = datetime.today()
    dateString = date.strftime('%Y%m%d')
    return dateString


def dateStringConverter(dateString):
    dateTime = datetime.strptime(dateString, '%Y%m%d')
    return dateTime


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


def secondsTilClose():
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


def weekdaysUntil(endDatetime):
    beginDate = datetime.today().date()
    endDate = endDatetime.date()
    weekdays = busday_count(beginDate, endDate)
    return weekdays


def weekdaysBetween(startDatetime, endDatetime):
    beginDate = startDatetime.date()
    endDate = endDatetime.date()
    weekdays = busday_count(beginDate, endDate)
    return weekdays


def weekdaysBetweenStr(startDateStr, endDateStr):
    beginDate = dateStringConverter(startDateStr)
    endDate = dateStringConverter(endDateStr)
    weekdays = busday_count(beginDate, endDate)
    return weekdays