from ib.ext.Contract import Contract
from ib.ext.ContractDetails import ContractDetails
from ib.opt import ibConnection, message
from time import sleep
from datetime import datetime


def print_message_from_ib(msg):
    print(msg)
#    print(msg.contractDetails.m_summary)#.m_expiry)
#    print(msg.contractDetails.m_summary.m_conId, msg.contractDetails.m_summary.m_strike)


def main():
    global con
    con = ibConnection(port=7496, clientId=1618)
    # clientId = 7496 for real account, 7497 for paper trader
    con.registerAll(print_message_from_ib)
#    con.register(print_message_from_ib, 'UpdateAccountValue')
#    con.register(print_message_from_ib, 'UpdatePortfolio')
#    con.register(print_message_from_ib, 'UpdateAccountTime')
#    con.register(print_message_from_ib, 'ContractDetails')
#    con.register(historicalDataHandler, message.historicalData)
#    con.register(marketDataHandler, message.tickPrice)
#    con.register(marketDataHandler, message.tickSize)
    con.connect()

    # In future blog posts, this is where we'll write code that actually does
    # something useful, like place orders, get real-time prices, etc.

    sleep(1)  # Give the program time to print messages sent from IB
#    con.disconnect()


def newContract(symbol, sec_type, exch='SMART', prim_exch='SMART', curr='USD',
                expiry=None, strike=None, opt_type=None):
    contract = Contract()
    contract.m_symbol = symbol
    contract.m_secType = sec_type
    contract.m_expiry = expiry
    contract.m_strike = strike
    contract.m_right = opt_type
    contract.m_exchange = exch
    contract.m_primaryExchange = prim_exch
    contract.m_currency = curr
    return contract


def getMarketData(contract):
    tickerId = 0
    genericTickList = ''
    snapshot = True
    con.reqMktData(tickerId, contract, genericTickList, snapshot)


def getContractDetails(contract):
    reqId = 0
    con.reqContractDetails(reqId, contract)


def getHistorialData(contract, whatToShow, reqId):
    # https://www.interactivebrokers.com/en/software/api/apiguide/tables/historical_data_limitations.htm
    tickerId = reqId
    endDateTime = datetime.today().strftime("%Y%m%d %H:%M:%S %Z")
    durationStr = "5 D"
    barSizeSetting = "1 day"
    # whatToShow='TRADES' #'TRADES', 'MIDPOINT', 'BID', 'ASK', 'BID_ASK',
    # 'HISTORICAL_VOLATILITY', 'OPTION_IMPLIED_VOLATILITY'
    useRTH = 0
    formatDate = 1
#    chartOptions = None
    con.reqHistoricalData(tickerId, contract, endDateTime, durationStr,
                          barSizeSetting, whatToShow, useRTH, formatDate)


def historicalDataHandler(msg):
#    print(msg)#.date, msg.open)
    if msg.reqId == 1:  # 'TRADES'
        trdList.append(msg)
    elif msg.reqId == 6:  # 'HISTORICAL_VOLATILITY'
        hisVolList.append(msg)
    elif msg.reqId == 7:  # 'OPTION_IMPLIED_VOLATILITY'
        impVolList.append(msg)


def marketDataHandler(msg):
   # if msg.typeName == 'tickPrice'
    print(msg.typeName)

if __name__ == "__main__":

    main()
#    con.reqAccountUpdates(True, 'U1385930')
#    sleep(8)
    thisContract = newContract('LVLT', 'STK', expiry='20160520', opt_type='PUT')
#    trdList = []
#    hisVolList = []
#    impVolList = []
    getMarketData(thisContract)
    sleep(1)
    con.cancelMktData(0)
    sleep(3)
#    getContractDetails(thisContract)
#    getHistorialData(thisContract, 'TRADES', 1)
#    getHistorialData(thisContract, 'HISTORICAL_VOLATILITY', 6)
#    getHistorialData(thisContract, 'OPTION_IMPLIED_VOLATILITY', 7)
#    sleep(5)
#    print(thisList)
#    ll = len(thisList)
#    for i in range(ll):
#        thisMsg = thisList.pop()
#        print(thisMsg)
    #    print(thisMsg.date, thisMsg.open)
    #    i += 1
#    con.disconnect
