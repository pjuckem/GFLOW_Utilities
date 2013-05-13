import numpy as np
import math


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

# ###########################
# Element file info block   #
# ###########################
# generate a list of the elements from a file listing the elements of interest (eg: wells for ZOC)
def get_acrwells(well_file):
	wells = []
	for well in well_file:
		wells.append(well.strip('\n'))    # need to strip the \n off of the matchelement
	return (wells)

# Check the element type
def checkelement(LS_line):
	try: coord = float(LS_line[0])
	except:	return 'NewElementList'
	else:
		try: coord = float(LS_line[3])
		except: return 'routedLS'
		else:
			try: coord = float(LS_line[4])
			except: return 'well'
			else:
				try: coord = float(LS_line[5])
				except: return 'non-routed'
				else: print ('\n\nThere was a problem parsing the Element file. \n')

# Generate a list of well and linesink elements (returns 2 lists) with X,Y coordinates for terminal element evaluation. 
# Note: the element file for "get_terminal_elements" contains more information (X,Y) than the file for "get_elements"
def get_terminal_elements(ele_file,X_ORIG,Y_ORIG):
	linesinks = []
	LS = []
	well = []
	wells = []
	for LS_line in ele_file:
		LS_line = LS_line.strip().split()
		ele_type = checkelement(LS_line)
		if ele_type == 'NewElementList':
			LSfirstX = 0
			LSfirstY = 0				
			continue # returns to next line of the element file	
		elif ele_type == 'well':
			LSfirstX = ((float(LS_line[0]) / 3.28083) + X_ORIG)
			LSfirstY = ((float(LS_line[1]) / 3.28083) + Y_ORIG)
			LSname = LS_line[4]
			well.append(str(LSfirstX))
			well.append(str(LSfirstY))
			well.append(LSname)
			wells.append(well)
			well = []
			continue # returns to next line of the element file
		elif ele_type == 'non-routed':
			LSfirstX = ((float(LS_line[0]) / 3.28083) + X_ORIG)
			LSfirstY = ((float(LS_line[1]) / 3.28083) + Y_ORIG)
			LSsecondX = ((float(LS_line[2]) / 3.28083) + X_ORIG)
			LSsecondY = ((float(LS_line[3]) / 3.28083) + Y_ORIG)			
			LSname = LS_line[5]
			LS.append(str(LSfirstX)) #append X coordinate
			LS.append(str(LSfirstY)) #append Y coordinate
			LS.append(str(LSsecondX)) #append X coordinate
			LS.append(str(LSsecondY)) #append Y coordinate			
			LS.append(LSname) #append LS name
			linesinks.append(LS) # append the 5-part string list to "linesinks" list (can't make arrays b/c passing string 'LSname')
			LS = []
			continue # returns to next line of the element file
		elif ele_type == 'routedLS':
			LSsecondX = ((float(LS_line[0]) / 3.28083) + X_ORIG)
			LSsecondY = ((float(LS_line[1]) / 3.28083) + Y_ORIG)			
			if LSfirstX == 0: # only start generating arrays for the LS after get the second coordinate
				LSfirstX = LSsecondX
				LSfirstY = LSsecondY
				LSname = LS_line[3]		
			elif LSfirstX > 0: 
				try: LSnextName = LS_line[3]
				except: LSnextName = 'last linesink'
				LS.append(str(LSfirstX)) #append X coordinate
				LS.append(str(LSfirstY)) #append Y coordinate
				LS.append(str(LSsecondX)) #append X coordinate
				LS.append(str(LSsecondY)) #append Y coordinate			
				LS.append(LSname) #append LS name
				linesinks.append(LS) # append the 5-part string list to "linesinks" list (can't make arrays b/c passing string 'LSname')
				LS = []
				LSfirstX = LSsecondX
				LSfirstY = LSsecondY
				LSname = LSnextName
		else: print ('\n\nThere is a problem with the file containing the list of elements \n')
	return(linesinks,wells)

# ########################
# Grid file info block   #
# ########################
def get_grid_nodes(grid_file):
	nodes = np.loadtxt(grid_file,delimiter=',',skiprows=1)
	return(nodes)

def check_node_spacing(nodes):
	Xcoord = nodes[:,0] # return all (:) from the 0th column
	Ycoord = nodes[:,1] # return all from the 1th column
	Xcoord = np.unique(Xcoord)  # only keep unique values (don't retain duplicates in the array)
	Ycoord = np.unique(Ycoord)
	dX = np.diff(Xcoord) # compute the difference between each value in the array (could be many values if non-uniform spacing)
	dY = np.diff(Ycoord)
	uniformX = np.unique(dX) # only keep unique values
	uniformY = np.unique(dY)
	if ((len(uniformX) > 1) or (len(uniformY) > 1)):  #if more than one spacing in x or y
		print "There is a problem with your grid. It's not uniformly spaced"
	else: nodespace = uniformX[0]  # ensures grid has uniform spacing
	return(nodespace)

