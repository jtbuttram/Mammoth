from ib.ext.Contract import Contract
from dataTools import pickler


class portfolio(object):
    def __init__(self):
        self.stocks = []


class stock(object):  # what if this class was an extension of a contract?
    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.position = 0
        self.last = 0
        self.bid = 0
        self.ask = 0
        self.close = 0
        self.historicalData = []
        self.subscribed = False
        self.subscrIndex = -1
        self.options = []
        self.contract = newContract(self.symbol, 'STK')
        self.industry = None


class option(object):
    def __init__(self, symbol, strike, expiry):
        self.underlying = None
        self.symbol = symbol.upper()
        self.expiry = expiry
        self.strike = strike
        self.position = 0
        self.opt_type = 'PUT'
        self.multiplier
        self.last = 0
        self.bid = 0
        self.ask = 0
        self.close = 0
        self.maintenance = 0
        self.impliedVolatility = 0
        self.expectedValue = 0
        self.annualizedReturn = 0
        self.subscribed = False
        self.subscrIndex = -1
        self.contract = None


def newContract(self, symbol, sec_type, opt_type='', strike='', expiry=''):
    contract = Contract()
    contract.m_symbol = symbol
    contract.m_secType = sec_type
    contract.m_exchange = 'SMART'
    contract.m_primaryExchange = 'SMART'
    contract.m_currency = 'USD'
    contract.m_expiry = expiry
    # str(expiry.year*10000 + expiry.month*100 + expiry.day)
    contract.m_strike = float(strike)
    contract.m_multiplier = 100
    contract.m_right = opt_type
    return contract


def newStock(portfolioObject, symbol):
    newStock = stock(symbol)
    portfolioObject.stocks.append(newStock)


def newOption(stockObject, strike, expiry):
    newOption = option(stockObject.symbol, strike, expiry)
    newOption.underlying = stockObject
    stockObject.options.append(newOption)


def buildPortfolio():
    symbols = ['AAPL', 'CAT', 'MSFT', 'BAC', 'COF', 'AXP', 'TSLA',
               'AMZN', 'GSK', 'NFLX']
    thisPortfolio = portfolio()
    while symbols:
        newStock(thisPortfolio, symbols.pop())
    pickler(thisPortfolio, 'portfolio')
    print thisPortfolio
    print thisPortfolio.stocks
