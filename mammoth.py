from ib.opt import ibConnection, message
from logicTools import isWeekday, secondsToOpen
from marketObjects import portfolio, stock, option, picklePortfolio, unPicklePortfolio


def main():
    global con
    con = ibConnection(port=7497, clientId=1618)
    # 7496 for real account, 7497 for paper trader
    con.registerAll(messageHandler)
    con.connect()


def messageHandler(msg):
    print(msg)


def subscriptionManager(marketObject, subscription=False):
    marketObject.subscription = subscription
    marketObject.subscriptionIndex = len(subscriptions)
    subscriptions.append(marketObject)


def initialize():
    global mammoth
    global subscriptions
    subscriptions = []
    mammoth = unPicklePortfolio()
    for i in mammoth.stocks:
        subscriptionManager(i, True)
        for j in i.options:
            subscriptionManager(j, True)


if False:  # __name__ == "__main__":
    main()
    while isWeekday():
        # today is a trading day
        initialize()
        while datetime.now().hour < 16:
            # it's trading hours
            pass
            # subscribe to everything
            # as quotes come in, selectively unsubscribe/re-subsubscribe
            # as quotes come in, promote best option from each stock
            # limit two stocks per industry
            # reorder best
        # unsubscribe from everything
        picklePortfolio(mammoth)
        sleep(secondsToOpen()-600)

initialize()
print(subscriptions)
