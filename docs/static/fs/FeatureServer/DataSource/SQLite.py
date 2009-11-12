import re, copy
from FeatureServer.DataSource import DataSource , Feature
try:
    import sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3

class SQLite (DataSource):
    """Similar to the PostGIS datasource. Works with the 
       built in sqlite in Python2.5+, or with pysqlite2."""
    wkt_linestring_match = re.compile(r'\(([^()]+)\)')

    def __init__(self, name, srid = 4326, order=None, writable = True, **args):
        DataSource.__init__(self, name, **args)
        self.table      = args["layer"]
        self.fid_col    = 'feature_id'
        self.geom_col   = 'wkt_geometry'
        self.order      = order
        self.srid       = srid # not used now...
        self.db         = None
        self.dsn        = args["dsn"]
        self.writable   = writable

    def begin (self):
        self.db = sqlite3.connect(self.dsn)
        # allow both dictionary and integer index lookups.
        self.db.row_factory = sqlite3.Row

        # create the table if it doesnt exist.
        if not self.table in self.tables():
            c = self.db.cursor()
            c.executescript(self.schema())

    def tables(self):
        c = self.db.cursor()
        res = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return [r[0] for r in res]

    def schema(self):
        return """\
CREATE TABLE '%s' (
    feature_id   INTEGER PRIMARY KEY,
    xmin INTEGER,
    ymin INTEGER,
    xmax INTEGER,
    ymax INTEGER,
    wkt_geometry VARCHAR
);
CREATE TABLE '%s_attrs' (
    id     INTEGER PRIMARY KEY,
    feature_id  INTEGER,
    title  VARCHAR(256),
    key    VARCHAR(256),
    value TEXT
);    
CREATE INDEX %s_xmin_idx on %s (xmin);
CREATE INDEX %s_xmax_idx on %s (xmax);
CREATE INDEX %s_ymin_idx on %s (ymin);
CREATE INDEX %s_ymax_idx on %s (ymax);
CREATE INDEX %s_attrs_title_idx on %s_attrs (title);
CREATE INDEX %s_attrs_feature_id on %s_attrs (feature_id);
CREATE INDEX %s_attrs_%s_key on %s_attrs (key);\
        """ % ((self.table,) * 17)

    def commit (self):
        if self.writable:
            self.db.commit()
        self.db.close()

    def rollback (self):
        if self.writable:
            self.db.rollback()
        self.db.close()

    def column_names (self, feature):
        return feature.properties.keys()

    def value_formats (self, feature):
        values = ["%%(%s)s" % self.geom_col]
        values = []
        for key, val in feature.properties.items():
            valtype = type(val).__name__
            valfmt  = {"unicode": "s", "str": "s", "int": "d", "float": "f",
                       "NoneType": "s"}[valtype]
            fmt     = "%%(%s)%s" % (key, valfmt)
            values.append(fmt)
        return values

    def feature_predicates (self, feature):
        columns = self.column_names(feature)
        values  = self.value_formats(feature)
        predicates = []
        for pair in zip(columns, values):
            if pair[0] != self.geom_col:
                predicates.append("%s = %s" % pair)
            else:
                predicates.append(" %s = %s " % (self.geom_col, self.to_wkt(feature.geometry)))     
        return predicates

    def feature_values (self, feature):
        return copy.deepcopy(feature.properties)

    def to_wkt (self, geom):
        def coords_to_wkt (coords):
            return ",".join(["%f %f" % tuple(c) for c in coords])
        coords = geom["coordinates"]
        if geom["type"] == "Point":
            return "POINT(%s)" % coords_to_wkt(coords)
        elif geom["type"] == "Line":
            return "LINESTRING(%s)" % coords_to_wkt(coords)
        elif geom["type"] == "Polygon":
            rings = ["(" + coords_to_wkt(ring) + ")" for ring in coords]
            rings = ",".join(rings)
            return "POLYGON(%s)" % rings
        else:
            raise Exception("Couldn't create WKT from geometry of type %s (%s). Only Point, Line, Polygon are supported." % (geom['type'], geom)) 

    def from_wkt (self, geom):
        coords = []
        for line in self.wkt_linestring_match.findall(geom):
            ring = []
            for pair in line.split(","):         
                ring.append(map(float, pair.split(" ")))
            coords.append(ring)
        if geom.startswith("POINT"):
            geomtype = "Point"
            coords = coords[0]
        elif geom.startswith("LINESTRING"):
            geomtype = "Line"
            coords = coords[0]
        elif geom.startswith("POLYGON"):
            geomtype = "Polygon"
        else:
            geomtype = geom[:geom.index["("]]
            raise Error("Unsupported geometry type %s" % geomtype)
        return {"type": geomtype, "coordinates": coords}

    def create (self, action):
        feature = action.feature
        bbox = feature.get_bbox()

        columns = ", ".join([self.geom_col,'xmin,ymin,xmax,ymax'])
        values = [self.to_wkt(feature.geometry)] + list(bbox) 
        sql = "INSERT INTO \"%s\" (%s) VALUES (?,?,?,?,?)" % ( self.table, columns)
        cursor = self.db.cursor()
        res = cursor.execute(str(sql), values)
        action.id = res.lastrowid

        insert_tuples = [(res.lastrowid, k, v) for k,v in feature.properties.items() if k != 'title']
        if 'title' in feature.properties:
            insert_tuples.append((res.lastrowid, 'title', feature.properties['title']))
        sql = "INSERT INTO \"%s_attrs\" (feature_id, key, value) VALUES (?, ?, ?)" % (self.table,) 
        cursor.executemany(sql,insert_tuples)

        self.db.commit()
        return self.select(action)
        

    def update (self, action):
        feature = action.feature
        predicates = ", ".join( self.feature_predicates(feature) )
        sql = "UPDATE \"%s_attrs\" SET %s WHERE %s = %d" % (
                    self.table, predicates, self.fid_col, action.id )
        cursor = self.db.cursor()
        cursor.execute(str(sql), self.feature_values(feature))
        self.db.commit()
        return self.select(action)
        
    def delete (self, action):
        sql = "DELETE FROM \"%s\" WHERE %s = %%(%s)d" % (
                    self.table, self.fid_col, self.fid_col )
        cursor = self.db.cursor()
        cursor.execute(str(sql), {self.fid_col: action.id})

        sql = "DELETE FROM \"%s_attrs\" WHERE %s = %%(%s)d" % (
                    self.table, self.fid_col, self.fid_col )
        cursor = self.db.cursor()
        cursor.execute(str(sql), {self.fid_col: action.id})
        return []


    def select (self, action):
        cursor = self.db.cursor()

        if action.id:
            sql = "SELECT * FROM \"%s\" WHERE %s = ?" % ( self.table,  self.fid_col)
            cursor.execute(str(sql), (action.id,))
            result = [cursor.fetchone()]
        else:
            filters = []
            attrs   = {}
            if action.bbox:
                filters.append( " %f   > xmin \
                                AND xmax > %f \
                                AND %f   > ymin \
                                AND ymax >  %f \
                                " % (action.bbox[2], action.bbox[0], action.bbox[3], action.bbox[1])
                            ) # just skip sql interpolation since
                              # these have to come from a calculatoin...

            if action.attributes:
                match = Feature(props = action.attributes)
                filters = self.feature_predicates(match)
                attrs = action.attributes

            sql = "SELECT * FROM \"%s\" " % ( self.table, )
            if filters:
                sql += " WHERE " + " AND ".join(filters)
            if self.order:
                sql += self.order
            if action.maxfeatures:
                sql += " LIMIT %d" % action.maxfeatures
            else:   
                sql += " LIMIT 1000"
            if action.startfeature:
                sql += " OFFSET %d" % action.startfeature
            cursor.execute(str(sql), attrs)
            result = cursor.fetchall()

        features = []
        sql = "SELECT key,value FROM \"%s_attrs\" WHERE feature_id = ?" % (self.table,)
        for row in result:
            attrs = cursor.execute(sql, (row['feature_id'],)).fetchall()
            d = dict(attr for attr in attrs)
            geom  = self.from_wkt(row[self.geom_col])
            id = row[self.fid_col]

            if (geom):
                features.append( Feature( id, geom, d ) ) 
        return features
