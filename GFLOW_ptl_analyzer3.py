# #############################################################################
# This code evaluates a pathline file from GFLOW and determines if individual
# particles end at a specified element or flow through a grid cell. The program 
# is designed to be used as part of a suite of codes to produce a map of the 
# probablility for an area contributing recharge to wells, the probable maximum 
# extent of a conserviate plume, and/or the terminal linesinks for a plume.
#
# The name file requires specification of the desired method:
# 1 -- Area contributing recharge to a well
# 2 -- Terminal linesinks for a conservative plume
# 3 -- Gridded maximum extent of a conservative plume
# 4 -- Both methods 2 and 3
# ##############################################################################

import sys
import time
import GFL_utilities as GFL
try:
	import shapefile
	shapefiles_imported = True
except: 
	shapefiles_imported = False
	print ('\n'
	       'WARNING: Unable to import the "shapefile" module. \n\n'
	       'Shapefile generation has been disabled for this run, \n'
	       'regardless of whether it was requested in the NAME file. \n'
	       'The ascii output file will still be generated as requested. \n\n')

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
	
# -- Failure with integer method in the name file
class MethodFail(Exception):
	def __init__(self,key):
		self.key = key
	def __str__(self):
		return('\n\nThe specified method does not match one of the 4 pre-determined methods. \n' +
		       'The offending input  was:\n' +
		       '"' + self.key + '"' +'\n' +
		       'Please specify an integer from 1 to 4 to indicate the desired method.')
# ############################################################################
# start of code; read in the namefile from the command prompt and process it.#
# ############################################################################
keywords = ['shapefiles','method', 'ranvarfilename', 'pstfilename', 'datfilename', 'pthfilename',
            'acrwellfilename', 'acroutfilename', 
            'elefilename', 'eleoutfilename','welloutfilename',
            'gridfilename', 'gridoutfilename']
shapekeys = ['yes','no']
methodkeys = [1,2,3,4]
try:
	namfile = sys.argv[1]
	#namfile = 'LF20SW_test4_KW.nam'
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

match = False
for key in allin.keys(): # test that all key words in NAM file match the predetermined list of key words
	for keyword in keywords:
		if key == keyword:
			match = True
			break
		else: match = False
	if match == False:
		raise(KeyFail(key))
	
# pass values to the variables from what was read-in using keywords
yes_no = allin['shapefiles'].lower() 
method = int(allin['method'])
ptlfilename = allin['pthfilename']
datfilename = allin['datfilename']

# Ensure that shapefiles are NOT written if "import shapefile" doesn't work, regardless of the NAME file.
if shapefiles_imported == False:
	yes_no = 'no'

match = False
for key in shapekeys: # test that input text for writing shapefiles matches one of the key words
	if key == yes_no:
		match = True
		break
	else: match = False
if match == False: 	raise(YesFail(yes_no))

match = False
for key in methodkeys:# test that input text for method matches one of the method key words
	if key == method:
		match = True
		break
	else: match = False
if match == False:      
	raise(MethodFail(str(method)))	



# open output files
if method == 1:
	try:
		acroutfilename = allin['acroutfilename']
		output_file = open(acroutfilename,'w')
	except:
		raise(FileFail(acroutfilename,'Area contributing recharge (ACR) output file'))
if (method == 2 or method == 4 ):
	try:	
		eleoutfilename = allin['eleoutfilename']
		eleoutput_file = open(eleoutfilename,'w')
	except:
		raise(FileFail(eleoutfilename,'element output file'))	
if ((method == 2 or method == 4) and ((allin['welloutfilename'].lower() <> 'none'))):  # Well elements are points and need a separate output shapefile
	try:	
		welloutfilename = allin['welloutfilename']
		welloutput_file = open(welloutfilename,'w')
	except:
		raise(FileFail(welloutfilename,'terminal well element output file'))
if method >=3: 
	try:
		gridoutfilename = allin['gridoutfilename']
		gridoutput_file = open(gridoutfilename, 'w')
	except:
		raise(FileFail(gridoutfilename,'gridoutput file'))	

#open method dependant input files
if method == 1:
	try:
		acrwellfilename = allin['acrwellfilename']
		acrwell_file = open(acrwellfilename,'r')
	except:
		raise(FileFail(acrwellfilename,'acrwellfilename'))
if (method == 2 or method == 4):
	try:
		elementfile = allin['elefilename']
		ele_file = open(elementfile,'r').readlines()
	except:
		raise(FileFail(elementfile,'element file'))
