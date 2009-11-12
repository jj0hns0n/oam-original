from FeatureServer.DataSource import DataSource, Feature
from FeatureServer.DataSource.OGR import OGR
import psycopg, copy, re, ogr

class PostGIS (DataSource):
    """PostGIS datasource. Setting up the table is beyond the scope of
       FeatureServer."""
    wkt_linestring_match = re.compile(r'\(([^()]+)\)')

    def __init__(self, name, srid = 4326, fid = "ogc_fid", geometry = "wkb_geometry", order = "", writable = True, **args):
        DataSource.__init__(self, name, **args)
        self.table      = args["layer"]
        self.fid_col    = fid
        self.geom_col   = geometry
        self.order      = order
        self.srid       = srid
        self.db         = None
        self.dsn        = args["dsn"]
        self.writable   = writable
    def begin (self):
        self.db = psycopg.connect(self.dsn)

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
                       "NoneType": "s", "bool": "s"}[valtype]
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
        if feature.geometry.has_key("coordinates"):
            predicates.append(" %s = SetSRID('%s'::geometry, %s) " % (self.geom_col, self.to_wkt(feature.geometry), self.srid))     
        return predicates

    def feature_values (self, feature):
        props = copy.deepcopy(feature.properties)
        for key, val in props.iteritems():
            if type(val) is unicode: ### b/c psycopg1 doesn't quote unicode
                props[key] = val.encode('utf-8')
        return props

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

    def from_wkb (self, geom):
        try:
            ogrgeom = ogr.CreateGeometryFromWkb(geom)
            return OGR.freeze_geometry(ogrgeom)
        except:
            return None 

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

    def id_sequence (self):
        return self.table + "_" + self.fid_col + "_seq"

    def create (self, action):
        feature = action.feature
        columns = ", ".join(self.column_names(feature)+[self.geom_col])
        values = ", ".join(self.value_formats(feature)+["SetSRID('%s'::geometry, %s) " % (self.to_wkt(feature.geometry), self.srid)])
        sql = "INSERT INTO \"%s\" (%s) VALUES (%s)" % (
                                        self.table, columns, values)
        cursor = self.db.cursor()
        cursor.execute(str(sql), self.feature_values(feature))
        cursor.execute("SELECT currval('%s');" % self.id_sequence())
        action.id = cursor.fetchone()[0]
        self.db.commit()
        return self.select(action)
        

    def update (self, action):
        feature = action.feature
        predicates = ", ".join( self.feature_predicates(feature) )
        sql = "UPDATE \"%s\" SET %s WHERE %s = %d" % (
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
        return []

    def select (self, action):
        cursor = self.db.cursor()

        if action.id:
            sql = "SELECT AsBinary(%s) as fs_binary_geom_col, * FROM \"%s\" WHERE %s = %%(%s)d" % (
                    self.geom_col, self.table, self.fid_col, self.fid_col )
            cursor.execute(str(sql), {self.fid_col: action.id})
            result = [cursor.fetchone()]
        else:
            filters = []
            attrs   = {}
            if action.bbox:
                filters.append( "%s && SetSRID('BOX3D(%f %f,%f %f)'::box3d, %s) and intersects(%s, SetSRID('BOX3D(%f %f,%f %f)'::box3d, %s))" % (
                                        (self.geom_col,) + tuple(action.bbox) + (self.srid,) + (self.geom_col,) + (tuple(action.bbox) + (self.srid,))))
            if action.attributes:
                match = Feature(props = action.attributes)
                filters = self.feature_predicates(match)
                attrs = action.attributes

            sql = "SELECT AsBinary(%s) as fs_binary_geom_col, * FROM \"%s\"" % (self.geom_col, self.table)
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
            result = cursor.fetchall() # should use fetchmany(action.maxfeatures)

        columns = [desc[0] for desc in cursor.description]
        features = []
        for row in result:
            props = dict(zip(columns, row))
            geom  = self.from_wkb(props['fs_binary_geom_col'])
            id = props[self.fid_col]
	    del props[self.fid_col]
            del props[self.geom_col]
            del props['fs_binary_geom_col']
            for key, value in props.items():
	    	if isinstance(value, str): props[key] = unicode(value, "utf-8")
	    if (geom):
	    	features.append( Feature( id, geom, props ) ) 
        return features
