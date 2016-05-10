import cPickle
import numpy as np
from datetime import datetime, timedelta
from logicTools import dateConverter


def pickler(thisObject, pickledName):
    pickledFilename = pickledName + '.pickle'
    with open(pickledFilename, 'wb') as pickledObject:
        cPickle.dump(thisObject, pickledObject)


def unPickler(pickledName):
    pickledFilename = pickledName + '.pickle'
    with open(pickledFilename, 'rb') as pickledObject:
        thisObject = cPickle.load(pickledObject)
    return thisObject


def sigmoid(z):
    """The sigmoid function."""
    return 1.0/(1.0+np.exp(-z))

def stepper(step):
    return 1 + np.random.random() * (step - 1) * 2


def dataLoader(sampleSize):
    T = datetime.now()
    daysHist = 250
    tMax = 50
    tMin = 1
    tNum = (tMax + 1 - tMin)
    n = 0
    thisPortfolio = unPickler('portfolio')
    for i in thisPortfolio.stocks:
        n += (len(i.historicalData) - daysHist - tMax - 1)
    step = n * tNum / float(sampleSize)
    print('step size is %d') % step
    trainingData = []
    oneDay = timedelta(days=1)
    for s in thisPortfolio.stocks:
        dataShelf = []
        day = datetime.today()
        gap = 0
        while gap < 30:
            dayStr = dateConverter(day)
            try:
                h = s.historicalData[dayStr]
                thisData = []
                for hd in [h.trades, h.historicalVolatility, h.impliedVolatility]:
                    for hdd in [hd.open, hd.high, hd.low, hd.close, hd.volume, hd.count, hd.WAP]:
                        thisData.append([hdd])
                        '''
                        DATA INDEX:
                                trades  histVol impVol
                        open    0       7       14
                        high    1       8       15
                        low     2       9       16
                        close   3       10      17
                        volume  4       11      18
                        count   5       12      19
                        WAP     6       13      20
                        '''
                dataShelf.append(thisData)
                gap = 0
            except KeyError:
                gap += 1
            day -= oneDay
        dataLen = len(dataShelf)
        print('dataShelf is %d long') % dataLen
        c = stepper(step)
        i = int(c // tNum)
        while i < (dataLen - daysHist - tMax - 1):
            #print('c is %d') % c
            #print('i is %d') % i
            i = int(c // tNum)
            t = int(c % tNum) + tMin
            targetData = np.array(dataShelf[i])
            todayData = np.array(dataShelf[i + t])
            thisData = []
            thisData.append(np.sqrt(t))
            for x in [17]:  # what raw data to add to the training data
                thisData.append(todayData.item(x))
            for j in range(daysHist):
                histData = np.array(dataShelf[i + t + j + 1])
                hd1 = (histData / todayData) - 1
                # cleanHD = sigmoid(hd1)
                for x in [0, 1, 2, 3, 4, 5, 6, 17]:
                    thisData.append(hd1.item(x))
            npThisData = np.array(thisData)
            inputData = np.reshape(npThisData, (2002, 1))
            outputData = targetData.item(6) / todayData.item(6)
            trainingData.append((inputData, outputData))
            c += stepper(step)
        print('stock complete; %d data points in training data') % len(trainingData)
    tt = (datetime.now() - T).seconds
    print('the loading process took %d seconds') % tt
    T = datetime.now()
    pickler(trainingData, 'trainingData')
    dt = (datetime.now() - T).seconds
    print('pickling process took %d seconds') % dt
