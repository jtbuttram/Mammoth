import pickle


def pickler(thisObject, pickledName):
    pickledFilename = pickledName + '.pickle'
    with open(pickledFilename, 'wb') as pickledObject:
        pickle.dump(thisObject, pickledObject)


def unPickler(pickledName):
    pickledFilename = pickledName + '.pickle'
    with open(pickledFilename, 'rb') as pickledObject:
        thisObject = pickle.load(pickledObject)
    return thisObject
