#!/usr/bin/python
from FeatureServer.Server import wsgiApp

import sys

if __name__ == '__main__':
    from wsgiref import simple_server
    print "Starting up Server..."
    httpd = simple_server.WSGIServer(('',8080), simple_server.WSGIRequestHandler,)
    print "Starting application..."
    httpd.set_app(wsgiApp)
    print "Now listening at http://localhost:8080/"
    httpd.serve_forever()
