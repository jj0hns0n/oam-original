from TileCache.Layers.MapServer import MapServer
import os, sys
import psycopg2

class OpenAerialMap (MapServer):
    def __init__(self, name, dsn = None, image_path = "", **kwargs):
        MapServer.__init__(self, name, **kwargs) 
        self.image_path = image_path
        self.dsn = dsn
        self.db  = psycopg2.connect(dsn)
        # XXX FIXME: this belongs on Tile, probably, not here
        self.INCHES_PER_DEGREE = 314982288 # assume 72 DPI

    def get_map(self, tile):
        import mapscript
        wms = MapServer.get_map(self, tile)
        bounds = tile.bounds()
        # XXX FIXME: I don't think this will work with other projections?
        scale  = self.INCHES_PER_DEGREE * (bounds[2]-bounds[0])/tile.size()[0]

        sql    = """SELECT dr.id, layername, data, type, min_scale, max_scale, srs, offsite,
                      ds.name, description, attribution, url
                      FROM view_datarecord dr, view_recordtypes rt,
                           view_datasource ds
                      WHERE type_id = rt.id
                      AND datasource_id = ds.id
                      AND bbox && 'BOX3D(%s %s, %s %s)'::box3d
                      AND %f >= min_scale and %f <= max_scale
                      AND active 
                      ORDER BY data_resolution DESC""" % (bounds + (scale, scale))

        cursor = self.db.cursor()
        cursor.execute(sql)
        for id, name, data, type, min_scale, max_scale, srs, offsite, \
            title, description, attribution, url in cursor:
            raster = mapscript.layerObj(wms)
            raster.name   = "layer_%s" % id
            raster.group  = "world"
            raster.type   = mapscript.MS_LAYER_RASTER
            raster.status = mapscript.MS_DEFAULT
            if srs and type == "WMS":
                raster.setProjection( "+init=" + srs.lower() )
            else:
                raster.setProjection( "+init=" + tile.layer.srs.lower() )
            if offsite:
                offsite = map(int, offsite.split(" "))  
                raster.offsite = mapscript.colorObj(offsite[0], offsite[1], offsite[2])
            else:    
                raster.offsite = mapscript.colorObj(0,0,0)

            metadata = {
                "srs": "EPSG:4326",
                "format": "image/jpeg",
                "server_version": "1.1.1",
                "name": name,
                "title": title,
                "abstract": description,
                "attribution_title": attribution,
                "attribution_onlineresource": url }

            for key, val in metadata.items():
                raster.metadata.set("wms_" + key, val)

            if type == "GeoTIFF":
                raster.data = os.path.join(self.image_path, data)
            elif type == "Tile Index":
                raster.tileindex = os.path.join(self.image_path, data)
                # XXX BUG: we don't set tileitem b/c it's not in the d/b
            elif type == "WMS":
                raster.connectiontype = mapscript.MS_WMS
                raster.connection = data
         
        return wms
    
    def renderTile(self, tile):
        try:
            wms = self.get_map(tile)
            req = self.get_request(tile)
            wms.loadOWSParameters(req)
            mapImage = wms.draw()
            tile.data = mapImage.getBytes()
        except:
            tile.data = open("/var/www/oam/tilecache/blank.jpg").read()
        return tile.data 