def index_grid_nodes(nodes):
	Xcoord = nodes[:,0] # return all (:) from the 0th column
	Ycoord = nodes[:,1] # return all from the 1th column
	Xcoord = np.unique(Xcoord)  # only keep unique values (don't retain duplicates in the array)
	Ycoord = np.unique(Ycoord)
	Xcoord = np.sort(Xcoord)
	Ycoord = np.sort(Ycoord)
	X,Y = np.meshgrid(Xcoord,Ycoord) #X and Y are now 1-d array for the index of each node in the grid
	return(X,Y)

# ##########################
# Pathline file info block #
# ##########################
def read_end_points(ptlfilename,X_ORIG,Y_ORIG):
	DATA= []
	STATUS = []
	Ps = []
	Pe = []
	PCOORDstr = []   
	PCOORDend = []   
	PATHLINE = 0
	Pelement = []
	Ptime = []
	# open particle pathline file for methods 1 & 2
	try:
		ptl_file = open(ptlfilename,'r')
	except:
		raise(FileFail(ptlfilename,'particle file'))
	for each_line in ptl_file:
		DATA = each_line.split()  # splits a string at whitespaces
		STATUS = DATA[0]  #starting point, intermediate point, or ending point
		if STATUS == 'START':
			Xstart = ((float(DATA[1]) / 3.28083) + X_ORIG)   # convert particle coordinates from feet to meter and add origin offset       
			Ystart = ((float(DATA[2]) / 3.28083) + Y_ORIG)   # all coordinate evaluations will now be performed with model coordinates
			Ps.append(Xstart)
			Ps.append(Ystart)
			PCOORDstr.append(np.array([Ps[0],Ps[1]]))
			Ps = []
		elif STATUS == 'END':
			Xend = ((float(DATA[1]) / 3.28083) + X_ORIG)   # convert particle coordinates from feet to meter and add origin offset 
			Yend = ((float(DATA[2]) / 3.28083) + Y_ORIG)    
			Pe.append(Xend)
			Pe.append(Yend)
			PCOORDend.append(np.array([Pe[0],Pe[1]])) # array of lists
			Pe = [] 
			Pelement.append(DATA[8])
			Ptime.append(float(DATA[4]))
	PCOORDstr = np.array(PCOORDstr) # array of an array
	PCOORDend = np.array(PCOORDend)
	return(PCOORDstr,PCOORDend,Pelement,Ptime)
# #############################
# shapefile writing functions #	
# #############################
def write_pointshapefile(pshape,test_pt,Z):  	
	pshape.point(test_pt[0],test_pt[1])    # write to the point shapefile with model coordinates
	pshape.record(Z)  
	
def write_nodeshapefile(nodeshape,test_pt,Z):  	
	nodeshape.point(test_pt[0],test_pt[1])    # write to the point shapefile with model coordinates
	nodeshape.record(Z) 	
	
def write_lineshapefile(lshape,parts,name,Z):  	
	lshape.line(parts)    # write to the line shapefile with model coordinates
	lshape.record(name,Z)  
	
# #######################################
# Evaluate which particles are captured #
# #######################################
# endpoint analysis for method 1
def perform_endpoint_analysis(yes_no,output_file,pshape,acrwells,PCOORDstr,PCOORDend,Pelement,Ptime): 
	Z = []
	Z = np.zeros(len(PCOORDstr))	
	for I, test_pt in enumerate (PCOORDend[:]):    # try just passing Pelement -- do we really need to pass PCOORDend? 
		for matchwell in acrwells:
			if matchwell == Pelement[I]:  
				Z[I] += 1 
	for i, coord in enumerate (PCOORDstr[:]):
		X = coord[0]
		Y = coord[1]    
		Endpt_outstring = '%-16.5f %-16.5f %d\n' %(X,Y,Z[i])
		output_file.write(Endpt_outstring)
		if pshape <> -999 and yes_no == 'yes':
			write_pointshapefile(pshape,coord,Z[i]) #passes 3 variables to the point shapefile definition

