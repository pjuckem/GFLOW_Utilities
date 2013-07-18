# Program to generate a grid of particles for a GFLOW template file (*.tpl).
# Input is a name file that specifies the input parameters and input files.
#
# Model origin should be copied from an existing *.tpl or *.dat file, and is 
# in model coordinates (UTM27, in meters). The polygon shapefile should also be 
# in model coordinates (UTM). Likewise, the distance between particles should
# be in model coordinates (meters if UTM). However, the starting elevation(s)
# is in COMPUTATIONAL units (ft above MSL if properties of the model are in ft 
# (eg: K = ft/d).
#
# Paul Juckem, USGS-WiWSC, Dec. 3, 2012

import sys
import numpy as np
import time
import shutil
try:
    import shapefile
    shapefiles_imported = True
except: 
    shapefiles_imported = False
    print ('\n'
           'WARNING: Unable to import the "shapefile" module. \n\n'
           'The program will not work without the ability to read \n'
           'the polygon shapefile that is to be filled with particles. \n\n')

echo = False
dat_echo = False
t_start = time.time()
# ####################### #
# Error Exception Classes #        
# ####################### #
# -- cannot read/write/open/close file
class FileFail(Exception):
    def __init__(self,filename,filetype):
        self.filename=filename
        self.ft = filetype
    def __str__(self):
        return('\n\nProblem with ' + self.ft +': ' + self.filename + ' \n' +
               "Either it can't be opened or closed, can't be read from or written to, or doesn't exist") 

# -- Failure parsing the input data file
class ParseFail(Exception):
    def __init__(self,offending_line):
        self.offending_line = offending_line
    def __str__(self):
        return('\n\nThere was a problem parsing a line in your data file. \n' +
               'The offending line was:\n' +
               '"' + self.offending_line + '"')

# -- Failure with keywords in the name file
class KeyFail(Exception):
    def __init__(self,key):
        self.key = key
    def __str__(self):
        return('\n\nThere was a problem with a keyword in the *.nam file. \n' +
               'The offending keyword was:\n' +
               '"' + self.key + '"')	

# -- Failure with keywords for writing shapefiles in the name file
class YesFail(Exception):
    def __init__(self,key):
        self.key = key
    def __str__(self):
        return('\n\nThere was a problem evaluating whether shapefiles were desired. \n' +
               'The offending word was:\n' +
               '"' + self.key + '"' +'\n' +
               'Please specify "Yes" or "No" after the "Shapefiles = " indicator.')	

# -- Failure with the specified units in the name file
class UnitFail(Exception):
    def __init__(self,key):
        self.key = key
    def __str__(self):
        return('\n\nThe specified units do not match one of the 2 pre-determined units. \n' +
               'The offending input  was:\n' +
               '"' + self.key + '"' +'\n' +
               'Please specify feet or meters.')

# -- Failure with reading the specified particle track direction
class DirectionFail(Exception):
    def __init__(self,key):
        self.key = key
    def __str__(self):
        return('\n\nThere was a problem reading the specified particle track DIRECTION. \n' +
               'The offending input  was:\n' +
               '"' + self.key + '"' +'\n' +
               'Please specify forward or backward.')

# ####################### #
# Ray-Cast IN/OUT method  #        
# ####################### #

# Determine if a point is inside a given polygon or not
# Polygon is a list of (x,y) pairs. This function
# returns True or False.  The algorithm is called
# the "Ray Casting Method". Function was copied from
# http://geospatialpython.com/2011/01/point-in-polygon.html

def point_in_poly(test_pt,poly):
    x = test_pt[0]
    y = test_pt[1]
    n = len(poly)
    inside = False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xints = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x,p1y = p2x,p2y
    return inside

# ######################### #
# Write particles functions #        
# ######################### #

def write_grid(test_pt,SE,Z):
    X = test_pt[0]
    Y = test_pt[1] 
    pt_outstring = ' ' + str((X - X_ORIG) * 3.28083) + ' ' + str((Y - Y_ORIG) *3.28083) + ' ' + str(SE) + ' ' + str(trace) + '\n' 
    output_file.write(pt_outstring)    # write to the output files       
    pshape.point(X,Y)    # write to the shapefile with model coordinates
    pshape.record(Z,SE)

# ###########################
# GFLOW dat file info block #
# ###########################
def get_model_origin(datfilename): # reads *.dat file and returns X and Y of model orgin	
    DATA = []
    try:
        dat_file = open(datfilename,'r').readlines()
    except:
        raise(FileFail(datfilename,'dat file'))

    for each_line in dat_file:
        DATA = each_line.split()  # splits a string at whitespaces    
        DATA = DATA[:] + [1]
        if DATA[0] == 'modelorigin': # Origin coordinates are in meters, all else in feet
            X_ORIG = float(DATA[1])
            Y_ORIG = float(DATA[2])
            break
    return (X_ORIG,Y_ORIG)	

# ############################################################## #			
# Start of code; read in the namfile from the command prompt.    #
# The namfile points to the files with input data.               #
# ############################################################## #
coord = []

# set up keywords, read Name file, generate dictionary of variable names and values from Name file.
keywords = ['write_shapefiles','datfilename', 'shapefile_name',
            'outfilename', 'distance_units', 'particle_spacing',
            'direction', 'elevation_units', 'elevation']
shapekeys = ['yes','no']
unitkeys = ['ft','feet','m','meter','meters']
directionkeys = ['forward', 'backward']
try:
    namfile = sys.argv[1]  
    lines = open(namfile,'r').readlines()
except:
    raise(FileFail(namfile,'name (*.nam) file'))

