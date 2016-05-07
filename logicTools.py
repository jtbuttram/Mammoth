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


def datetimeConverver(date='today'):
    if date == 'today':
        date = datetime.today()
    dateString = date.strftime('%Y%m%d %H:%M:%S %Z')
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


def weekdaysUntil(dateString):
    beginDate = datetime.today().date()
    endDate = dateStringConverter(dateString).date()
    weekdays = busday_count(beginDate, endDate)
    return weekdays


def callMonitor(callId=None, monitorCall=True, timeout=100):
    # leave callId blank to return number of outstanding calls
    timeOut = timedelta(seconds=timeout)
    global cooker
    if callId is not None:
        try:
            cooker
        except NameError:
            cooker = {}
        if not monitorCall:
            try:
                elapsed = (datetime.now() - cooker[callId]).microseconds / 1000
                del cooker[callId]
                print('resolved callId %d in %d ms') % (callId, elapsed)
            except KeyError:
                pass
        else:
            while len(cooker) >= 100:
                sleep(0.1)
                print('trying to add callId %d') % callId
            try:
                while cooker[callId]:
                    sleep(0.1)
            except KeyError:
                cooker[callId] = datetime.now()
                print('monitoring callId %d') % callId
            trash = []
            for k, v in cooker.iteritems():
                if v < datetime.now() - timeOut:
                    trash.append(k)
            while trash:
                del cooker[trash.pop()]
    else:
        try:
            cooker
        except NameError:
            return 0
        trash = []
        for k, v in cooker.iteritems():
            if v < datetime.now() - timeOut:
                trash.append(k)
                print('callId %d timed out after %d seconds') % (k, timeout)
        while trash:
            del cooker[trash.pop()]
        return len(cooker)