# terminal element analysis (method 2)
def perform_terminal_linesink_analysis(yes_no,eleoutput_file,lshape,linesinks,PCOORDend,Pelement): 
	Z = []
	Z = np.zeros(len(linesinks))	
	for I, matchelement in enumerate (linesinks[:]): # pull the linesink name
		for i, test_pt in enumerate (PCOORDend[:]):
			if matchelement[4] == Pelement[i]:  
				Z[I] += 1
				break # once a LS in the LS file is matched with a particle, start with a new LS (we're not counting # of PTL captured by a LS, just if an LS captures atleast one ptl)
	for i, line in enumerate (linesinks[:]):
		X1 = float(line[0])
		Y1 = float(line[1])
		X2 = float(line[2])
		Y2 = float(line[3])
		name = line[4]
		Endpt_outstring = '%-16.5f %-16.5f %-16.5f %-16.5f %d\n' %(X1,Y1,X2,Y2,Z[i])
		eleoutput_file.write(Endpt_outstring)    # write to the output files 
		if lshape <> -999 and yes_no == 'yes':
			parts = [[[X1,Y1],[X2,Y2]]]
			write_lineshapefile(lshape,parts,name,Z[i]) # passes 4 variables to line shapefile writer
				
def perform_terminal_element_analysis(yes_no,eleoutput_file,welloutput_file,lshape,pshape,linesinks,wells,PCOORDend,Pelement):
	perform_terminal_linesink_analysis(yes_no,eleoutput_file,lshape,linesinks,PCOORDend,Pelement)	# The LS analysis always needs to be performed.
	W = []
	W = np.zeros(len(wells))
	for I, matchelement in enumerate (wells[:]): # pull the well name
		for i, test_pt in enumerate (PCOORDend[:]):
			if matchelement[2] == Pelement[i]:  
				W[I] += 1
				break # once a well in the Element file is matched with a particle, start with a new well
	for i, line in enumerate (wells[:]):
		X1 = float(line[0])
		Y1 = float(line[1])
		name = line[2]
		wellpt_outstring = '%-16.5f %-16.5f %d\n' %(X1,Y1,W[i])
		welloutput_file.write(wellpt_outstring)    # write to the output files 
		if pshape <> -999 and yes_no == 'yes':
			parts = [X1,Y1]
			write_pointshapefile(pshape,parts,W[i]) # passes 3 variables to shapefile writer pshape,test_pt,Z

