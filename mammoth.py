from ib.ext.Contract import Contract
from ib.opt import ibConnection, message
from marketObjects import *
from dataTools import pickler, unPickler
from logicTools import *
from datetime import datetime, timedelta
from time import sleep
from calendar import weekday
from brain import newTarget, optionValue
import math
from apiConnection import makeReservation, nextReservation, disconnect, callMonitor


'''
ACCEPTANCE CRITERIA
-------------------------------------------------------------------------------
* iterate through marketObjects according to likelihood of a trade
* never subscribe to anything
* if connection is lost, reconnect and re-subscribe to everything
* at portfolio level:
    * track positions
    * track available funds
    * cap leverage
* as quotes come in:
    * adjust check-in frequency
        * add to a queue after a variable amount of time
        * the most competitive objects get added back to queue immediately?
        * every option gets checked at least once each hour
        * every stock gets checked at least once each minute
    * calculate value of each option
    * calculate expected return of each option
    * when best expected return for a stock changes, promote that option
* when an option is promoted:
    * compare all promoted options
    * trade to optimize return, including cost of trades
    * avoid day trades
    * limit two positions per industry
* limit program to 100 outstanding requests
    * global variable and function to interact with it
        * function returns true if ok to submit requests
* only store contract details for imminently relevant options
    * strike near last (w/n annualized volatility from historical data)
    * expiry w/n 40 weekdays
* pull in history when initializing (but only if not up to date)
* try again on timeouts
* scan portfolio frequently and update active contracts to monitor
* update positions and activity
-------------------------------------------------------------------------------
'''


def main():
    timeout = timedelta(minutes=10)
    ready()
    while True:
        while datetime.now() < lastActive + timeout:
            ready()
            nextReservation()
#            sleep(0.1)
        disconnect()
        pickler(mammoth, 'portfolio')
        if weekday(datetime.today()) == 4:
            updateMammoth()
        sleep(secondsTilOpen()-540)  # wake up 9 minutes before trading


def initialize():
    global mammoth
    global objRef
    objRef = {}
    mammoth = unPickler('portfolio')  # try, except then newPortfolio
    objId = 0
    for i in mammoth.stocks:
        objRef[objId] = i
        i.objId = objId
        objId += 1
        for j in i.options:
            objRef[objId] = j
            j.objId = objId
            objId += 1
    makeReservation('accountDetails')


def reset():
    pass


def ready():
    try:
        mammoth
    except NameError:
        initialize()
    lastActivity()


def updateMammoth():
    ready()
    for i in mammoth.stocks:
        removeExpiredContracts(i)
        makeReservation('stockDetails', i)
        makeReservation('historicalData', i)
        makeReservation('optionDetails', i)


def lastActivity():
    global lastActive
    lastActive = datetime.now()
#    print(msg)


###############################################################################
#   PORTFOLIO DATA
###############################################################################


def updateAccountDetails(attribute, value):
    eString = 'mammoth%s = value' % attribute
    exec(eString)


def updatePositions(openPositions):
    i = 0
    while i < len(mammoth.openPositions):
        dupe = False
        j = 0
        while j < len(openPositions):
            if mammoth.openPositions[i].contract.m_conId == openPositions[j].contract.m_conId:
                mammoth.openPositions[i].contract = openPositions[j].contract
                mammoth.openPositions[i].position = openPositions[j].position
                openPositions.pop(j)
                dupe = True
                break
            else:
                j += 1
        if not dupe:
            mammoth.openPositions[i].position = 0
            mammoth.openPositions.pop(i)
        else:
            i += 1
    for k in openPositions:
        sDupe = False
        oDupe = False
        for i in mammoth.stocks:
            if i.symbol == k.symbol:
                if k.secType == 'STK':
                    i.position = k.position
                    i.contract = k.contract
                    mammoth.openPositions.append(i)
                    sDupe = True
                    break
                elif k.secType == 'OPT':
                    for j in i.options:
                        if j.contract.m_conId == k.contract.m_conId:
                            j.position = k.position
                            j.active = True
                            j.contract = k.contract
                            mammoth.openPositions.append(j)
                            oDupe = True
                            break
        if not sDupe:
            thisStock = newStock(mammoth, k.symbol)
            thisStock.objId = len(objRef)
            objRef[thisStock.objId] = thisStock
            thisStock.position = k.position
            thisStock.contract = k.contract
            mammoth.openPositions.append(thisStock)
            makeReservation('stockDetails', thisStock)
            makeReservation('historicalData', thisStock)
            makeReservation('optionDetails', thisStock)
        if not oDupe:
            for i in mammoth.stocks:
                if i.symbol == k.symbol:
                    thisStock = i
            thisOption = newOption(thisStock, k.contract)
            thisOption.objId = len(objRef)
            objRef[thisOption.objId] = thisOption
            thisOption.position = k.position
            thisOption.contract = k.contract
            mammoth.openPositions.append(thisOption)