lineinfo = []
varnames = []
vals = []
for eachline in lines:
    lineinfo = eachline.split('#')[0].split('=') # splits by = on the left tuple
    if len(lineinfo) > 1: # allows comments to be placed anywhere in the file following a #
        varnames.append(lineinfo[0].strip().lower()) # assign variable name after strip whitespace and ensure lower case
        vals.append(lineinfo[1].strip()) # assign variable
allin = dict(zip(varnames,vals)) # construct dictionary of keywords and variables from NAM file.

# test that all key words in NAM file match the predetermined list of key words
match = False
for key in allin.keys(): 
    for keyword in keywords:
        if key == keyword:
            match = True
            break
        else: match = False
    if match == False:
        raise(KeyFail(key))    

# pass values to the variables from what was read-in using keywords
yes_no = allin['write_shapefiles'].lower() 
distunits = allin['distance_units'].lower()
outfilename = allin['outfilename']
datfilename = allin['datfilename']
shapefilename = allin['shapefile_name']    
elevunits = allin['elevation_units'].lower()
direction = allin['direction'].lower()

match = False
for key in shapekeys: # test that input text for writing shapefiles matches one of the key words
    if key == yes_no:
        match = True
        break
    else: match = False
if match == False: 	raise(YesFail(yes_no))

match = False
for key in unitkeys:# test that input text for method matches one of the method key words
    if key == distunits:
        match = True
        break
    else: match = False
if match == False:      
    raise(UnitsFail(str(distunits)))	

match = False
for key in unitkeys:# test that input text for method matches one of the method key words
    if key == elevunits:
        match = True
        break
    else: match = False
if match == False:      
    raise(UnitsFail(str(elevunits)))

match = False
for key in directionkeys:# test that input text for method matches one of the method key words
    if key == direction:
        match = True
        break
    else: match = False
if match == False:      
    raise(DirectionFail(str(direction)))

# ####################
# Start computations #
# #################### 

# get the model origin
X_ORIG,Y_ORIG = get_model_origin(datfilename)

# Set the ptl track direction value
if direction.lower() == 'forward':
    trace = 1.0
elif direction.lower() == 'backward':
    trace = -1.0

# compute the appropriate distance between each particle.
dist = float(allin['particle_spacing']) # read distance between particles
if (distunits == 'ft' or distunits == 'feet'):
    dist = dist * 0.3048 # convert to metric so all coordinates are metric.

# get starting elevation of particles
SE = float(allin['elevation'])
# Note: Will not do anything with the specified elevation units, because expect
# that the user knows the computational units of their model. This variable 
# in the NAM file was included solely for the user to feel comfortable that
# the distance and elevation units do not need to be in the same units.

# open output file 
try:
    output_file = open(outfilename,'w')
except:
    raise(FileFail(outfilename,'output file'))

# ###################################################      
# perform evaluation based on NstrtElev and polygon #
# ###################################################

Z = 0
pshape = shapefile.Writer(shapefile.POINT)        #set up the point shapefile
pshape.field('ptl')
pshape.field('StartElev','N',7,2)
pt_outstring = '  X   ' + '   Y   ' + '    StartElev    ' + ' for/back \n' 
output_file.write(pt_outstring)    # write header to the output files 

# #############################
# Rectangle grid of particles #
# #############################
'''
Xmin = 9999999999999
Ymin = 9999999999999
Xmax = 0
Ymax = 0
'''
# open the shapefile for the grid
try:
    sf = shapefile.Reader(shapefilename)
except:
    raise(FileFail(shapefilename,'shapefile'))

sfshape = sf.shapes()
box = []
for eachpoly,polygon in enumerate(sfshape):  # allows for multiple polygons within one shapefile
    box = sfshape[eachpoly].bbox
    Xmin = box[0]
    Ymin = box[1]
    Xmax = box[2]
    Ymax = box[3]
    ptlpoly = []
    ptlpoly = sfshape[eachpoly].points[:]
    Pg = []
    PCOORDgrd = []
    Ypoly = Ymin
    Xpoly = Xmin
    # Generate rectangular grid, starting at lower left moving to upper right
    while (Ypoly <= Ymax):
        Xpoly = Xmin
        Pg.append(Xpoly)
        Pg.append(Ypoly)
        PCOORDgrd.append(np.array([Pg[0],Pg[1]])) # adds X & Y to lists, then to array PCOORDstr
        Pg = [] 
        while (Xpoly <= Xmax):
            Xpoly = Xpoly + dist
            Pg.append(Xpoly)
            Pg.append(Ypoly)
            PCOORDgrd.append(np.array([Pg[0],Pg[1]])) # adds X & Y to lists, then to array PCOORDstr
            Pg = []  
        Ypoly = Ypoly + dist	

# check generated grid of points against true extent of the polygons
    for test_pt in (PCOORDgrd[:]): 	
        inout = point_in_poly(test_pt,ptlpoly) # function call to test in/out of polygon
        if inout:			
            Z += 1
            write_grid(test_pt,SE,Z)

# close output file    
try:
    output_file.close()
except:
    raise(FileFail(outfilename,'output file'))

# save the shapefile
if yes_no == 'yes':
    pshape.save(outfilename)
    # copy the projection file from the input Shapefile to the output shapefile
    prefix,suffix = shapefilename.split('.')
    prjinfile = prefix + '.prj'
    prefix,suffix = outfilename.split('.')
    prjoutfile = prefix + '.prj'
    shutil.copyfile(prjinfile,prjoutfile)

#get the elapsed time in seconds
t_end = time.time()-t_start

print '%f particles were generated' %(Z)
print 'took %f seconds to run this puppy \n \n' %(t_end)