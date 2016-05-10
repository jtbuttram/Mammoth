from scipy import stats
import math
from logicTools import weekdaysUntil, dateConverter
from dataTools import pickler, unPickler, dataLoader
from datetime import datetime, timedelta
from time import sleep


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


if __name__ == "__main__":
    dataLoader(100)
    theData = unPickler('trainingData')
    print(theData[0])
    sleep(10)
