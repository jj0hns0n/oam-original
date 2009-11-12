import doctest
import os
import xml.dom.minidom as minidom
import sys; sys.path.append("..")
tests = os.listdir('.')
for test in tests:
    if test != "runtests.py" and os.path.isfile(test): 
        doctest.testfile(test)
        
