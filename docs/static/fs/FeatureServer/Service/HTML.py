from __init__ import Request, Action 
from FeatureServer.DataSource import Feature
from Cheetah.Template import Template

class HTML (Request):
    default_template = "template/default.html"

    def _datasource (self):
        return self.service.datasources[self.datasource]

    def encode(self, result):
        template = self.template()
        output = Template(template, searchList = [{'actions':result}, self])
        return "text/html; charset=utf-8", str(output).decode("utf-8")
    
    def template(self):
        datasource = self._datasource()
        if hasattr(datasource, "template"):
            template = datasource.template
        else:
            template = self.default_template
        return file(template).read()
