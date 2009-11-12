from FeatureServer.DataSource import DataSource, Lock
import anydbm, UserDict
try:
    import cPickle as Pickle
except ImportError:
    import Pickle

class DBM (DataSource):
    """Simple datasource using the anydbm module and pickled datastructures."""
    def __init__(self, name, writable = 0, lockfile = None, **args):
        DataSource.__init__(self, name, **args)
        self.db = Recno( args["file"] )
        self.append = self.db.append
        self.writable = int(writable)
        if self.writable and lockfile:
            self.lock = Lock(lockfile)
        else:
            self.lock = None

    def __iter__ (self):
        return self.db.__iter__()

    def begin (self):
        if self.lock: return self.lock.lock()

    def commit (self):
        if hasattr(self.db, "sync"): self.db.sync()
        if self.lock: self.lock.unlock()

    def rollback (self):
        if self.lock: self.lock.unlock()

    def create (self, action):
        thunk = self.thaw_feature(action.feature)
        action.id = self.append(thunk)
        return self.select(action)

    def update (self, action):
        self.db[action.id] = self.thaw_feature(action.feature)
        return self.select(action)
        
    def delete (self, action):
        feature = action.feature
        if action.id:
            del self.db[action.id]
        elif action.attributes:
            for feat in self.select(action):
                del self.db[feat.id]
        return []

    def select (self, action):
        def _overlap (a, b):
            return a[2] >= b[0] and \
                   b[2] >= a[0] and \
                   a[3] >= b[1] and \
                   b[3] >= a[1]

        if action.id:
            feature = self.freeze_feature( self.db[action.id] )
            feature.id = action.id
            return [feature]
        else:
            result = []
            count  = action.maxfeatures
            counter = 0
            for id in self:
                if counter < action.startfeature:
                    counter += 1
                    continue
                thunk = self.db[id]
                feature = self.freeze_feature(thunk)
                feature.id = id
                if action.bbox and not _overlap(action.bbox, feature.bbox):
                    continue
                if action.attributes:
                    props = feature.properties
                    skip  = False
                    for key, val in action.attributes.items():
                        if (key not in props and val is not None) or \
                           (key in props and str(props[key]) != val):
                            skip = True
                            break
                    if skip: continue
                result.append(feature)
                if count is not None:
                    count -= 1
                    if not count: break
            return result

    def freeze_feature (self, thunk):
        return Pickle.loads(thunk)

    def thaw_feature (self, feature):
        feature.bbox = feature.get_bbox()
        return Pickle.dumps(feature)

class Recno (object):
    """Class to handle managment of the database file.""" 
    class Iterator (object):
        def __init__ (self, recno, idx = 0):
            self.recno = recno
            self.idx = self.recno.max + 1
            self.stopIdx = idx
        
        def __iter__ (self):
            return self

        def next (self):
            while True:
                self.idx -= 1
                if self.idx == 0 or self.idx == self.stopIdx:
                    raise StopIteration
                if not self.recno.has_key(self.idx):
                    continue
                return self.idx

    def __init__(self, file):
        self.data  = anydbm.open( file, "c" )
        self.file  = file
        self.max   = 0
        if self.data.has_key("_"):
            self.max = int(self.data["_"])

    def __getitem__ (self, key):
        return self.data[str(key)]

    def __setitem__ (self, key, val):
        self.data[str(key)] = val
        if key > self.max: self.max = key

    def __delitem__ (self, key):
        del self.data[str(key)]

    def __len__ (self):
        return len(self.data)

    def __iter__ (self):
        return self.Iterator(self)

    def has_key (self, key):
        return self.data.has_key(str(key))

    def sync (self):
        self.data["_"] = str(self.max)
        del self.data
        self.data  = anydbm.open( self.file, "c" )

    __del__ = sync

    def append (self, val):
        self.max += 1
        self.__setitem__(self.max, val)
        return self.max