if method >= 3:
	try:
		gridfilename = allin['gridfilename']
		grid_file = open(gridfilename,'r')
	except:
		raise(FileFail(gridfilename,'grid file'))

# ###########################
# GFLOW dat file info block #
# ###########################
X_ORIG,Y_ORIG = GFL.get_model_origin(datfilename)

# ###########################
# Element file info block   #
# ###########################    	

# parse the files
if method == 1:
	acrwells = []
	acrwells = GFL.get_acrwells(acrwell_file)

if (method == 2 or method == 4):
	linesinks = []
	wells = []
	linesinks,wells = GFL.get_terminal_elements(ele_file,X_ORIG,Y_ORIG)

#process the grid/node file	
if (method >= 3):
	nodes = GFL.get_grid_nodes(grid_file)
	
# Pathline file info
if method <> 3:
	PCOORDstr,PCOORDend,Pelement,Ptime = GFL.read_end_points(ptlfilename,X_ORIG,Y_ORIG)

# #######################################
# Evaluate which particles are captured #
# #######################################
if method == 1:
	if shapefiles_imported == True:
		pshape = shapefile.Writer(shapefile.POINT)        #set up the point output shapefile
		pshape.field('In_Out')
	else: pshape = -999
	Endpt_outstring = '      X       ' + '      Y     ' + '  In/Out' + '\n' 
	output_file.write(Endpt_outstring)    # write to the output files 	
	GFL.perform_endpoint_analysis(yes_no,output_file,pshape,acrwells,PCOORDstr,PCOORDend,Pelement,Ptime)

if (method == 2 or method == 4): 
	if shapefiles_imported == True:
		lshape = shapefile.Writer(shapefile.POLYLINE)        #set up the line output shapefile
		lshape.field('Linesink ID')	
		lshape.field('In_Out')	
	else: lshape = -999
	Endpt_outstring = ('      X1      ' + '       Y1      ' + '         X2      ' + '         Y2      ' 
                           + '  In/Out' + '\n')
	eleoutput_file.write(Endpt_outstring)    # write to the output files 		
	if len(wells) > 0:
		if shapefiles_imported == True:		
			pshape = shapefile.Writer(shapefile.POINT)        #set up the point output shapefile
			pshape.field('In_Out')	
		else: pshape = -999
		wellpt_outstring = ('      X      ' + '         Y      ' + '   In/Out' + '\n')
		welloutput_file.write(wellpt_outstring)    # write to the output files 
		GFL.perform_terminal_element_analysis(yes_no,eleoutput_file,welloutput_file,lshape,pshape,linesinks,wells,PCOORDend,Pelement)
	else:	
		GFL.perform_terminal_linesink_analysis(yes_no,eleoutput_file,lshape,linesinks,PCOORDend,Pelement)
		
if (method >= 3):
	Z = GFL.map_pathlines_to_nodes(ptlfilename,nodes,X_ORIG,Y_ORIG)

if (method >= 3):	
	if shapefiles_imported == True:	
		nodeshape = shapefile.Writer(shapefile.POINT)        #set up the point output shapefile
		nodeshape.field('In_Out')	
	else: nodeshape = -999
	node_outstring = ('      X      ' + '         Y      ' + '  In/Out' + '\n')
	gridoutput_file.write(node_outstring)    # write to the output files 	
	GFL.write_flowpaths_to_nodes(yes_no,gridoutput_file,nodeshape,nodes,Z)

# close output file    
if method  == 1:
	try: output_file.close()
	except:	raise(FileFail(acroutfilename,'ACR output file'))
if (method == 2 or method == 4):
	try: eleoutput_file.close()
	except: raise(FileFail(eleoutfilename,'element output file'))
if ((method == 2 or method == 4) and len(wells) > 0):
	try: welloutput_file.close()
	except: raise(FileFail(welloutfilename,'well output file'))
if method >= 3:
	try: gridoutput_file.close()
	except: raise(FileFail(gridoutfilename,'grid node output file'))
		
# save the shapefile
if shapefiles_imported == True and yes_no == 'yes':
	if method == 1:
		pshape.save(acroutfilename)
	if (method == 2 or method == 4):
		lshape.save(eleoutfilename)
		if len(wells) > 0:
			pshape.save(welloutfilename)
	if method >= 3:
		nodeshape.save(gridoutfilename)
	
#get the elapsed time in seconds
t_end = time.time()-t_start

print 'took %f seconds to run this puppy' %(t_end)