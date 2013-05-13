# Program to generate a grid of points (nodes, or pixels) to analyze GFLOW forward traces.
# Input is a name file that specifies the input parameters and input files.
# The name file contains: 1) the bounding polygon of interest, 2) the model origin, and
# 3) distance between points. 
#
# Model origin should be copied from an existing *.tpl or *.dat file, and is 
# in model coordinates (UTM27, in meters). The polygon shapefile should also be 
# in model coordinates (UTM). Likewise, the distance between points should
# be in model coordinates (meters if UTM).  It is common to set the distance
# between points equal to a multiple of the GFLOW particle step size, which
# can be read from the GFLOW input *.dat file.
#
# Paul Juckem, USGS-WiWSC, Jan. 10, 2012

import sys
import numpy as np
import time
try:
	import shapefile
	shapefiles_imported = True
except: 
	shapefiles_imported = False
	print ('\n'
	       'WARNING: Unable to import the "shapefile" module. \n\n'
	       'The program will not work without the ability to read \n'
	       'the polygon shapefile that is to be filled with grid nodes. \n\n')


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
		return('\n\nThe specified computational units do not match one of the 2 pre-determined units. \n' +
		       'The offending input  was:\n' +
		       '"' + self.key + '"' +'\n' +
		       'Please specify feet or meters to indicate the input units specified for the model. \n'
		       'For example, "feet" if hydraulic conductivity is in ft/d.')

# -- Failure with reading the particle step from the GFLOW DAT file
class StepFail(Exception):
	def __init__(self,key):
		self.key = key
	def __str__(self):
		return('\n\nThere was a problem reading the particle step size from the GFLOW *.dat file. \n' +
		       'Please ensure that particles have been added to GFLOW and that the window-appropriate \n'
		       'step size has been computed by GFLOW and written to the *.dat file.')	

# ####################### #
# Ray-Cast IN/OUT method  #        
# ####################### #

# Determine if a point is inside a given polygon or not
# Polygon is a list of (x,y) pairs. This function
# returns True or False.  The algorithm is called
# the "Ray Casting Method". Function was modified from
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

def write_grid(test_pt,Z,yes_no):
	X = test_pt[0]
	Y = test_pt[1] 
	pt_outstring = str(X) + ', ' + str(Y) + '\n' 
	output_file.write(pt_outstring)    # write to the output files       
	if yes_no == 'yes':
		pshape.point(X,Y)    # write to the shapefile with model coordinates
		pshape.record(Z)

# ############################## #
# Get step from GFLOW #        
# ############################## #	
def get_step(datfilename): # reads *.dat file and returns X and Y of model orgin	
	DATA = []
	ptl_step = -999.9  # in case there is a problem, a large number precludes long processing time
	try:
		dat_file = open(datfilename,'r').readlines()
	except:
		raise(FileFail(datfilename,'dat file'))
	
	for each_line in dat_file:
		DATA = each_line.split()  # splits a string at whitespaces    
		DATA = DATA[:] + [1]
		if DATA[0] == 'step':
			ptl_step = float(DATA[1])
			break
	return (ptl_step)	

# ############################################################## #			
# Start of code; read in the namfile from the command prompt.    #
# The namfile points to the files with input data.               #
# ############################################################## #

# process input
keywords = ['write_shapefiles','datfilename', 'shapefile_name',
            'outfilename', 'computational_units', 'step_multiplier',
            'step_size']
shapekeys = ['yes','no']
unitkeys = ['ft','feet','m','meter','meters']
try:
	namfile = sys.argv[1]
	#namfile = 'swlaganalyzegrid.nam'
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

mult = False
match = False
for key in allin.keys(): # test that all key words in NAM file match the predetermined list of key words
	for keyword in keywords:
		if key == keyword:
			match = True
			if key == 'step_multiplier':
				mult = True
			break
		else: match = False
	if match == False:
		raise(KeyFail(key))
	
# pass values to the variables from what was read-in using keywords
yes_no = allin['write_shapefiles'].lower() 
units = allin['computational_units'].lower()
outfilename = allin['outfilename']
datfilename = allin['datfilename']
shapefilename = allin['shapefile_name']

match = False
for key in shapekeys: # test that input text for writing shapefiles matches one of the key words
	if key == yes_no:
		match = True
		break
	else: match = False
if match == False: 	raise(YesFail(yes_no))

match = False
for key in unitkeys:# test that input text for method matches one of the method key words
	if key == units:
		match = True
		break
	else: match = False
if match == False:      
	raise(UnitsFail(str(units)))	


# ####################
# Start computations #
# #################### 

# compute the appropriate distance between each grid node.
if mult == True:
	stp_mult = float(allin['step_multiplier'])
	dist = get_step(datfilename) # pull the step size from the DAT file
	if dist == -999.9:
		raise(StepFail(datfilename))
	
	elif (units == 'ft' or units == 'feet'):
		dist = dist * 0.3048 # convert to metric so all coordinates are metric.
	dist = np.floor(dist * stp_mult) # need to round down so that number of digits is reduced
					 # Otherwise the PTH analyzer throws an error due to uneven spaced grid.

else:
    dist = float(allin['step_size']) # read distance directly if "step_size" is specified
    if (units == 'ft' or units == 'feet'):
	dist = dist * 0.3048 # convert to metric so all coordinates are metric.
	
# open output file 
try:
	output_file = open(outfilename,'w')
except:
	raise(FileFail(outfilename,'output file'))

# #############################
# Rectangle grid of particles #
# #############################  
# open the shapefile for the grid
try:
	sf = shapefile.Reader(shapefilename)

except:
	raise(FileFail(shapefilename,'shapefile'))

sfshape = sf.shapes()
box = []
box = sfshape[0].bbox
Xmin = box[0]
Ymin = box[1]
Xmax = box[2]
Ymax = box[3]
ptlpoly = []
ptlpoly = sfshape[0].points[:]
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

# #########################      
# Evaluate and write grid #
# #########################

Z = 0
pshape = shapefile.Writer(shapefile.POINT)        #set up the point shapefile
pshape.field('ptl')
#pshape.field('StartElev','N',7,2) # StartElev is a number with upto 7 spaces, 2 of which are decimals
pt_outstring = '     X      ' + '       Y    ' + '    ID_Num  ' + '\n' 
output_file.write(pt_outstring)    # write header to the output files 

for test_pt in (PCOORDgrd[:]): 	
	inout = point_in_poly(test_pt,ptlpoly) # function call to test in/out of polygon
	if inout:  
		Z += 1		
		write_grid(test_pt,Z,yes_no) # function call to write the coordinates to flat file and shapefile

# close output file    
try:	output_file.close()
except:	raise(FileFail(outfilename,'output file'))

# save the shapefile
if yes_no == 'yes':
	pshape.save(outfilename)

#get the elapsed time in seconds
t_end = time.time()-t_start

print '%f grid nodes were generated' %(Z)
print 'took %f seconds to run this puppy \n \n' %(t_end)