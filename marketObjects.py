import pickle


class portfolio(object):
    def __init__(self):
        self.stocks = []


class stock(object):
    def __init__(self, symbol):
        self.symbol = None
        self.position = 0
        self.last = 0
        self.bid = 0
        self.ask = 0
        self.close = 0
        self.historicalData = None
        self.subscribed = False
        self.subscriptionIndex = -1
        self.options = []


class option(object):
    def __init__(self, strike, expiry):
        self.expiry = expiry
        self.strike = strike
        self.position = 0
        self.type = 'PUT'
        self.last = 0
        self.bid = 0
        self.ask = 0
        self.close = 0
        self.maintenance = 0
        self.impliedVolatility = 0
        self.expectedValue = 0
        self.annualizedReturn = 0
        self.subscribed = False
        self.subscriptionIndex = -1


def newStock(portfolio, symbol):
    newStock = stock(symbol)
    portfolio.stocks.append(newStock)


def buildPortfolio():
    symbols = ['AAPL', 'CAT', 'MSFT', 'BAC', 'COF', 'AXP', 'TSLA',
               'AMZN', 'GSK', 'NFLX']
    thisPortfolio = portfolio()
    while symbols:
        newStock(thisPortfolio, symbols.pop())
    with open('mammoth.pickle', 'wb') as pickledPortfolio:
        pickle.dump(thisPortfolio, pickledPortfolio)
    print thisPortfolio
    print thisPortfolio.stocks


def picklePortfolio(thisPortfolio):
    with open('mammoth.pickle', 'wb') as pickledPortfolio:
        pickle.dump(thisPortfolio, pickledPortfolio)


def unPicklePortfolio():
    with open('mammoth.pickle', 'rb') as pickledPortfolio:
        thisPortfolio = pickle.load(pickledPortfolio)
    return thisPortfolio