###############################################################################
#   CONTRACT DATA
###############################################################################


def updateStockDetails(objId, contract, industry):
    thisStock = objRef[objId]
    thisStock.contract = contract
    thisStock.industry = industry


def updateOptionDetails(objId, contract):
    thisStock = objRef[objId]
    if contract.m_conId:
        dupe = False
        for i in thisStock.options:
            if i.contract.m_conId == contract.m_conId:
                thisOption = i
                dupe = True
                break
        if not dupe:
            thisOption = newOption(thisStock, contract)
            thisOption.objId = len(objRef)
            objRef[thisOption.objId] = thisOption
        thisOption.active = activeContract(contract, thisStock)


def activeContract(contract, stockObject):
    dayVol = stockObject.historicalVolatility / math.sqrt(250)
    last = stockObject.last
    strike = contract.m_strike
    expiry = dateStringConverter(contract.m_expiry)
    t = weekdaysUntil(expiry)
    tq = math.sqrt(t)
    tooHigh = (strike > last * (1 + dayVol * tq * 2))
    tooLow = (strike < last * (1 - dayVol * tq * 2))
    tooFar = (t > 40)
    active = (not tooHigh) and (not tooLow) and (not tooFar)
    return active


###############################################################################
#   MARKET DATA
###############################################################################


def updateMarketData(objId, attribute, value):
    thisObject = objRef[objId]
    eString = 'thisObject%s = value' % attribute
    exec(eString)
    if thisObject.secType == 'STK':
        stockDataProcessor(thisObject)
    elif thisObject.secType == 'OPT':
        optionDataProcessor(thisObject)


###############################################################################
#   HISTORICAL DATA
###############################################################################


def refreshHistoricalData(portfolioObject):
    for i in portfolioObject.stocks:
        makeReservation('historicalData',i)


def updateHistoricalData(objId, date, dataType, data):  # reqId is for underlying
    thisObject = objRef[objId]
    try:
        thisObject.historicalData[date]
    except NameError:
        thisObject.historicalData[date] = historicalData(date)
        exec('thisObject.historicalData[date]%s = data') % dataType


def findHistoricalVolatility(stockObject):
    keepGoing = True
    thisDate = datetime.today()
    while keepGoing:
        dateString = thisDate.strftime('%Y%m%d')
        try:
            stockObject.historicalVolatility = (stockObject
                                                .historicalData[dateString]
                                                .historicalVolatility
                                                .close)
            keepGoing = False
        except KeyError:
            thisDate = (thisDate - timedelta(days=1))


###############################################################################
#   PROCESSORS
###############################################################################


def stockDataProcessor(stockObject):
    # update target price for each expiry (quote --> neural network)
    for expiry, target in stockObject.target.iteritems():
        stockObject.target[expiry] = newTarget(expiry, stockObject)
    # update option EVs (numpy based on volatility)
#    for j in stockObject.options:
#        j.expectedValue = optionValue(j)


def optionDataProcessor(optionObject):
    pass
    # update EV
    # update Annualized Return
    #


###############################################################################
#   PROGRAM
###############################################################################

if __name__ == "__main__":
 #   ready()
#    print('Done.')
#    sleep(8)
#    woolly()
 #   resetContractDetails(mammoth)
    symbols = ['BAC', 'AXP', 'GSK', 'COF', 'CAT', 'MSFT', 'AAPL']
#    symbols = ['COF', 'CAT', 'MSFT']
#    symbols = ['TSLA', 'NKE', 'NFLX', 'AAPL']
    buildPortfolio(symbols)
    ready()
    for i in mammoth.stocks:
        getStockDetails(i)
    while callMonitor():
        sleep(0.1)

#    initialize()
#    sleep(3)
    refreshHistoricalData(mammoth)
    while callMonitor():
        sleep(0.1)
    pickler(mammoth, 'portfolio')

#    initialize()
#    updateMammoth()
#    pickler(mammoth, 'portfolio')
#    initialize()
#    mammoth = unPickler('portfolio')
 #   for i in mammoth.stocks:
 #       print(str(len(i.options)) + ' options in ' + i.symbol)
 #   for j in mammoth.openPositions:
 #       print('%d %s %d %s %s') % (j.position, j.symbol, j.strike, j.optType, j.expiry)
#        for j in i.options:
#            print(str(j.symbol) + ' ' + str(j.expiry) + ' ' + str(j.strike))

#    for i in mammoth.stocks:
#        removeExpiredContracts(i)

    for i in mammoth.stocks:
        print('%d options in %s') % (len(i.options), i.symbol)
        print('%d days of history for %s') % (len(i.historicalData), i.symbol)

#    print(subscriptions)
#    pickler(mammoth, 'portfolio')
