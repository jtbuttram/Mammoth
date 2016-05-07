from ib.opt import ibConnection, message
from logicTools import callMonitor
from mammoth import updateAccountDetails updatePositions


def main():
    global con
    con = ibConnection(port=7496, clientId=1618)
    # 7496 for real account, 7497 for paper trader
    con.registerAll(allMessageHandler)
    con.register(accountDetailsHandler, 'UpdateAccountValue')
    con.register(positionsHandler, 'UpdatePortfolio')
    con.register(marketDataHandler, message.tickPrice)
    con.register(contractDetailsHandler, 'ContractDetails')
    con.register(contractDetailsEnder, 'ContractDetailsEnd')
    con.register(historicalDataHandler, message.historicalData)
    con.connect()


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
    global lastMsg
    lastMsg = datetime.now()
#    print(msg)


###############################################################################
#   PORTFOLIO DATA
###############################################################################


def getAccountDetails():
    check()
    callMonitor(88888888, True)
    callMonitor(88888889, True)
    con.reqAccountUpdates(False, 'U1385930')


def accountDetailsHandler(msg):
    callMonitor(88888888, False)
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
    updateAccountDetails(attribute, value)


def positionsHandler(msg):
    callMonitor(88888889, False)
    contract = msg.contract
    updatePositions(contract, msg.contract.m_symbol, msg.contract.m_conId)


###############################################################################
#   CONTRACT DATA
###############################################################################


def refreshPortfolio(portfolio, symbols=None):
    # add input of symbols to remove
    while symbols:
        dupe = False
        symbol = symbols.pop()
        for i in portfolio.stocks:
            if i.symbol == symbol:
                dupe = True
                break
        if not dupe:
            thisStock = newStock(portfolio, symbol)
            thisStock.objId = len(objRef)
            objRef[thisStock.objId] = thisStock
            reqId = thisStock.objId
            callMonitor(reqId + 90000000, True)
            con.reqContractDetails(reqId + 90000000, stockObject.contract)
    while callMonitor():
        sleep(0.1)
    return thisPortfolio


def getStockDetails(stockObject):
    ready()
    reqId = stockObject.objId
    callMonitor(reqId + 90000000, True)
    con.reqContractDetails(reqId + 90000000, stockObject.contract)


def getOptionDetails(stockObject):
    ready()
    reqId = stockObject.objId
    contract = newContract(stockObject.symbol, 'OPT', optType='PUT')
    callMonitor(reqId, True)
    con.reqContractDetails(reqId, contract)


def contractDetailsHandler(msg):  # reqId is for underlying stock
    thisContract = msg.contractDetails.m_summary
    refObject = objRef[msg.reqId % 90000000]
    if refObject.secType == 'STK':
        thisStock = refObject
    elif refObject.secType == 'OPT':
        thisStock = refObject.underlying
    if thisContract.m_conId:
        if thisContract.m_secType == 'STK':
            thisStock.industry = msg.contractDetails.m_industry
            thisStock.contract = thisContract
        elif thisContract.m_secType == 'OPT':
            if keepContract(thisContract, thisStock):
                try:  # see if marketObject already exists
                    thisStock.options[thisContract.m_conId]
                except KeyError:  # create new marketObject
                    objRef[len(objRef)] = newOption(thisStock, thisContract)
            else:
                try:
                    oId = thisStock.options[thisContract.m_conId].objId
                    del thisStock.options[thisContract.m_conId]
                    del objRef[oId]
                except KeyError:
                    pass


def contractDetailsEnder(msg):
    callMonitor(msg.reqId, False)


###############################################################################
#   MARKET DATA
###############################################################################


def getMarketData(marketObject, subscription=False):
    ready()
    marketObject.subscription = subscription
    callMonitor(marketObject.objId, True, timeout=5)
    snapshot = not subscription
    con.reqMktData(marketObject.objId, marketObject.contract, '', snapshot)


def marketDataHandler(msg):
    callMonitor(msg.tickerId, False)
    thisObject = objRef[msg.tickerId]
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
    callMonitor(reqId, True, timeout=5)
    con.reqHistoricalData(tickerId, contract, endDateTime, durationStr,
                          barSizeSetting, whatToShow, useRTH, formatDate)


def refreshHistoricalData(portfolioObject):
    for i in portfolioObject.stocks:
        getHistoricalData(i.contract, 'TRADES', i.objId + 10000000)
        getHistoricalData(i.contract, 'HISTORICAL_VOLATILITY',
                          i.objId + 60000000)
        getHistoricalData(i.contract, 'OPTION_IMPLIED_VOLATILITY',
                          i.objId + 70000000)


def historicalDataHandler(msg):  # reqId is for underlying
    thisObject = objRef[msg.reqId % 10000000]
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
