__author__ = 'pfjuckem'

# http://code.google.com/p/pyproj/downloads/detail?name=pyproj-1.9.3.win32-py2.7.exe&can=2&q=

from pyproj import Proj
from pyproj import transform

# define filename, output filename here
filename = "M:\\GroundWater_Systems\\USFS\\Medford\\GFLOW\\WCRs\\WGNHS_WCRs_WTM.csv"
output_filename = "M:\\GroundWater_Systems\\USFS\\Medford\\GFLOW\\WCRs\\WGNHS_WCRs_UTM15.dat"
ofp = open(output_filename, "w")

p1 = Proj(init='epsg:3071') #WTM Harn
p2 = Proj(init='epsg:26714') #UTM27 zone 15
p1projection = p1.srs #pulls projection info from the object
HeaderX = 'X_UTM27_Z15'
HeaderY = 'Y_UTM27_Z15'

for line in open(filename):
    # strip out whitespace to left and right of string, split by the space between
    Xin, Yin, Name = line.split(',')
    if Xin[0].isalpha():
        ofp.write(HeaderX + ", " + HeaderY + ", " + Name)
    else:
        Xin = float(Xin)
        Yin = float(Yin)
        if int(p1.srs.split(':')[-1]) != 4326: # if Xin & Yin are already in lat long, don't project them.
            Xin, Yin = p1(Xin, Yin, inverse=True)
        Xout, Yout = transform(p1, p2, Xin, Yin) # use this if changing coordinate system (LL, WTM, UTM)
        ofp.write(str(Xout) + ", " + str(Yout) + ", " + Name)

ofp.close()

''' List of previously used projections
Proj('+proj=utm +zone=16 +ellps=clrk66 +datum=NAD27 +units=m +no_defs') #UTM27 zone 16, manually defined
Proj('+proj=utm +zone=15 +ellps=clrk66 +datum=NAD27 +units=m +no_defs') #UTM27 zone 15, manually defined
Proj(init='epsg:26716') #UTM27 zone 16
Proj(init='epsg:26715') #UTM27 zone 15
Proj(init='epsg:3071') #WTM Harn
Proj(init='epsg:4326') #WGS84 (lat/long) -- may want to change this to 4269 (NAD83 northamerica) or 4152 (NAD83HARN)
'''