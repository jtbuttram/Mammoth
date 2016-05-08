from ib.ext.Contract import Contract
from ib.opt import ibConnection, message
from marketObjects import *
from dataTools import pickler, unPickler
from logicTools import *
from datetime import datetime, timedelta
from time import sleep
from calendar import weekday
from brain import newTarget, optionValue
import math


'''
ACCEPTANCE CRITERIA
-------------------------------------------------------------------------------
* iterate through marketObjects according to likelihood of a trade
* never subscribe to anything
* if connection is lost, reconnect and re-subscribe to everything
* at portfolio level:
    * track positions
    * track available funds
    * cap leverage
* as quotes come in:
    * adjust check-in frequency
        * add to a queue after a variable amount of time
        * the most competitive objects get added back to queue immediately?
        * every option gets checked at least once each hour
        * every stock gets checked at least once each minute
    * calculate value of each option
    * calculate expected return of each option
    * when best expected return for a stock changes, promote that option
* when an option is promoted:
    * compare all promoted options
    * trade to optimize return, including cost of trades
    * avoid day trades
    * limit two positions per industry
* limit program to 100 outstanding requests
    * global variable and function to interact with it
        * function returns true if ok to submit requests
* only store contract details for imminently relevant options
    * strike near last (w/n annualized volatility from historical data)
    * expiry w/n 40 weekdays
* pull in history when initializing (but only if not up to date)
* try again on timeouts
* scan portfolio frequently and update active contracts to monitor
* update positions and activity
* obey pacing rules for historical data
-------------------------------------------------------------------------------
'''


def main():
    timeout = timedelta(minutes=10)
    ready()
    while True:
        while datetime.now() < lastActive + timeout:
            ready()
            nextReservation()
#            sleep(0.1)
        disconnect()
        pickler(mammoth, 'portfolio')
        if weekday(datetime.today()) == 4:
            updateMammoth()
        sleep(secondsTilOpen()-540)  # wake up 9 minutes before trading

def initialize():
    connect()
    global mammoth
    global objRef
    objRef = {}
    try:
        mammoth = unPickler('portfolio_X')
    except IOError:
