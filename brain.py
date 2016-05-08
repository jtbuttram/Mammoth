from scipy import stats
import math
from logicTools import weekdaysUntil, dateConverter
from dataTools import pickler, unPickler
from datetime import datetime, timedelta


def newTarget(expiry, stockObject):
    # this is where the neural network goes
    newTarget = stockObject.last
    return newTarget


def optionValue(optionObject):
    stockObject = optionObject.underlying
    optType = optionObject.optType
    expiry = optionObject.expiry
    target = optionObject.underlying.target[expiry]
    strike = optionObject.strike
    volatility = stockObject.impliedVolatility
    optionValue = blackScholes(optType, target, strike, expiry, volatility)
    return optionValue


def blackScholes(optType, target, strike, expiry, volatility, riskFreeRate=0,
                 dividend=0):
    if optType == 'PUT':
        cp = -1
    elif optType == 'CALL':
        cp = 1
    s = target  # initial stock price
    k = strike  # strike price
    t = weekdaysUntil(expiry)  # expiration time
    v = volatility
    rf = riskFreeRate
    div = dividend
    d1 = ((math.log(s / k) + (rf - div + 0.5 * math.pow(v, 2)) * t) /
          (v * math.sqrt(t)))
    d2 = d1 - v * math.sqrt(t)
    optionPrice = ((cp * s * math.exp(-div * t) * stats.norm.cdf(cp * d1)) -
                   (cp * k * math.exp(-rf * t) * stats.norm.cdf(cp * d2)))
    return optionPrice

def impliedVolatility():
    pass

def translateHistoricalData():
    thisPortfolio = unPickler('portfolio')
    oneDay = timedelta(days=1)
    thisData = []
    for s in thisPortfolio.stocks:
        dataMap = []
        day = datetime.today()
        gap = 0
        while gap < 30:
            dayStr = dateConverter(day)
            try:
                s.historicalData[dayStr]
                dataMap.append(dayStr)
                gap = 0
            except KeyError:
                gap += 1
            day -= oneDay
        dataLen = len(dataMap)
        daysHist = 250
        if dataLen > daysHist:
            for i in range(dataLen - daysHist):
                inputData = []
                outputData = []
                h = s.historicalData[dataMap[i]]
                hd = h.trades
                outputData.append([hd.open])
                outputData.append([hd.high])
                outputData.append([hd.low])
                outputData.append([hd.close])
                outputData.append([hd.volume])
                outputData.append([hd.count])
                outputData.append([hd.WAP])
                hd = h.historicalVolatility
                outputData.append([hd.open])
                outputData.append([hd.high])
                outputData.append([hd.low])
                outputData.append([hd.close])
                outputData.append([hd.volume])
                outputData.append([hd.count])
                outputData.append([hd.WAP])
                hd = h.impliedVolatility
                outputData.append([hd.open])
                outputData.append([hd.high])
                outputData.append([hd.low])
                outputData.append([hd.close])
                outputData.append([hd.volume])
                outputData.append([hd.count])
                outputData.append([hd.WAP])
#                for hd in [h.trades, h.historicalVolatility, h.impliedVolatility]:
#                    for hdd in [hd.open, hd.high, hd.low, hd.close, hd.volume, hd.count, hd.WAP]:
#                        outputData.append([hdd])
                for j in range(daysHist):
                    h = s.historicalData[dataMap[i + j + 1]]
                    hd = h.trades
                    inputData.append([hd.open])
                    inputData.append([hd.high])
                    inputData.append([hd.low])
                    inputData.append([hd.close])
                    inputData.append([hd.volume])
                    inputData.append([hd.count])
                    inputData.append([hd.WAP])
                    hd = h.historicalVolatility
                    inputData.append([hd.open])
                    inputData.append([hd.high])
                    inputData.append([hd.low])
                    inputData.append([hd.close])
                    inputData.append([hd.volume])
                    inputData.append([hd.count])
                    inputData.append([hd.WAP])
                    hd = h.impliedVolatility
                    inputData.append([hd.open])
                    inputData.append([hd.high])
                    inputData.append([hd.low])
                    inputData.append([hd.close])
                    inputData.append([hd.volume])
                    inputData.append([hd.count])
                    inputData.append([hd.WAP])
#                    for hd in [h.trades, h.historicalVolatility, h.impliedVolatility]:
#                        for hdd in [hd.open, hd.high, hd.low, hd.close, hd.volume, hd.count, hd.WAP]:
#                            inputData.append([hdd])
                thisData.append((inputData, outputData))
        print(len(thisData))
    pickler(thisData, 'trainingData')


if __name__ == "__main__":
    translateHistoricalData()