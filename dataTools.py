import cPickle


def pickler(thisObject, pickledName):
    pickledFilename = pickledName + '.pickle'
    with open(pickledFilename, 'wb') as pickledObject:
        cPickle.dump(thisObject, pickledObject)


def unPickler(pickledName):
    pickledFilename = pickledName + '.pickle'
    with open(pickledFilename, 'rb') as pickledObject:
        thisObject = cPickle.load(pickledObject)
    return thisObject