# map flowpaths to grids (method 3)
def map_pathlines_to_nodes(ptlfilename,nodes,X_ORIG,Y_ORIG): # will need to make direct calls to other functions here so don't have to pass things like X_orig and halfNS
	try:
		ptl_file = open(ptlfilename,'r') #re-open the pth file because method 3 evaluates it differently than methods 1 & 2.
	except:
		raise(FileFail(ptlfilename,'particle file'))
	cc = 0	
	print 'Mapping pathlines to the grid.'
	X,Y = index_grid_nodes(nodes)
	Z = np.zeros_like(X)
	nodespace = check_node_spacing(nodes)
	halfNS = 0.5 * nodespace
	for each_line in ptl_file:
		cc += 1
		DATA = each_line.split()  # splits a string at whitespaces
		STATUS = DATA[0]  #starting point, intermediate point, or ending point
		if STATUS == 'START':
			junk = DATA.pop()
			i = 0 # initialize the counter so can identify the start of a particle pathline
			continue
		elif STATUS == 'END':
			junk = DATA.pop()			
			continue # no need to process an end point
		elif i == 0:  # only populate the first coordinate of a particle pathline immediately after finding the START
			x1 = ((float(DATA[0]) / 3.28083) + X_ORIG)   # convert particle coordinates from feet to meter and add origin offset       
			y1 = ((float(DATA[1]) / 3.28083) + Y_ORIG)   # all coordinate evaluations will now be performed with model coordinates				
			i += 1
		else:
			x2 = ((float(DATA[0]) / 3.28083) + X_ORIG)     
			y2 = ((float(DATA[1]) / 3.28083) + Y_ORIG)
			ptlstep = math.sqrt((math.pow((x2-x1),2)) + (math.pow((y2-y1),2))) # compute the step size for the particle so can compare with grid spacing
			if x2 < x1: 
				xmin = x2
				xmax = x1
			else: 
				xmin = x1
				xmax = x2
			if y2 < y1: 
				ymin = y2
				ymax = y1
			else: 
				ymin = y1
				ymax = y2
			xminus = xmin - (halfNS) # add, subtract half of the node spacing to the particle segment extents in order to
			yminus = ymin - (halfNS) # compute the bounds over which to search for nearby nodes that will be analyzed.
			xplus = xmax + (halfNS)
			yplus = ymax + (halfNS)
			indices  = np.where((X<=xplus) & (X>=xminus) & (Y<=yplus) & (Y>=yminus)) # identify the indices of the nodes that are within 1/2 node spacing of either endpoint of the pathline segment

			if len(indices[0]) < 1:  #if the indices array is empty, the pathline is outside of the grid (eg: under a weak sink lake). 
				x1 = x2
				y1 = y2				
				continue # So, skip this particle. The user will have to evaluate if this is an actual problem   
			
			elif nodespace >= ptlstep: # If grid spacing > pathline step, any nodes captured correspond with cells that this ptl trace has gone through.
				for cind in np.arange(len(indices[0])): # loop through each node near the pathline segment
					index = np.array([indices[0][cind],indices[1][cind]])				
					Z[index[0],index[1]] = 1
					#print (str(index[0]) + ', ' + str(index[1]) + ', ' + str(X[index[0],index[0]]) + ', ' + str(Y[index[1],index[1]]) + ', ' + str(Z[index[0],index[1]]))
			else:
				#nodespace <= ptlstep # If grid spacing < pathline step, need to evaluate if both endpoints are inside a cell or if ptl crosses a grid.
				dely = y2 - y1
				delx = x2 - x1
				if delx == 0: delx = 1e-9				
				m = (dely/delx)	# compute slope of the pathline segment	
				if m == 0: 
					m = 1e-9
					print 'Adjusted the slope of a particle pathline segment to a non-zero value of 1e-9'
				b = y1-m*x1     # compute y-offset of the pathline segment
									
				for cind in np.arange(len(indices[0])): # loop through each node near the pathline segment
					index = np.array([indices[0][cind],indices[1][cind]])
					ylg = m*(X[index[0],index[1]]+halfNS)+b # equation for Y coordinate of the pathline at the right edge of the cell
					ysm = m*(X[index[0],index[1]]-halfNS)+b # equation for Y coordinate of the pathline at the left edge of the cell
					xlg = ((Y[index[0],index[1]]+halfNS)-b)/m #equation for X coordinate of the pathline at top edge of the cell
					xsm = ((Y[index[0],index[1]]-halfNS)-b)/m #equation for X coordinate of the pathline at bottom edge of the cell
					#print (str(index[0]) + ', ' + str(index[1]) + ', ' + str(X[index[0],index[1]]) + ', ' + str(Y[index[0],index[1]]) + ', ' + str(Z[index[0],index[1]]))
					
					# If the max/min coordinates of the entire segment are within the cell, then it's in and no need to check for intersecting the grid
					# This should be a rare occurance, but could occur when the nodespace is almost = to ptlstep and the pathline segment is tilted at an angle
					if ((ymax < (Y[index[0],index[1]]+halfNS)) & 
				            (ymin > (Y[index[0],index[1]]-halfNS)) & 
				            (xmax < (X[index[0],index[1]]+halfNS)) &
				            (xmin > (X[index[0],index[1]]-halfNS))):
						Z[index[0],index[1]] = 1 
					#Test to see if any x or y intersection coordinate is within the limits of the cell.
					#Must bound by both the grid dimensions and the pathline segment dimensions.
					#Once we find that the pathline crosses a side of the cell, the pathline entered the cell.
					elif (ylg < ymax and ylg > ymin and ylg < (Y[index[0],index[1]]+halfNS) and ylg > (Y[index[0],index[1]]-halfNS)):
						Z[index[0],index[1]] = 1 
					elif (ysm < ymax and ysm > ymin and ysm < (Y[index[0],index[1]]+halfNS) and ysm > (Y[index[0],index[1]]-halfNS)):
						Z[index[0],index[1]] = 1 
					elif (xlg < xmax and xlg > xmin and xlg < (X[index[0],index[1]]+halfNS) and xlg > (X[index[0],index[1]]-halfNS)):
						Z[index[0],index[1]] = 1 						
					elif (xsm < xmax and xsm > xmin and xsm < (X[index[0],index[1]]+halfNS) and xsm > (X[index[0],index[1]]-halfNS)):
						Z[index[0],index[1]] = 1 
			x1 = x2
			y1 = y2
			if cc%2500 == 0:   # prints the vertical ..... on screen
				print '.'
	return(Z)

# write the Z array for the flowpath mapping algorithm
def write_flowpaths_to_nodes(yes_no,gridoutput_file,nodeshape,nodes,Z): 	
	if nodeshape <> -999 and yes_no == 'yes':
		print 'Writing the grid node shapefile...'
	X,Y = index_grid_nodes(nodes)
	for i,eachnode in enumerate(nodes):	
		#print str(i) + '\n'
		ind  = np.where((X==eachnode[0]) & (Y==eachnode[1]))
		node_outstring = '%-16.5f %-16.5f %d\n' %(X[ind],Y[ind],Z[ind])
		gridoutput_file.write(node_outstring)    # write to the output files 
		if nodeshape <> -999 and yes_no == 'yes':		
			parts = (X[ind],Y[ind])
			write_nodeshapefile(nodeshape,parts,np.squeeze(Z[ind])) # passes 2 variables to shapefile writer
		if i%5000 == 0:   # prints the vertical ..... on screen
			print '.'	