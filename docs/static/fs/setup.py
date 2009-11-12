#!/usr/bin/env python

from distutils.core import setup

setup(name='FeatureServer',
      version='1.10',
      description='A server for geographic features on the web.',
      author='MetaCarta Labs',
      author_email='labs+featureserver@metacarta.com',
      url='http://featureserver.org/',
      license="Clear BSD",
      packages=['FeatureServer', 'FeatureServer.DataSource', 'FeatureServer.Service'],
      scripts=['featureserver.cgi', 'featureserver.fcgi',
               'featureserver_http_server.py'],
      data_files=[('/etc', ['featureserver.cfg'])]
     )
