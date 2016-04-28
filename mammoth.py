from ib.ext.Contract import Contract
from ib.opt import ibConnection, message
from marketObjects import *
# newStock, newOption, newContract, buildPortfolio, removeExpiredContracts, promote, newOpenPosition
from dataTools import pickler, unPickler
from logicTools import *
from datetime import datetime, timedelta
from time import sleep
from calendar import weekday
from brain import newTarget, optionValue
import math


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
-------------------------------------------------------------------------------
'''


def main():
    global con
    con = ibConnection(port=7496, clientId=1618)
    # 7496 for real account, 7497 for paper trader
    con.registerAll(allMessageHandler)
    con.register(accountDetailsHandler, 'UpdateAccountValue')
    con.register(positionsHandler, 'UpdatePortfolio')
#    con.register(portfolioDetailsHandler, 'UpdateAccountTime')
    con.register(marketDataHandler, message.tickPrice)
    con.register(contractDetailsHandler, 'ContractDetails')
    con.register(contractDetailsEnder, 'ContractDetailsEnd')
    con.register(historicalDataHandler, message.historicalData)
    con.connect()


def initialize():
    global mammoth
    global subscriptions
    subscriptions = {}
    global contracts
    contracts = {}
    mammoth = unPickler('portfolio')
    k = 0
    for i in mammoth.stocks:
        subscriptions[k] = i
        i.subscrIndex = k
        getMarketData(i)
        k += 1
        contracts[i.contract.m_conId] = i
        for j in i.options:
            subscriptions[k] = j
            j.subscrIndex = k
#            getMarketData(j)
            k += 1
            contracts[j.contract.m_conId] = j
#    getAccountDetails()


def ready():
    try:
        con
    except NameError:
        main()
    if not con.m_connected:
        main()
    try:
        mammoth
    except NameError:
        initialize()
    global lastMsg
    lastMsg = datetime.now()


def updateMammoth():
    ready()
    for i in mammoth.stocks:
        removeExpiredContracts(i)
        getContractDetails(i)
#        j = 0
        while callMonitor():
            sleep(1)
#            if j % 10 == 9:
#                print('%d calls cooking...') % callMonitor()
#            else:
#                print j
#            j += 1


def allMessageHandler(msg):
    global lastMsg
    lastMsg = datetime.now()
#    print(msg)


def woolly():
    timeOut = datetime.timedelta(minutes=10)
    ready()
    while True:
        while datetime.now() < lastMsg + timeOut:
            ready()
            sleep(60)
        con.disconnect()
        pickler(mammoth, 'portfolio')
        if weekday(t.today()) == 4:
            updateMammoth()
        sleep(secondsTilOpen()-540)  # wake up 9 minutes before trading


###############################################################################
#   PORTFOLIO DATA
###############################################################################


def getAccountDetails():
    callMonitor(88888888, True)
    con.reqAccountUpdates(False, 'U1385930')


def accountDetailsHandler(msg):
    if msg.key == 'CashBalance' and msg.currency == 'USD':
        mammoth.cashBalance = msg.value
    elif msg.key == 'AvailableFunds' and msg.currency == 'USD':
        mammoth.availableFunds = msg.value
    elif msg.key == 'MaintMarginReq' and msg.currency == 'USD':
        mammoth.maintenance = msg.value
    elif msg.key == 'NetLiquidationByCurrency' and msg.currency == 'USD':
        mammoth.netLiquidation = msg.value
    elif msg.key == 'OptionMarketValue' and msg.currency == 'USD':
        mammoth.optionMarketValue = msg.value
    elif msg.key == 'StockMarketValue' and msg.currency == 'USD':
        mammoth.stockMarketValue = msg.value
    elif msg.key == 'RealizedPnL' and msg.currency == 'USD':
        mammoth.realizedPnL = msg.value
    elif msg.key == 'UnrealizedPnL' and msg.currency == 'USD':
        mammoth.unrealizedPnL = msg.value


def positionsHandler(msg):
    callMonitor(88888888, False)
    thisOption = contracts[msg.contract.m_conId]
    thisOption.position = msg.position
    newOpenPosition(thisOption)


###############################################################################
#   CONTRACT DATA
###############################################################################


def getContractDetails(stockObject):
    ready()
    reqId = stockObject.subscrIndex

    contract = newContract(stockObject.symbol, 'STK')
    callMonitor(reqId + 90000000, True)
    con.reqContractDetails(reqId + 90000000, contract)

    contract = newContract(stockObject.symbol, 'OPT', optType='PUT')
    callMonitor(reqId, True)
    con.reqContractDetails(reqId, contract)


def contractDetailsHandler(msg):  # reqId is for underlying stock
    thisContract = msg.contractDetails.m_summary
    cId = thisContract.m_conId
    thisStock = subscriptions[msg.reqId % 90000000]
    if thisContract.m_conId:
        if keepContract(thisContract, thisStock):
            try:  # see if marketObject already exists
                contracts[cId]
            except KeyError:  # create new marketObject
                if thisContract.m_secType == 'OPT':
                    contracts[cId] = newOption(thisStock, thisContract)
                elif thisContract.m_secType == 'STK':
                    thisStock.industry = msg.contractDetails.m_industry
                    thisStock.contract = thisContract
        else:
            try:
                del thisStock.options[cId]
                del contracts[cId]
            except KeyError:
                pass


def keepContract(contract, stockObject):
    dayVol = thisStock.historicalVolatility / math.sqrt(250)
    last = stockObject.last
    srike = contract.m_strike
    expiry = dateStringConverver(contract.m_expiry)
    t = weekdaysUntil(expiry)
    tq = math.sqrt(t)
    tooHigh = (strike > last * (1 + dayVol * tq * 2))
    tooLow = (strike < last * (1 - dayVol * tq * 2))
    tooFar = (t > 40)
    keepIt = (not tooHigh) and (not tooLow) and (not tooFar)
    return keepIt


def contractDetailsEnder(msg):
    callMonitor(msg.reqId, False)


###############################################################################
#   MARKET DATA
###############################################################################


def getMarketData(marketObject, subscription=False):
    ready()
    marketObject.subscription = subscription
    callMonitor(marketObject.subscrIndex, True, timeout=5)
    con.reqMktData(marketObject.subscrIndex, marketObject.contract, '',
                   not subscription)
#    sleep(0.02)  # avoid 100+ simultaneous requests


def marketDataHandler(msg):
    callMonitor(msg.tickerId, False)
    thisObject = subscriptions[msg.tickerId]
    if msg.field == 1:
        thisObject.bid = msg.price
    elif msg.field == 2:
        thisObject.ask = msg.price
    elif msg.field == 4:
        thisObject.last = msg.price
    elif msg.field == 6:
        pass  # thisObject.high = msg.price
    elif msg.field == 7:
        pass  # thisObject.low = msg.price
    elif msg.field == 9:
        thisObject.close = msg.price
    if thisObject.secType == 'STK':
        stockDataProcessor(thisObject)
    elif thisObject.secType == 'OPT':
        optionDataProcessor(thisObject)


###############################################################################
#   HISTORICAL DATA
###############################################################################


def getHistoricalData(contract, whatToShow, reqId):
    ready()
#    https://www.interactivebrokers.com/en/software/api/apiguide/tables/historical_data_limitations.htm
    tickerId = reqId
    endDateTime = datetimeConverver()
#    endDateTime = datetime.today().strftime("%Y%m%d %H:%M:%S %Z")
    durationStr = "5 D"
    barSizeSetting = "1 day"
#    whatToShow = ['TRADES', 'MIDPOINT', 'BID', 'ASK', 'BID_ASK',
#                  'HISTORICAL_VOLATILITY', 'OPTION_IMPLIED_VOLATILITY']
    useRTH = 1
    formatDate = 1
#    chartOptions = None
    callMonitor(reqId, True)
    con.reqHistoricalData(tickerId, contract, endDateTime, durationStr,
                          barSizeSetting, whatToShow, useRTH, formatDate)


def refreshHistoricalData(portfolioObject):
    for i in portfolioObject.stocks:
        getHistoricalData(i.contract, 'TRADES', i.subscrIndex + 10000000)
        getHistoricalData(i.contract, 'HISTORICAL_VOLATILITY',
                          i.subscrIndex + 60000000)
        getHistoricalData(i.contract, 'OPTION_IMPLIED_VOLATILITY',
                          i.subscrIndex + 70000000)


def historicalDataHandler(msg):  # reqId is for underlying
    thisObject = subscriptions[msg.reqId % 10000000]
    if msg.date[:8] == 'finished':
        callMonitor(msg.reqId, False)
        if type(thisObject).__name__ == 'stock':
            findHistoricalVolatility(thisObject)
    else:
        thisObject.historicalData[msg.date] = historicalData(msg.date)
        if 1 == msg.reqId // 10000000:
            t = thisObject.historicalData[msg.date].trades
        elif 6 == msg.reqId // 10000000:
            t = thisObject.historicalData[msg.date].historicalVolatility
        elif 7 == msg.reqId // 10000000:
            t = thisObject.historicalData[msg.date].impliedVolatility
        t.open = msg.open
        t.high = msg.high
        t.low = msg.low
        t.close = msg.close
        t.volume = msg.volume
        t.count = msg.count
        t.WAP = msg.WAP


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
    symbols = ['BAC', 'AXP', 'GSK']
#    symbols = ['COF', 'CAT', 'MSFT']
#    symbols = ['TSLA', 'NKE', 'NFLX', 'AAPL']
    buildPortfolio(symbols)
    ready()

    initialize()
    sleep(3)
    refreshHistoricalData(mammoth)
    while callMonitor():
        sleep(1)
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
