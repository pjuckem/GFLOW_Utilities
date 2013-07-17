#!/usr/bin/python
# pyproj is a library for projection transformations with python. downloaded from here:
# http://code.google.com/p/pyproj/downloads/detail?name=pyproj-1.9.3.win32-py2.7.exe&can=2&q=

from pyproj import Proj
from pyproj import transform

def makeDictionary(x, y):
    d = {'X': x , 'Y' : y}
    return(d)

# define filename, output filename here

filename = "toColumbia.lss.xml"
output_filename = "RockExpWTM.lss.xml"

ofp = open(output_filename, "w")

# create a list to hold the dictionaries
mylist = []

# let's count how many x,y pairs we find
xCount = 0
yCount = 0

p1 = Proj(init='epsg:26716') #UTM27 zone 16
p2 = Proj(init='epsg:3071') #WTM Harn
p3 = Proj(init='epsg:4326') #WGS84 (lat/long) -- may want to change this to 4269 (NAD83 northamerica) or 4152 (NAD83HARN)

for line in open(filename):
    # strip out whitespace to left and right of string, split by the space between
    parts = line.split()
    #print parts[0]

    #need to write empty lines, but skip processing them.
    if line == "\n":
        ofp.write(line)
        continue

    if((parts[0] == "<X>") or (parts[0] == "<Y>")):
        if(parts[0] == "<X>"):
            # when an X is found, "parts[1]" still has the stupid "</X>" appended to it
            # this ugly looking code removes the trailing "</X>" or "</Y>"
            my_x = parts[1].split("<")[0] #works on second variable of parts (#####</x>), but only keeps the 0th variable after the split (#...#)
            my_x = float(my_x)
            #new_x = float(my_x) + 20000.0 + 80945*3.0
            #ofp.write("\t\t\t\t<X> " + str(new_x) + "</X>\n")
            xCount = xCount + 1

        if(parts[0] == "<Y>"):
            my_y = parts[1].split("<")[0]
            my_y = float(my_y)
            x1,y1 = p1(my_x,my_y,inverse=True)
            x2,y2 = transform(p3,p2,x1,y1)
            #new_y = float(my_y) - 4480000.0
            ofp.write("\t\t\t\t<X> " + str(x2) + "</X>\n")            
            ofp.write("\t\t\t\t<Y> " + str(y2) + "</Y>\n")
            yCount = yCount + 1
            #mydict = makeDictionary(new_x, new_y)
            #mylist.append(mydict)

    else:
        ofp.write(line)

#mylist.reverse()
'''
for item in mylist:
    ofp.write("\t\t<Vertex>\n")
    # item is a dictionary plucked from mylist; can retrieve the stored value
    # by accessing the "key", in this case "X" and "Y"
    ofp.write("\t\t\t<X> " + item["X"] + "</X>\n")
    ofp.write("\t\t\t<Y> " + item["Y"] + "</Y>\n")    
    ofp.write("\t\t</Vertex>\n")
'''
#ofp.flush()
ofp.close()

