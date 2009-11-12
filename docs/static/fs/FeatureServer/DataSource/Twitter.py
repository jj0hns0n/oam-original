from FeatureServer.DataSource import DataSource, Feature
import urllib, simplejson    

class Twitter (DataSource):
    """Specialized datasource allowing read-only access to a given 
       username's location via the Twittervision API."""
    def __init__(self, name, username, **args):
        DataSource.__init__(self, name, **args)
        self.username = username
        
    def select (self, action):
        data = urllib.urlopen("http://api.twittervision.com/user/current_status/%s.json" % self.username).read()
        user_data = simplejson.loads(data)
        geom = {'type':'Point', 'coordinates': [[user_data['location']['longitude'], user_data['location']['latitude']]]}
        f = Feature(int(user_data["id"]), geom)
        return [f]