#        symbols = ['BAC', 'AXP', 'GSK', 'COF', 'CAT', 'MSFT', 'AAPL']
        symbols = ['A', 'AA', 'AAL', 'AAP', 'AAPL', 'ABBV', 'ABC', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADM', 'ADP', 'ADS', 'ADSK', 'AEE', 'AEP', 'AES', 'AET', 'AFL', 'AGN', 'AIG', 'AIV', 'AIZ', 'AKAM', 'ALL', 'ALLE', 'ALXN', 'AMAT', 'AME', 'AMG', 'AMGN', 'AMP', 'AMT', 'AMZN', 'AN', 'ANTM', 'AON', 'APA', 'APC', 'APD', 'APH', 'ARG', 'ATVI', 'AVB', 'AVGO', 'AVY', 'AWK', 'AXP', 'AZO', 'BA', 'BAC', 'BAX', 'BBBY', 'BBT', 'BBY', 'BCR', 'BDX', 'BEN', 'BF.B', 'BHI', 'BIIB', 'BK', 'BLK', 'BLL', 'BMY', 'BRK.B', 'BSX', 'BWA', 'BXLT', 'BXP', 'C', 'CA', 'CAG', 'CAH', 'CAT', 'CB', 'CBG', 'CBS', 'CCE', 'CCI', 'CCL', 'CELG', 'CERN', 'CF', 'CFG', 'CHD', 'CHK', 'CHRW', 'CI', 'CINF', 'CL', 'CLX', 'CMA', 'CMCSA', 'CME', 'CMG', 'CMI', 'CMS', 'CNC', 'CNP', 'COF', 'COG', 'COH', 'COL', 'COP', 'COST', 'CPB', 'CPGX', 'CRM', 'CSCO', 'CSRA', 'CSX', 'CTAS', 'CTL', 'CTSH', 'CTXS', 'CVC', 'CVS', 'CVX', 'CXO', 'D', 'DAL', 'DD', 'DE', 'DFS', 'DG', 'DGX', 'DHI', 'DHR', 'DIS', 'DISCA', 'DISCK', 'DLPH', 'DLTR', 'DNB', 'DO', 'DOV', 'DOW', 'DPS', 'DRI', 'DTE', 'DUK', 'DVA', 'DVN', 'EA', 'EBAY', 'ECL', 'ED', 'EFX', 'EIX', 'EL', 'EMC', 'EMN', 'EMR', 'ENDP', 'EOG', 'EQIX', 'EQR', 'EQT', 'ES', 'ESRX', 'ESS', 'ETFC', 'ETN', 'ETR', 'EW', 'EXC', 'EXPD', 'EXPE', 'EXR', 'F', 'FAST', 'FB', 'FCX', 'FDX', 'FE', 'FFIV', 'FIS', 'FISV', 'FITB', 'FL', 'FLIR', 'FLR', 'FLS', 'FMC', 'FOX', 'FOXA', 'FRT', 'FSLR', 'FTI', 'FTR', 'GAS', 'GD', 'GE', 'GGP', 'GILD', 'GIS', 'GLW', 'GM', 'GME', 'GOOG', 'GOOGL', 'GPC', 'GPS', 'GRMN', 'GS', 'GT', 'GWW', 'HAL', 'HAR', 'HAS', 'HBAN', 'HBI', 'HCA', 'HCN', 'HCP', 'HD', 'HES', 'HIG', 'HOG', 'HOLX', 'HON', 'HOT', 'HP', 'HPE', 'HPQ', 'HRB', 'HRL', 'HRS', 'HSIC', 'HST', 'HSY', 'HUM', 'IBM', 'ICE', 'IFF', 'ILMN', 'INTC', 'INTU', 'IP', 'IPG', 'IR', 'IRM', 'ISRG', 'ITW', 'IVZ', 'JBHT', 'JCI', 'JEC', 'JNJ', 'JNPR', 'JPM', 'JWN', 'K', 'KEY', 'KHC', 'KIM', 'KLAC', 'KMB', 'KMI', 'KMX', 'KO', 'KORS', 'KR', 'KSS', 'KSU', 'L', 'LB', 'LEG', 'LEN', 'LH', 'LLL', 'LLTC', 'LLY', 'LM', 'LMT', 'LNC', 'LOW', 'LRCX', 'LUK', 'LUV', 'LVLT', 'LYB', 'M', 'MA', 'MAC', 'MAR', 'MAS', 'MAT', 'MCD', 'MCHP', 'MCK', 'MCO', 'MDLZ', 'MDT', 'MET', 'MHK', 'MJN', 'MKC', 'MLM', 'MMC', 'MMM', 'MNK', 'MNST', 'MO', 'MON', 'MOS', 'MPC', 'MRK', 'MRO', 'MS', 'MSFT', 'MSI', 'MTB', 'MU', 'MUR', 'MYL', 'NAVI', 'NBL', 'NDAQ', 'NEE', 'NEM', 'NFLX', 'NFX', 'NI', 'NKE', 'NLSN', 'NOC', 'NOV', 'NRG', 'NSC', 'NTAP', 'NTRS', 'NUE', 'NVDA', 'NWL', 'NWS', 'NWSA', 'O', 'OI', 'OKE', 'OMC', 'ORCL', 'ORLY', 'OXY', 'PAYX', 'PBCT', 'PBI', 'PCAR', 'PCG', 'PCLN', 'PDCO', 'PEG', 'PEP', 'PFE', 'PFG', 'PG', 'PGR', 'PH', 'PHM', 'PKI', 'PLD', 'PM', 'PNC', 'PNR', 'PNW', 'PPG', 'PPL', 'PRGO', 'PRU', 'PSA', 'PSX', 'PVH', 'PWR', 'PX', 'PXD', 'PYPL', 'QCOM', 'QRVO', 'R', 'RAI', 'RCL', 'REGN', 'RF', 'RHI', 'RHT', 'RIG', 'RL', 'ROK', 'ROP', 'ROST', 'RRC', 'RSG', 'RTN', 'SBUX', 'SCG', 'SCHW', 'SE', 'SEE', 'SHW', 'SIG', 'SJM', 'SLB', 'SLG', 'SNA', 'SNDK', 'SNI', 'SO', 'SPG', 'SPLS', 'SRCL', 'SRE', 'STI', 'STJ', 'STT', 'STX', 'STZ', 'SWK', 'SWKS', 'SWN', 'SYF', 'SYK', 'SYMC', 'SYY', 'T', 'TAP', 'TDC', 'TE', 'TEL', 'TGNA', 'TGT', 'THC', 'TIF', 'TJX', 'TMK', 'TMO', 'TRIP', 'TROW', 'TRV', 'TSCO', 'TSN', 'TSO', 'TSS', 'TWC', 'TWX', 'TXN', 'TXT', 'TYC', 'UA', 'UAL', 'UDR', 'UHS', 'UNH', 'UNM', 'UNP', 'UPS', 'URBN', 'URI', 'USB', 'UTX', 'V', 'VAR', 'VFC', 'VIAB', 'VLO', 'VMC', 'VNO', 'VRSK', 'VRSN', 'VRTX', 'VTR', 'VZ', 'WAT', 'WBA', 'WDC', 'WEC', 'WFC', 'WFM', 'WHR', 'WLTW', 'WM', 'WMB', 'WMT', 'WRK', 'WU', 'WY', 'WYN', 'WYNN', 'XEC', 'XEL', 'XL', 'XLNX', 'XOM', 'XRAY', 'XRX', 'XYL', 'YHOO', 'YUM', 'ZBH', 'ZION', 'ZTS']
        mammoth = buildPortfolio(symbols)
        for i in mammoth.stocks:
            i.objId = len(objRef)
            objRef[i.objId] = i
        aWholeNewMammoth()
    objId = 0
    for i in mammoth.stocks:
        objRef[objId] = i
        i.objId = objId
        objId += 1
        for j in i.options:
            objRef[objId] = j
            j.objId = objId
            objId += 1
#    makeReservation('accountDetails')

def reset():
    pass

def ready():
    try:
        mammoth
    except NameError:
        initialize()
    lastActivity()

def aWholeNewMammoth():
    ready()
    for i in mammoth.stocks:
        getStockDetails(i)
    while callMonitor():
        sleep(1)
    for i in mammoth.stocks:
        refreshHistoricalData(i)
    for i in mammoth.stocks:
        getOptionDetails(i)
    while callMonitor():
        sleep(1)
    pickler(mammoth, 'portfolio')

def updateMammoth():
    ready()
    for i in mammoth.stocks:
#        removeExpiredContracts(i)
        makeReservation('stockDetails', i)
        makeReservation('historicalData', i)
    while reservations or callMonitor():
        nextReservation()
        sleep(0.05)
    for i in mammoth.stocks:
        makeReservation('optionDetails', i)
        nextReservation()
        while callMonitor():
            sleep(1)

def lastActivity():
    global lastActive
    lastActive = datetime.now()

def connect():
    global con
    con = ibConnection(port=7496, clientId=1618)
    # 7496 for real account, 7497 for paper trader
    con.registerAll(allMessageHandler)
    con.register(accountDetailsHandler, 'UpdateAccountValue')
    con.register(positionsHandler, 'UpdatePortfolio')
    con.register(accountDetailsEnder, 'AccountDownloadEnd')
    con.register(marketDataHandler, message.tickPrice)
    con.register(contractDetailsHandler, 'ContractDetails')
    con.register(contractDetailsEnder, 'ContractDetailsEnd')
    con.register(historicalDataHandler, message.historicalData)
    con.connect()

def disconnect():
    con.disconnect()

def check():
    try:
        con
    except NameError:
        connect()
    if not con.m_connected:
        connect()

def allMessageHandler(msg):
#    print(msg)
    lastActivity()

###############################################################################
#   PORTFOLIO DATA
###############################################################################

def updateAccountDetails(attribute, value):
    eString = 'mammoth%s = value' % attribute
    exec(eString)

def updatePositions(openPositions):
    i = 0
    while i < len(mammoth.openPositions):
        dupe = False
        j = 0
        while j < len(openPositions):
            if mammoth.openPositions[i].contract.m_conId == openPositions[j].contract.m_conId:
                mammoth.openPositions[i].contract = openPositions[j].contract
                mammoth.openPositions[i].position = openPositions[j].position
                openPositions.pop(j)
                dupe = True
                break
            else:
                j += 1
        if not dupe:
            mammoth.openPositions[i].position = 0
            mammoth.openPositions.pop(i)
        else:
            i += 1
    for k in openPositions:
        sDupe = False
        oDupe = False
        for i in mammoth.stocks:
            if i.symbol == k.symbol:
                if k.secType == 'STK':
                    i.position = k.position
                    i.contract = k.contract
                    mammoth.openPositions.append(i)
                    sDupe = True
                    break
                elif k.secType == 'OPT':
                    for j in i.options:
                        if j.contract.m_conId == k.contract.m_conId:
                            j.position = k.position
                            j.active = True
                            j.contract = k.contract
                            mammoth.openPositions.append(j)
                            oDupe = True
                            break
        if not sDupe:
            thisStock = newStock(mammoth, k.symbol)
            thisStock.objId = len(objRef)
            objRef[thisStock.objId] = thisStock
            thisStock.position = k.position
            thisStock.contract = k.contract
            mammoth.openPositions.append(thisStock)
            makeReservation('stockDetails', thisStock)
            makeReservation('historicalData', thisStock)
            makeReservation('optionDetails', thisStock)
        if not oDupe:
            for i in mammoth.stocks:
                if i.symbol == k.symbol:
                    thisStock = i
            thisOption = newOption(thisStock, k.contract)
            thisOption.objId = len(objRef)
            objRef[thisOption.objId] = thisOption
            thisOption.position = k.position
            thisOption.contract = k.contract
            mammoth.openPositions.append(thisOption)

def getAccountDetails():
    check()
    global opens
    opens = []
    callMonitor(88888888, True)
    con.reqAccountUpdates(True, 'U1385930')

def accountDetailsHandler(msg):
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
    try:
        updateAccountDetails(attribute, value)
    except UnboundLocalError:
        pass

def positionsHandler(msg):
    if msg.contract.m_secType == 'STK':
        thisObject = stock(msg.contract.m_symbol)
    elif msg.contract.m_secType == 'OPT':
        thisObject = option(msg.contract.m_symbol, msg.contract.m_strike, msg.contract.m_expiry)
    thisObject.contract = msg.contract
    thisObject.position = msg.position
    opens.append(thisObject)

def accountDetailsEnder(msg):
    callMonitor(88888888, False)
    updatePositions(opens)
    del opens
    con.reqAccountUpdates(False, 'U1385930')

###############################################################################
#   CONTRACT DATA
###############################################################################

def updateStockDetails(objId, contract, industry):
    global objRef
    thisStock = objRef[objId]
    thisStock.contract = contract
    thisStock.industry = industry

def updateOptionDetails(objId, contract):
    thisStock = objRef[objId]
    if contract.m_conId:
        dupe = False
        for i in thisStock.options:
            if i.contract.m_conId == contract.m_conId:
                thisOption = i
                dupe = True
                break
        if not dupe:
            thisOption = newOption(thisStock, contract)
            thisOption.objId = len(objRef)
            objRef[thisOption.objId] = thisOption
        thisOption.active = activeContract(contract, thisStock)

def activeContract(contract, stockObject):
    dayVol = stockObject.historicalVolatility / math.sqrt(250)
    last = stockObject.last
    strike = contract.m_strike
    expiry = dateStringConverter(contract.m_expiry)
    if expiry < datetime.now():
        active = False
        return active
    t = weekdaysUntil(expiry)
    tq = math.sqrt(t)
    tooHigh = (strike > last * (1 + dayVol * tq * 2))
    tooLow = (strike < last * (1 - dayVol * tq * 2))
    tooFar = (t > 40)
    active = (not tooHigh) and (not tooLow) and (not tooFar)
    return active

def getStockDetails(stockObject):
    check()
    reqId = stockObject.objId
    callMonitor(reqId, True)
    con.reqContractDetails(reqId, stockObject.contract)

def getOptionDetails(stockObject):
    check()
    reqId = stockObject.objId
    contract = newContract(stockObject.symbol, 'OPT', optType='PUT')
    callMonitor(reqId, True)
    con.reqContractDetails(reqId, contract)

def contractDetailsHandler(msg):  # reqId is for underlying stock
    thisContract = msg.contractDetails.m_summary
    if thisContract.m_secType == 'STK':
        updateStockDetails(msg.reqId, thisContract, msg.contractDetails.m_industry)
    elif thisContract.m_secType == 'OPT':
        updateOptionDetails(msg.reqId, thisContract)

def contractDetailsEnder(msg):
    callMonitor(msg.reqId, False)

###############################################################################
#   MARKET DATA
###############################################################################

def updateMarketData(objId, attribute, value):
    thisObject = objRef[objId]
    eString = 'thisObject%s = value' % attribute
    exec(eString)
    if thisObject.secType == 'STK':
        stockDataProcessor(thisObject)
    elif thisObject.secType == 'OPT':
        optionDataProcessor(thisObject)

def getMarketData(marketObject, subscription=False):
    check()
    marketObject.subscription = subscription
    snapshot = not subscription
    callMonitor(marketObject.objId, True, timeout=5)
    con.reqMktData(marketObject.objId, marketObject.contract, '', snapshot)

def marketDataHandler(msg):
    callMonitor(msg.tickerId, False)
    thisObject = objRef[msg.tickerId]
    if msg.field == 1:
        attribute = '.bid'
        value = msg.price
    elif msg.field == 2:
        attribute = '.ask'
        value = msg.price
    elif msg.field == 4:
        attribute = '.last'
        value = msg.price
    elif msg.field == 6:
        pass
        #        attribute = '.high'
        #        value = msg.price
    elif msg.field == 7:
        pass
        #        attribute = '.low'
        #        value = msg.price
    elif msg.field == 9:
        attribute = '.close'
        value = msg.price
    updateMarketData(msg.tickerId, attribute, value)

###############################################################################
#   HISTORICAL DATA
###############################################################################

def refreshHistoricalData(marketObject):
    for increment in range(2):
            getHistoricalData(marketObject, increment)
            sleep(30.1)

def updateHistoricalData(objId, date, dataType, data):  # reqId is for underlying
    thisObject = objRef[objId]
    try:
        thisObject.historicalData[date]
    except KeyError:
        thisObject.historicalData[date] = historicalData(date)
        exec('thisObject.historicalData[date]%s = data') % dataType

def findHistoricalVolatility(stockObject):
    keepGoing = True
    thisDate = datetime.today()
    for i in stockObject.historicalData:
        dateString = thisDate.strftime('%Y%m%d')
        try:
            stockObject.historicalVolatility = (stockObject.historicalData[dateString].historicalVolatility.close)
            break
        except KeyError:
            thisDate = (thisDate - timedelta(days=1))

def getHistoricalData(marketObject, increment):
    check()
    contract = marketObject.contract
    durationStr = '5 Y'
    barSizeSetting = '1 day'
    useRTH = 1
    formatDate = 1
    daysAgo = 1800 * increment
    endDateTime = (datetime.today() - timedelta(days=daysAgo)).strftime("%Y%m%d %H:%M:%S %Z")
#    endDateTime = datetimeConverter()

    whatToShow = 'TRADES'
    reqId = marketObject.objId + 10000000
    callMonitor(reqId, True)
    con.reqHistoricalData(reqId, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate)

    whatToShow = 'HISTORICAL_VOLATILITY'
    reqId = marketObject.objId + 60000000
    callMonitor(reqId, True)
    con.reqHistoricalData(reqId, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate)

    whatToShow = 'OPTION_IMPLIED_VOLATILITY'
    reqId = marketObject.objId + 70000000
    callMonitor(reqId, True)
    con.reqHistoricalData(reqId, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate)

def historicalDataHandler(msg):  # reqId is for underlying
    objId = msg.reqId % 10000000
    if msg.date[:8] == 'finished':
        callMonitor(msg.reqId, False)
        findHistoricalVolatility(objRef[objId])
    else:
        thisData = dataFormat()
        date = msg.date
        if 1 == msg.reqId // 10000000:
            dataType = '.trades'
        elif 6 == msg.reqId // 10000000:
            dataType = '.historicalVolatility'
        elif 7 == msg.reqId // 10000000:
            dataType = '.impliedVolatility'
        thisData.open = msg.open
        thisData.high = msg.high
        thisData.low = msg.low
        thisData.close = msg.close
        thisData.volume = msg.volume
        thisData.count = msg.count
        thisData.WAP = msg.WAP
        updateHistoricalData(objId, date, dataType, thisData)

###############################################################################
#   CALL MANAGEMENT
###############################################################################

class reservation(object):
    def __init__(self, callType, marketObject, time, special):
        self.callType = callType
        self.marketObject = marketObject
        self.time = time
        self.special = special
        if callType == 'accountDetails':
            self.objId = 88888888
        else:
            self.objId = marketObject.objId

def makeReservation(callType, marketObject=None, delay=0, special=0):
    global reservations
    try:
        reservations
    except NameError:
        reservations = []
    time = datetime.now() + timedelta(seconds=delay)
    thisReservation = reservation(callType, marketObject, time, special)
    j = 0
    for i in reservations:
        j += 1
        if time > i.time:
            j -= 1
            break
    reservations.insert(j,thisReservation)

def nextReservation():
    i = len(reservations) - 1
    while reservations:
        try:
            cooker[reservations[i].objId]
            proceed = False
        except KeyError:
            proceed = True
#            try:  # check for outstanding impVol call
#                cooker[reservations[i].objId + 70000000]
#                proceed = False
#            except KeyError:
#                pass
        except NameError:
            proceed = True
        if proceed:
            thisReservation = reservations.pop(i)
            if thisReservation.callType == 'accountDetails':
                getAccountDetails()
            if thisReservation.callType == 'stockDetails':
                getStockDetails(thisReservation.marketObject)
            if thisReservation.callType == 'optionDetails':
                getOptionDetails(thisReservation.marketObject)
            if thisReservation.callType == 'marketData':
                getMarketData(thisReservation.marketObject)
            if thisReservation.callType == 'historicalData':
                getHistoricalData(thisReservation.marketObject, thisReservation.special)
            break
        else:
            i -= 1
            if i < 0:
                i = len(reservations) - 1

def callMonitor(callId=None, monitorCall=True, timeout=100):
    # leave callId blank to return number of outstanding calls
    global cooker
    try:
        cooker
    except NameError:
        cooker = {}
    trash = []
    for k, v in cooker.iteritems():
        if v < datetime.now():
            trash.append(k)
            print('callId %d timed out') % k
    while trash:
        del cooker[trash.pop()]
    if callId is not None:
        if not monitorCall:
            try:
#                sElapsed = (datetime.now() - cooker[callId]).seconds
#                msElapsed = (datetime.now() - cooker[callId]).microseconds / 1000
                del cooker[callId]
                print('resolved callId %d') % callId
#                if sElapsed == 0:
#                    print('resolved callId %d in $d ms') % (callId, msElapsed)
#                else:
#                    print('resolved callId %d in %d.%d sec') % (callId, sElapsed, msElapsed)
            except KeyError:
                pass
        else:
            while len(cooker) >= 100:
                sleep(0.1)
                trash = []
                for k, v in cooker.iteritems():
                    if v < datetime.now():
                        trash.append(k)
                        print('callId %d timed out') % k
                while trash:
                    del cooker[trash.pop()]
                print('waiting to add callId %d') % callId
            try:
                cooker[callId]
            except KeyError:
                cooker[callId] = datetime.now() + timedelta(seconds=timeout)
                print('monitoring callId %d') % callId
    else:
        return len(cooker)

###############################################################################
#   PROCESSORS
###############################################################################

def stockDataProcessor(stockObject):
    # update target price for each expiry (quote --> neural network)
    for expiry, target in stockObject.target.iteritems():
        stockObject.target[expiry] = newTarget(expiry, stockObject)
    # update option EVs (numpy based on volatility)
#    for j in stockObject.options:
#        j.expectedValue = optionValue(j)

def optionDataProcessor(optionObject):
    pass
    # update EV
    # update Annualized Return
    #

###############################################################################
#   PROGRAM
###############################################################################

if __name__ == "__main__":
 #   ready()
#    print('Done.')
#    sleep(8)
#    woolly()
 #   resetContractDetails(mammoth)
#    symbols = ['BAC', 'AXP', 'GSK', 'COF', 'CAT', 'MSFT', 'AAPL']
#    symbols = ['COF', 'CAT', 'MSFT']
#    symbols = ['TSLA', 'NKE', 'NFLX', 'AAPL']
#    buildPortfolio(symbols)
#    ready()
#    for i in mammoth.stocks:
#        getStockDetails(i)
#    while callMonitor():
#        sleep(0.1)

    initialize()
#    timeout = timedelta(seconds=1)
#    while datetime.now() < lastActive + timeout or callMonitor() or reservations:
#        nextReservation()
#        sleep(0.1)
#    refreshHistoricalData(mammoth)
#    while callMonitor():
#        sleep(1)
#    pickler(mammoth, 'portfolio')

#    initialize()
#    pickler(mammoth, 'portfolio')
#    initialize()
#    mammoth = unPickler('portfolio')
 #   for i in mammoth.stocks:
 #       print(str(len(i.options)) + ' options in ' + i.symbol)
 #   for j in mammoth.openPositions:
 #       print('%d %s %d %s %s') % (j.position, j.symbol, j.strike, j.optType, j.expiry)
#        for j in i.options:
#            print(str(j.symbol) + ' ' + str(j.expiry) + ' ' + str(j.strike))

#    for i in mammoth.stocks:
#        removeExpiredContracts(i)

    for i in mammoth.stocks:
        print('%d options in %s') % (len(i.options), i.symbol)
        print('%d days of history for %s') % (len(i.historicalData), i.symbol)

#    print(subscriptions)
#    pickler(mammoth, 'portfolio')
