from ib.ext.Contract import Contract
from ib.opt import ibConnection, message
from marketObjects import newStock, newOption, newContract, buildPortfolio
from dataTools import pickler, unPickler
from logicTools import isWeekday, secondsTilOpen
from datetime import datetime as t
from time import sleep


def main():
    global con
    con = ibConnection(port=7497, clientId=1618)
    # 7496 for real account, 7497 for paper trader
    con.register(marketDataHandler, message.tickPrice)
    con.register(contractDetailsHandler, 'ContractDetails')
    con.register(contractDetailsEnder, 'ContractDetailsEnd')
    con.register(historicalDataHandler, message.historicalData)
    con.connect()


def initialize():
    global mammoth
    global subscriptions
    subscriptions = {}
    mammoth = unPickler('portfolio')
    k = 0
    for i in mammoth.stocks:
        subscriptions[k] = i
        i.subscrIndex = k
        subscriptionManager(i, True)
        k += 1
        for j in i.options:
            subscriptions[k] = j
            j.subscrIndex = k
            subscriptionManager(j, True)
            k += 1


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


###############################################################################
#   CONTRACT DATA
###############################################################################


def updateAllContracts():
    ready()
    for i in mammoth.stocks:
        getContractDetails(i)


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
    thisStock = subscriptions[msg.reqId]
    thisContract = msg.contractDetails.m_summary
    if thisContract.m_secType == 'STK':
        thisStock.industry = msg.contractDetails.m_industry
        thisStock.contract = thisContract
    dupe = False
    if thisContract.m_secType == 'OPT':
        for i in thisStock.options:
            if i.contract.m_conId == thisContract.m_conId:
                dupe = True
                break
    if not dupe:
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
#   PROGRAM
###############################################################################


def stockDataProcessor(stockObject):
    pass


def optionDataProcessor(optionObject):
    pass


###############################################################################
#   PROGRAM
###############################################################################

if __name__ == "__main__":
    program = False

    symbols = ['AXP', 'CAT', 'MSFT', 'BAC', 'GSK', 'TSLA', 'COF', 'NKE',
               'NFLX', 'AAPL']
    buildPortfolio(symbols)
    ready()
    updateAllContracts()
    pickler(mammoth, 'portfolio')
    initialize()
    for i in mammoth.stocks:
        print(str(len(i.options)) + ' options in ' + i.symbol)
    for i in mammoth.stocks:
        for j in i.options:
            print(str(j.symbol) + ' ' + str(j.expiry) + ' ' + str(j.strike))
#    print(subscriptions)
#    pickler(mammoth, 'portfolio')

    if program:
        main()
        while isWeekday():
            # today is a trading day
            initialize()
            updateAllContracts()
            while t.now().hour < 16:
                # it's trading hours
                pass
                # subscribe to everything
                # as quotes come in, selectively unsubscribe/re-subsubscribe
                # as quotes come in, promote best option from each stock
                # limit two stocks per industry
                # reorder best
            # unsubscribe from everything
            pickler(mammoth, 'portfolio')
            sleep(secondsTilOpen()-1800)  # start up 30 minutes before trading
