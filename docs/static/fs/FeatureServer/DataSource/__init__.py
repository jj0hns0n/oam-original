import os, warnings, time

class DataSource (object):
    """Base datasource class. Datasources override the create, update, 
       and delete methods to support those actions, and can optionally
       use begin, commit, and rollback methods to perform locking."""
    
    def __init__(self, name, **kwargs):
        self.name = name
        for key, val in kwargs.items():
            setattr(self, key, val)
    def create (self, feature):
        raise NotImplementedError
    def update (self, feature):
        raise NotImplementedError
    def delete (self, feature):
        raise NotImplementedError
    def select (self, params):
        pass
    def begin (self):
        pass
    def commit (self):
        pass
    def rollback (self):
        pass

class Lock (object):
    """Locking method used in several DataSources which do not have
       internal locking mechanisms."""
    def __init__ (self, lock, timeout = 30.0, stale_interval = 300.0):
        self.lockfile = lock
        self.timeout  = float(timeout)
        self.stale    = float(stale_interval)

    def lock (self, blocking = True):
        result = self.attemptLock()
        if result:
            return True
        elif not blocking:
            return False
        while result is not True:
            time.sleep(0.25)
            result = self.attemptLock(tile)
        return True

    def attemptLock (self):
        try: 
            os.makedirs(self.lockfile)
            return True
        except OSError:
            pass
        try:
            st = os.stat(self.lockfile)
            if st.st_ctime + self.stale < time.time():
                warnings.warn("removing stale lock %s" % self.lockfile)
                # remove stale lock
                self.unlock()
                os.makedirs(self.lockfile)
                return True
        except OSError:
            pass
        return False 
     
    def unlock (self):
        try:
            os.rmdir(self.lockfile)
        except OSError, E:
            warnings.warn("unlock %s failed: %s" % (self.lockfile, str(E)))

    __del__ = unlock

class Feature (object):
    def __init__ (self, id = None, geometry = None, props = None):
        self.id         = id
        self.geometry   = geometry or {}
        self.properties = props or {}
        self.bbox       = None

    def get_bbox (self):
        minx = miny = 2**31
        maxx = maxy = -2**31
        try:
            coords = self.geometry["coordinates"]
            if self.geometry["type"] in ("Point", "Line"):
                for coord in coords:
                    if coord[0] < minx: minx = coord[0]
                    if coord[0] > maxx: maxx = coord[0]
                    if coord[1] < miny: miny = coord[1]
                    if coord[1] > maxy: maxy = coord[1]
            else:
                for ring in coords:
                    for coord in ring:
                        if coord[0] < minx: minx = coord[0]
                        if coord[0] > maxx: maxx = coord[0]
                        if coord[1] < miny: miny = coord[1]
                        if coord[1] > maxy: maxy = coord[1]
            return (minx, miny, maxx, maxy)
        except:
            raise Exception("Unable to determine bounding box for feature with geometry %s" % self.geometry)

    def to_dict (self):
        return {"id": self.id,
                "geometry": self.geometry,
                "properties": self.properties}
