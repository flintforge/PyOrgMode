'''
%load_ext autoreload
%autoreload 2
%aimport pyorgmode
'''
import locale
locale.setlocale(locale.LC_ALL, "")
from pyorgmode import *
org = OrgDataStructure()
org.load_from_file("test.org")
topnodes = org.toplevel_nodes()
headings = [T.heading for T in topnodes]
print(headings)
print(topnodes)
for it in topnodes :
    print (it.level, it.todo, it.priority, it.heading, it.tags)
