from ib.opt import ibConnection, message
from datetime import datetime, timedelta
from marketObjects import stock, option, dataFormat


def main():
    global con
    con = ibConnection(port=7496, clientId=1618)
    # 7496 for real account, 7497 for paper trader
    con.registerAll(allMessageHandler)
    con.register(accountDetailsHandler, 'UpdateAccountValue')
    con.register(positionsHandler, 'UpdatePortfolio')
    con.register(accountDetailsEnder, 'AccountDownloadEnd')
    con.register(marketDataHandler, message.tickPrice)
    con.register(contractDetailsHandler, 'ContractDetails')
    con.register(contractDetailsEnder, 'ContractDetailsEnd')
    con.register(historicalDataHandler, message.historicalData)
    con.connect()


def disconnect():
    con.disconnect()


def __init__():
    main()


def check():
    try:
        con
    except NameError:
        main()
    if not con.m_connected:
        main()


def allMessageHandler(msg):
#    print(msg)
    mammoth.lastActivity()


###############################################################################
#   PORTFOLIO DATA
###############################################################################


def getAccountDetails():
    check()
    callMonitor(88888888, True)
    con.reqAccountUpdates(False, 'U1385930')


def accountDetailsHandler(msg):
    if msg.key == 'CashBalance' and msg.currency == 'USD':
        attribute = '.cashBalance'
    elif msg.key == 'AvailableFunds' and msg.currency == 'USD':
        attribute = '.availableFunds'
    elif msg.key == 'MaintMarginReq' and msg.currency == 'USD':
        attribute = '.maintenance'
    elif msg.key == 'NetLiquidationByCurrency' and msg.currency == 'USD':
        attribute = '.netLiquidation'
    elif msg.key == 'OptionMarketValue' and msg.currency == 'USD':
        attribute = '.optionMarketValue'
    elif msg.key == 'StockMarketValue' and msg.currency == 'USD':
        attribute = '.stockMarketValue'
    elif msg.key == 'RealizedPnL' and msg.currency == 'USD':
        attribute = '.realizedPnL'
    elif msg.key == 'UnrealizedPnL' and msg.currency == 'USD':
        attribute = '.unrealizedPnL'
    value = msg.value
    mammoth.updateAccountDetails(attribute, value)


def positionsHandler(msg):
    global opens
    try:
        opens
    except NameError:
        opens = []
    if msg.contract.m_secType == 'STK':
        thisObject = stock(msg.contract.m_symbol)
    elif msg.contract.m_secType == 'OPT':
        thisObject = option(msg.contract.m_symbol, msg.contract.m_strike, msg.contract.m_expiry)
    thisObject.contract = msg.contract
    thisObject.position = msg.position
    opens.append(thisObject)


def accountDetailsEnder():
    callMonitor(88888888, False)
    mammoth.updatePositions(opens)
    del opens



###############################################################################
#   CONTRACT DATA
###############################################################################


def getStockDetails(stockObject):
    check()
    reqId = stockObject.objId
    callMonitor(reqId, True)
    con.reqContractDetails(reqId, stockObject.contract)


def getOptionDetails(stockObject):
    check()
    reqId = stockObject.objId
    contract = newContract(stockObject.symbol, 'OPT', optType='PUT')
    callMonitor(reqId, True)
    con.reqContractDetails(reqId, contract)


def contractDetailsHandler(msg):  # reqId is for underlying stock
    thisContract = msg.contractDetails.m_summary
    if thisContract.m_secType == 'STK':
        mammoth.updateStockDetails(msg.reqId, thisContract, msg.contractDetails.m_industry)
    elif thisContract.m_secType == 'OPT':
        mammoth.updateOptionDetails(msg.reqId, thisContract)


def contractDetailsEnder(msg):
    callMonitor(msg.reqId, False)


###############################################################################
#   MARKET DATA
###############################################################################


def getMarketData(marketObject, subscription=False):
    check()
    marketObject.subscription = subscription
    snapshot = not subscription
    callMonitor(marketObject.objId, True, timeout=5)
    con.reqMktData(marketObject.objId, marketObject.contract, '', snapshot)


def marketDataHandler(msg):
    callMonitor(msg.tickerId, False)
    thisObject = objRef[msg.tickerId]
    if msg.field == 1:
        attribute = '.bid'
        value = msg.price
    elif msg.field == 2:
        attribute = '.ask'
        value = msg.price
    elif msg.field == 4:
        attribute = '.last'
        value = msg.price
    elif msg.field == 6:
        pass
