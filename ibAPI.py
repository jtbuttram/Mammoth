from ib.ext.Contract import Contract
from ib.opt import ibConnection, message


def main():
    global con
    con = ibConnection(port=7497, clientId=1618)
    # 7496 for real account, 7497 for paper trader
    con.register(marketDataHandler, message.tickPrice)
    con.register(contractDetailsHandler, 'ContractDetails')
    con.register(historicalDataHandler, message.historicalData)
    con.connect()


def marketDataHandler(msg):
    thisObject = subscriptions[msg.tickerId]
    if msg.field == 1:
        thisObject.bid = msg.price
    if msg.field == 2:
        thisObject.ask = msg.price
    if msg.field == 4:
        thisObject.last = msg.price
    if msg.field == 6:
        pass  # thisObject.high = msg.price
    if msg.field == 7:
        pass  # thisObject.low = msg.price
    if msg.field == 9:
        thisObject.close = msg.price


def contractDetailsHandler(msg):  # reqId is for underlying
    print(msg.contractDetails.m_summary)
    thisObject = subscriptions[msg.reqId]
    addOption = newOption(thisObject, msg.contractDetails.m_summary.m_strike,
                          msg.contractDetails.m_summary.m_expiry)
    addOption.contract = msg.contractDetails.m_summary
    thisObject.options.append(addOption)
    # need to dedupe


def historicalDataHandler(msg):  # reqId is for underlying
    thisObject = subscriptions[msg.reqId]
    thisObject.HistoricalData.append((msg.date, msg.open, msg.high, msg.low,
                                      msg.close, msg.volume, msg.count,
                                      msg.WAP))


def subscriptionManager(marketObject, subscription=False):
    marketObject.subscription = subscription
    snapshot = not subscription
    con.reqMktData(marketObject.subscrIndex, marketObject.contract, '',
                   snapshot)
