from django.conf import settings
from django.db import models

import math, urllib, os
import time as time_module
import ogr, gdal

class Cache(models.Model):
    class Admin: pass
    def __str__(self):
        return self.extent
    extent = models.CharField(max_length=255)
    min_zoom = models.IntegerField()
    max_zoom = models.IntegerField()

class License(models.Model):
    class Admin: pass
    def __str__(self):
        return self.name.encode("utf-8")
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)

class Agent(models.Model):
    class Admin: pass
    def __str__(self):
        return self.name.encode("utf-8")
    name        = models.CharField(max_length=255)
    url         = models.CharField(max_length=255)
    attribution = models.CharField(max_length=255)

class DataSource(models.Model):
    class Admin: pass
    def __str__(self):
        return self.name.encode("utf-8")
    name        = models.CharField(max_length=255)
    description = models.TextField()
    url         = models.CharField(max_length=255)
    date        = models.DateField(help_text=time_module.strftime("%Y-%m-%d"))
    attribution = models.CharField(max_length=255, default = "", help_text="Short string used to identify provider")
    agent       = models.ForeignKey(Agent, help_text="<a href='/agent/create/'>Create New</a>")
    license       = models.ForeignKey(License, help_text="<a href='/licensing/'>Licensing Information</a>")
    def save(self):
        super(DataSource, self).save()
        directory = "/optistor/viz/openaerialmap/datasources/%s" % self.id
        try:
            os.stat(directory)
        except OSError:
            os.mkdir(directory, 0775)
            os.chmod(directory, 0775)

class RecordTypes(models.Model):
    class Admin: pass
    def __str__(self):
        return self.type.encode("utf-8")
    type       = models.CharField(max_length=255)
    template   = models.CharField(max_length=255)

class SpatialManager(models.Manager):
    def overlaps (self, (minx,miny,maxx,maxy)):
        box3d = 'BOX3D(%s %s, %s %s)' % (minx,miny,maxx,maxy)
        return self.extra(where=["bbox && '%s'::box3d" % box3d])

class DataRecord(models.Model):
    class Admin: pass
    def __str__(self):
        return "%s: %s-%s" % (self.datasource.name, self.min_scale, self.max_scale) 
    datasource      = models.ForeignKey(DataSource)
    type            = models.ForeignKey(RecordTypes)
    data            = models.CharField(max_length=255, help_text="Absolute path to file on disk.")
    layername       = models.CharField(max_length=255, default = "None", help_text = "Usually empty."  )
    data_resolution = models.FloatField(default = 0, help_text = "Meters / pixel")
    min_scale       = models.FloatField("Min scale denominator", default = 0, help_text = "Largest scale")
    max_scale       = models.FloatField("Max scale denominator", default = 0, help_text = "Smallest scale")
    extent          = models.CharField(max_length=255, help_text = "Comma seperated: left, bottom, right, top. Will be determined automatically for tile indexes and GeoTIFFs.")
    bbox            = models.TextField(editable=False)
    srs             = models.CharField(max_length=255, help_text = "Spatial reference system. Used only for WMS.", default="EPSG:4326")
    offsite         = models.CharField(max_length=255, editable=False, default="0 0 0")
    active          = models.BooleanField(default=True)
    objects         = SpatialManager()
    
    def get_zoom(self):
        avg_scale = (self.min_scale + self.max_scale) / 2
        return int(math.log(442943842 * 1 / avg_scale) / math.log(2))

    def get_center(self):
        bbox = map(float, self.extent.split(","))
        return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2) 
    
    def save(self):
        if self.max_scale == self.min_scale:
            raise ValueError, "max_scale should not be the same as min_scale"
        if self.type.type == "Tile Index":
            ds = ogr.Open(self.data)
            l = ds.GetLayer()
            extent = l.GetExtent()
            self.extent = "%s,%s,%s,%s" % (extent[0], extent[2], extent[1], extent[3]) 
        elif self.type.type == "GeoTIFF":
            ds = gdal.Open(self.data)
            xform = ds.GetGeoTransform()
            minx = xform[0]
            maxy = xform[3]
            maxx = minx + ds.RasterXSize * xform[1] + ds.RasterYSize * xform[2]
            miny = maxy + ds.RasterXSize * xform[4] + ds.RasterYSize * xform[5]  
            self.extent = "%s,%s,%s,%s" % (minx, miny, maxx, maxy)  
        minx,miny,maxx,maxy = self.extent.split(",")
        self.bbox = "POLYGON((%s %s, %s %s, %s %s, %s %s, %s %s))" % (
                minx, miny, minx, maxy, maxx, maxy, maxx, miny, minx, miny)
        super(DataRecord, self).save()
