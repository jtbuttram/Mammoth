from ib.ext.Contract import Contract
from ib.opt import ibConnection, message
from marketObjects import *
# newStock, newOption, newContract, buildPortfolio, removeExpiredContracts, promote, newOpenPosition
from dataTools import pickler, unPickler
from logicTools import isWeekday, secondsTilOpen
from datetime import datetime as t
from time import sleep
from calendar import weekday
from brain import newTarget

'''
ACCEPTANCE CRITERIA
-------------------------------------------------------------------------------
* subscribe to everything before market open
* at portfolio level:
    * track positions
    * track available funds
    * cap leverage
* as quotes come in:
    * selectively unsubscribe from options
    * calculate value of each option
    * calculate expected return of each option
    * when best expected return for a stock changes, promote that option
* when an option is promoted:
    * compare all promoted options
    * trade to optimize return, including cost of trades
    * avoid day trades
    * limit two positions per industry
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
        subscriptionManager(i, True)
        k += 1
        contracts[i.contract.m_conId] = i
        for j in i.options:
            subscriptions[k] = j
            j.subscrIndex = k
            subscriptionManager(j, True)
            k += 1
            contracts[j.contract.m_conId] = j
    con.reqAccountUpdates(True, 'U1385930')
    print('Account details requested.')


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
    lastMsg = t.now()


def updateMammoth():
    ready()
    for i in mammoth.stocks:
        removeExpiredContracts(i)
        getContractDetails(i)


def allMessageHandler(msg):
    global lastMsg
    lastMsg = t.now()


def woolly():
    timeOut = t.timedelta(minutes=10)
    ready()
    while True:
        while t.now() < lastMsg + timeOut:
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
    thisOption = contracts[msg.contract.m_conId]
    thisOption.position = msg.position
    newOpenPosition(thisOption)


###############################################################################
#   CONTRACT DATA
###############################################################################


def getContractDetails(stockObject):
    reqId = stockObject.subscrIndex
    contract = newContract(stockObject.symbol, 'STK')
    con.reqContractDetails(reqId, contract)
    contract = newContract(stockObject.symbol, 'OPT', optType='PUT')
    con.reqContractDetails(reqId, contract)
    global cooker
    cooker = True
    i = 0
    while cooker and i < 120:
        sleep(0.1)
        i += 0.1
    print('Returned ' + str(len(stockObject.options)) + ' options for ' +
          stockObject.symbol + ' in ' + str(i) + ' seconds')


def contractDetailsHandler(msg):  # reqId is for underlying stock
    thisContract = msg.contractDetails.m_summary
    try:
        thisObject = contracts[thisContract.m_conId]
    except KeyError:
        if thisContract.m_conId is None:
            pass
        else:
            thisStock = subscriptions[msg.reqId]
            if thisContract.m_secType == 'STK':
                thisStock.industry = msg.contractDetails.m_industry
                thisStock.contract = thisContract
            elif thisContract.m_secType == 'OPT':
                addOption = newOption(thisStock, thisContract.m_strike,
                                      thisContract.m_expiry)
                addOption.contract = thisContract
                thisStock.options.append(addOption)


def contractDetailsEnder(msg):
    global cooker
    cooker = False


###############################################################################
#   MARKET DATA
###############################################################################


def subscriptionManager(marketObject, subscription=False):
    marketObject.subscription = subscription
    con.reqMktData(marketObject.subscrIndex, marketObject.contract, '',
                   not subscription)
    sleep(0.01)  # avoid 100+ simultaneous requests


def marketDataHandler(msg):
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


def getHistorialData(contract, whatToShow, reqId):
    # https://www.interactivebrokers.com/en/software/api/apiguide/tables/historical_data_limitations.htm
    tickerId = reqId
    endDateTime = t.today().strftime("%Y%m%d %H:%M:%S %Z")
    durationStr = "5 D"
    barSizeSetting = "1 day"
    # whatToShow='TRADES' #'TRADES', 'MIDPOINT', 'BID', 'ASK', 'BID_ASK',
    # 'HISTORICAL_VOLATILITY', 'OPTION_IMPLIED_VOLATILITY'
    useRTH = 0
    formatDate = 1
#    chartOptions = None
    con.reqHistoricalData(tickerId, contract, endDateTime, durationStr,
                          barSizeSetting, whatToShow, useRTH, formatDate)


def historicalDataHandler(msg):  # reqId is for underlying
    thisObject = subscriptions[msg.reqId]
    thisObject.HistoricalData.append((msg.date, msg.open, msg.high, msg.low,
                                      msg.close, msg.volume, msg.count,
                                      msg.WAP))


###############################################################################
#   PROCESSORS
###############################################################################


def stockDataProcessor(stockObject):
    # update target price for each expiry (quote --> neural network)
    for expiry, target in stockObject.target.iteritems():
        stockObject.target[expiry] = newTarget(expiry, stockObject)
    # update option EVs (numpy based on volatility)
    for j in stockObject.options:
        j.expectedValue = optionValue(j)


def optionDataProcessor(optionObject):
    pass
    # update EV
    # update Annualized Return
    #


###############################################################################
#   PROGRAM
###############################################################################

if __name__ == "__main__":
#    ready()
#    print('Done.')
#    sleep(8)
#    woolly()

    symbols = ['AXP', 'CAT', 'MSFT', 'BAC', 'GSK', 'TSLA', 'COF', 'NKE',
               'NFLX', 'AAPL']
    buildPortfolio(symbols)
    ready()
    updateMammoth()
    pickler(mammoth, 'portfolio')
#    initialize()
#    mammoth = unPickler('portfolio')

    for i in mammoth.stocks:
        print(str(len(i.options)) + ' options in ' + i.symbol)
#        for j in i.options:
#            print(str(j.symbol) + ' ' + str(j.expiry) + ' ' + str(j.strike))

#    for i in mammoth.stocks:
#        removeExpiredContracts(i)

#    for i in mammoth.stocks:
#        print(str(len(i.options)) + ' options in ' + i.symbol)

#    print(subscriptions)
#    pickler(mammoth, 'portfolio')