#        attribute = '.high'
#        value = msg.price
    elif msg.field == 7:
        pass
#        attribute = '.low'
#        value = msg.price
    elif msg.field == 9:
        attribute = '.close'
        value = msg.price
    mammoth.updateMarketData(msg.tickerId, attribute, value)


###############################################################################
#   HISTORICAL DATA
###############################################################################


def getHistoricalData(marketObject):
    check()
    contract = marketObject.contract
    durationStr = '5 D'
    barSizeSetting = '1 day'
    useRTH = 1
    formatDate = 1
    endDateTime = datetimeConverver()

    whatToShow = 'TRADES'
    reqId = marketObject.objId + 10000000
    callMonitor(reqId, True, timeout=5)
    con.reqHistoricalData(reqId, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate)

    whatToShow = 'HISTORICAL_VOLATILITY'
    reqId = marketObject.objId + 60000000
    callMonitor(reqId, True, timeout=5)
    con.reqHistoricalData(reqId, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate)

    whatToShow = 'OPTION_IMPLIED_VOLATILITY'
    reqId = marketObject.objId + 70000000
    callMonitor(reqId, True, timeout=5)
    con.reqHistoricalData(reqId, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate)


def historicalDataHandler(msg):  # reqId is for underlying
    objId = msg.reqId % 10000000
    if msg.date[:8] == 'finished':
        callMonitor(msg.reqId, False)
    else:
        thisData = dataFormat()
        date = msg.date
        if 1 == msg.reqId // 10000000:
            dataType = '.trades'
        elif 6 == msg.reqId // 10000000:
            dataType = '.historicalVolatility'
        elif 7 == msg.reqId // 10000000:
            dataType = '.impliedVolatility'
        thisData.open = msg.open
        thisData.high = msg.high
        thisData.low = msg.low
        thisData.close = msg.close
        thisData.volume = msg.volume
        thisData.count = msg.count
        thisData.WAP = msg.WAP
    mammoth.updateHistoricalData(objId, date, dataType, thisData)


###############################################################################
#   CALL MANAGEMENT
###############################################################################


class reservation(object):
    def __init__(self, callType, marketObject, time):
        self.callType = callType
        self.marketObject = marketObject
        self.time = time
        if marketObject:
            self.objId = marketObject.objId


def makeReservation(callType, marketObject=None, delay=0):
    global reservations
    try:
        reservations
    except NameError:
        reservations = []
    time = datetime.now() + timedelta(seconds=delay)
    thisReservation = reservation(callType, marketObject, time)
    j = 0
    for i in reservations:
        j += 1
        if time > i.time:
            j -= 1
            break
    reservations.insert(j,thisReservation)


def nextReservation():
    i = len(reservations) - 1
    while reservations:
        if callMonitor(reservations[i].objId):
            thisReservation = reservations.pop(i)
            break
        else:
            i -= 1
            if i < 0:
                i = len(reservations) - 1
    if thisReservation.callType == 'accountDetails':
        getAccountDetails()
    if thisReservation.callType == 'stockDetails':
        getStockDetails(thisReservation.marketObject)
    if thisReservation.callType == 'optionDetails':
        getOptionDetails(thisReservation.marketObject)
    if thisReservation.callType == 'marketData':
        getMarketData(thisReservation.marketObject)
    if thisReservation.callType == 'historicalData':
        getHistoricalData(thisReservation.marketObject)


def callMonitor(callId=None, monitorCall=True, timeout=100):
    # leave callId blank to return number of outstanding calls
    timeOut = timedelta(seconds=timeout)
    global cooker
    try:
        cooker
    except NameError:
        cooker = {}
    trash = []
    for k, v in cooker.iteritems():
        if v < datetime.now() - timeOut:
            trash.append(k)
            print('callId %d timed out after %d seconds') % (k, timeout)
    while trash:
        del cooker[trash.pop()]
    if callId is not None:
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
                print('waiting to add callId %d') % callId
            try:
                if cooker[callId]:
                    return False
            except KeyError:
                cooker[callId] = datetime.now()
                print('monitoring callId %d') % callId
                return True
    else:
        return len(cooker)


import mammoth  # this import is at the end of the module to avoid circular reference issues