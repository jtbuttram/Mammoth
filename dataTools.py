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


def dataLoader():
    t = datetime.now()
    thisPortfolio = unPickler('portfolio')
    trainingData = []
    oneDay = timedelta(days=1)
    for s in thisPortfolio.stocks:
        dataMap = []
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
        daysHist = 250
        tMax = 60
        tMin = 1
        for i in range(min(2000, dataLen - daysHist - tMin)):
            targetData = dataShelf[i]
            for t in range(1, min(tMax + 1, dataLen - i - daysHist)):
                todayData = np.array(dataShelf[i + t])
                thisData = []
                thisData.append(np.sqrt(t))
                for x in [17]:  # what raw data to add to the training data
                    thisData.append(todayData.item(x))
                for j in range(daysHist):
                    histData = np.array(dataShelf[i + t + j + 1])
                    hd1 = (histData / todayData) - 1
#                    cleanHD = sigmoid(hd1)
                    for x in [0, 1, 2, 3, 4, 5, 6, 17]:
                        thisData.append(hd1.item(x))
#                npThisData = np.array(thisData)
                inputData = np.reshape(thisData, (2002, 1))
                outputData = targetData[6] / todayData[6]
                trainingData.append((inputData, outputData))
            print('%d data points in training data') % len(trainingData)
        print('stock complete')
    tt = (datetime.now() - t).seconds
    print('the loading process took %d seconds') % tt
    t = datetime.now()
    pickler(trainingData, 'trainingData')
    dt = (datetime.now() - t).seconds
    print('pickling process took %d seconds') % dt


if __name__ == "__main__":
    dataLoader()