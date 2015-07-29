import sys
import os
"""
print sys.argv[0]
print os.path.realpath(sys.argv[0])
print os.path.abspath(sys.argv[0])
print os.path.dirname(os.path.realpath(sys.argv[0]))
"""
#print os.path.abspath(os.path.dirname(sys.argv[0]))
print os.path.join(sys.path[0], "lastEvent")
