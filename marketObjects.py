from ib.ext.Contract import Contract
from dataTools import pickler
from logicTools import datetimeConverver


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
        self.promoted = []  # highest EV option for each stock
        self.stocks = []


class stock(object):  # what if this class was an extension of a contract?
    def __init__(self, symbol):
        self.portfolio = portfolio()
        self.symbol = symbol.upper()
        self.position = 0
        self.secType = 'STK'
        self.last = 0
        self.bid = 0
        self.ask = 0
        self.close = 0
        self.historicalData = []
        self.impliedVolatility = 0
        self.target = {}
        self.subscribed = False
        self.subscrIndex = -1
        self.options = []
        self.promoted = ''  # highest EV option for each stock
        self.contract = Contract()  # newContract(self.symbol, 'STK')
        self.industry = None


class option(object):
    def __init__(self, symbol, strike, expiry):
        self.underlying = ''
        self.symbol = symbol.upper()
        self.expiry = expiry
        self.strike = strike
        self.position = 0
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
        self.subscrIndex = -1
        self.contract = Contract()


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
    contract.m_expiry = expiry  # is this datetime or dateString?
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


def newOption(stockObject, strike, expiry):
    newOption = option(stockObject.symbol, strike, expiry)
    newOption.underlying = stockObject
    stockObject.options.append(newOption)
    stockObject.target[expiry] = 0
    return newOption


def newOpenPosition(thisOption):
    thisPortfolio = thisOption.underlying.portfolio
    dupe = False
    for i in thisPortfolio.openPositions:
        if i.contract.m_conId == thisOption.contract.m_conId:
            i = thisOption
            dupe = True
            break
    if not dupe:
        thisPortfolio.openPositions.append(thisOption)


def removeExpiredContracts(stockObject):
    today = datetimeConverver()
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
    pickler(thisPortfolio, 'portfolio')
    print('Portfolio built.')


if __name__ == "__main__":
#    buildPortfolio()
    print(datetimeConverver())
