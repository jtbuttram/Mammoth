from ib.ext.Contract import Contract
from dataTools import pickler
from logicTools import datetimeConverter


class portfolio(object):
    def __init__(self):
        self.cashBalance = 0
        self.maintenance = -1
        self.netLiquidation = 0
        self.optionMarketValue = 0
        self.stockMarketValue = 0
        self.realizedPnL = 0
        self.unrealizedPnL = 0
        self.totalCash = 0
        self.availableFunds = 0
        self.openPositions = []  # open positions
        self.promoted = []  # key is stock symbol
        self.stocks = []


class stock(object):  # what if this class was an extension of a contract?
    def __init__(self, symbol):
        self.portfolio = None
        self.symbol = symbol.upper()
        self.objId = -1
        self.position = 0
        self.secType = 'STK'
        self.last = 0
        self.bid = 0
        self.ask = 0
        self.close = 0
        self.historicalData = {}
        self.historicalVolatility = 0
        self.impliedVolatility = 0
        self.target = {}
        self.subscribed = False
        self.options = []
        self.promoted = None  # highest EV option for each stock
        self.contract = newContract(self.symbol, 'STK')
        self.industry = None


class option(object):
    def __init__(self, symbol, strike, expiry):
        self.underlying = ''
        self.symbol = symbol.upper()
        self.expiry = expiry
        self.strike = strike
        self.objId = -1
        self.position = 0
        self.active = False
        self.secType = 'OPT'
        self.optType = 'PUT'
        self.last = 0
        self.bid = 0
        self.ask = 0
        self.close = 0
        self.maintenance = 0
        self.expectedValue = 0
        self.annualizedReturn = 0
        self.subscribed = False
        self.contract = None


class dataFormat(object):
    def __init__(self):
        # self.date = -1
        self.open = -1
        self.high = -1
        self.low = -1
        self.close = -1
        self.volume = -1
        self.count = -1
        self.WAP = -1


class historicalData(object):
    def __init__(self, date):
        self.date = date
        self.trades = dataFormat()
        self.historicalVolatility = dataFormat()
        self.impliedVolatility = dataFormat()


def promote(thisOption):
    thisStock = thisOption.underlying
    thisStock.promoted = thisOption


def newContract(symbol, secType, optType='', strike=0, expiry=''):
    contract = Contract()
    contract.m_symbol = symbol
    contract.m_secType = secType
    contract.m_exchange = 'SMART'
    contract.m_primaryExchange = 'SMART'
    contract.m_currency = 'USD'
    contract.m_expiry = expiry  # dateString
    contract.m_strike = float(strike)
    contract.m_multiplier = 100
    contract.m_right = optType
    return contract


def newStock(portfolioObject, symbol):
    newStock = stock(symbol)
    portfolioObject.stocks.append(newStock)
    portfolioObject.promoted.append(newStock.promoted)
    newStock.portfolio = portfolioObject
    return newStock


def newOption(stockObject, contract):
    strike = contract.m_strike
    expiry = contract.m_expiry
    newOption = option(stockObject.symbol, strike, expiry)
    newOption.underlying = stockObject
    newOption.contract = contract
    stockObject.options.append(newOption)
#    stockObject.target[expiry] = 0
    return newOption


def openPosition(thisObject):
    # promote both stocks and options
    if thisObject.secType == 'STK':
        thisPortfolio = thisObject.portfolio
    elif thisObject.secType == 'OPT':
        thisPortfolio = thisObject.underlying.portfolio
    dupe = False
    for i in thisPortfolio.openPositions:
        if i.contract.m_conId == thisObject.contract.m_conId:
            i = thisObject
            dupe = True
            break
    if not dupe:
        thisPortfolio.openPositions.append(thisObject)


def removeExpiredContracts(stockObject):
    today = datetimeConverter()
    i = 0
    while i < len(stockObject.options):
        if stockObject.options[i].expiry < today:
            del stockObject.options[i]
        elif stockObject.options[i].expiry is None:
            del stockObject.options[i]
        else:
            i += 1


def buildPortfolio(symbols):  # symbols is a list of stock symbols
    #    , 'COF', 'AXP', 'TSLA', 'AMZN', 'GSK', 'NFLX']
    thisPortfolio = portfolio()
    while symbols:
        newStock(thisPortfolio, symbols.pop())
    l = len(thisPortfolio.stocks)
    pickler(thisPortfolio, 'portfolio')
#    return thisPortfolio
    print('Portfolio built with %d stocks loaded.') % l
    return thisPortfolio


def resetContractDetails(portfolioObject):
    for i in portfolioObject.stocks:
        i.options = []

if __name__ == "__main__":
#    buildPortfolio()
    print(datetimeConverter())
