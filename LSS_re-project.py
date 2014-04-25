#!/usr/bin/python
# pyproj is a library for projection transformations with python. downloaded from here:
# http://code.google.com/p/pyproj/downloads/detail?name=pyproj-1.9.3.win32-py2.7.exe&can=2&q=

from pyproj import Proj
from pyproj import transform

# define filename, output filename here
filename = "D:\\PFJData2\\Projects\\GW_team\\USFS\\ParkFalls\\GFLOW\\PF13_FF-medford.lss.xml"
output_filename = "D:\\PFJData2\\Projects\\GW_team\\USFS\\ParkFalls\\GFLOW\\PF13_FF-medford_zone15.lss.xml"
ofp = open(output_filename, "w")

# count x,y pairs
xCount = 0
yCount = 0

#p1 = Proj('+proj=utm +zone=16 +ellps=clrk66 +datum=NAD27 +units=m +no_defs')
#p2 = Proj('+proj=utm +zone=15 +ellps=clrk66 +datum=NAD27 +units=m +no_defs')
p1 = Proj(init='epsg:26716') #UTM27 zone 16
p2 = Proj(init='epsg:26715') #UTM27 zone 15

#p2 = Proj(init='epsg:3071') #WTM Harn
#p3 = Proj(init='epsg:4326') #WGS84 (lat/long) -- may want to change this to 4269 (NAD83 northamerica) or 4152 (NAD83HARN)

for line in open(filename):
    # strip out whitespace to left and right of string, split by the space between
    parts = line.split()

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
            xCount = xCount + 1

        if(parts[0] == "<Y>"):
            my_y = parts[1].split("<")[0]
            my_y = float(my_y)
            x1, y1 = p1(my_x, my_y, inverse=True)
            x2, y2 = p2(x1, y1) # simply re-assign the projection b/c they're both UTM
            #x2, y2 = transform(p1, p2, x1, y1) # use this if changing coordinate system (WTM & UTM)
            ofp.write("\t\t\t\t<X> " + str(x2) + "</X>\n")            
            ofp.write("\t\t\t\t<Y> " + str(y2) + "</Y>\n")
            yCount = yCount + 1

    else:
        ofp.write(line)

ofp.close()

