#  This program computes a difference between two target flows from data output to the XTR file.
#  This allows the flow gain, which is more important for these particular targets than the actual flow,
#  to be computed and used as a target in PEST.
#
#  -Paul Juckem, 2/1/2013
import sys
echo = False

namfile = sys.argv[1]
namdat = open(namfile,'r').readlines()
outfilename = namdat[0].strip().split()[0]
xtrfilename = namdat[1].strip().split()[0].upper()
gagefilename = namdat[2].strip().split()[0]
output_file = open(outfilename,'w')
indat = open(xtrfilename,'r').readlines()
gages = open(gagefilename,'r').readlines()

lineinfo = []
TG = []
Station = []
for eachline in gages:
	lineinfo = eachline.split(',') # splits by "," and keeps GFLOW name and my name for the gage target	
	Station.append(lineinfo[0].strip()) # assign variable name after strip whitespace and ensure lower case
	TG.append(lineinfo[1].strip()) # assign variable
allin = dict(zip(Station,TG)) # construct dictionary of kUSGS station IDs and GFLOW labels.

# Searches line by line through the data file and returns (stind & endind) the index number for the lines of interest
# Then uses those indexes to re-write the input for only the data of interest between these lines
stind = 0
k=-1
for cline in indat:
	k += 1
	var = cline.split()[1]
	if stind < 1:
		if 'gage' == cline.split()[1].strip(','):
			stind = k
	elif '! discharge' in cline:
		endind = k 
		break
# keep only the relevant bits
indat = indat[stind+1:endind]

Stations = []
Flows = []
for Station_ID in allin.keys(): # test that all GFLOW gage IDs in *_gages.in file match the predetermined list above
	GF_ID = allin[Station_ID]	
	for eachline in indat:
		line = eachline.strip().split()
		LABEL = line[5]
		if LABEL == GF_ID:
			val,exp = line[4].split('D+')
			exp,junk = exp.split(',')		
			val = float(val)
			exp = float(exp)
			Q = val * (10 ** exp)
			Stations.append(Station_ID)
			Flows.append(Q)
allQ = dict(zip(Stations,Flows)) # construct dictionary of USGS station IDs and simulated flows.

# format output for writing to disk and screen
g04077400gain = allQ['g04077400'] - allQ['p04077150'] - allQ['g04075500'] - allQ['p04076400'] - allQ['p04076080']
p04077595gain = allQ['p04077595'] - allQ['p04075905']
p04076080gain = allQ['p04076080'] - allQ['p04075850'] - allQ['p04075803']
p04077675gain = allQ['p04077675'] - allQ['g04077630'] - allQ['p04077670']
p04075350gain = allQ['p04075350'] - allQ['p04075300'] - allQ['g04075200']
p04070950gain = allQ['p04070950'] - allQ['m04070945']
p04070800gain = allQ['p04070800'] - allQ['m04070771']
p04070720gain = allQ['p04070720'] - allQ['p04070680'] - allQ['p04070606']
p04075850gain = allQ['p04075850'] - allQ['m04075830']
'''TC3_midUSgain = allQ['Tourt3_midUS'] - allQ['Tourt4_start']
TC2_midDSgain = allQ['Tourt2_midDS'] - allQ['Tourt3_midUS']
TC1_DSgain = allQ['Tourt1_end'] - allQ['Tourt2_midDS']
'''
outstring = ('* \n')
output_file.write(outstring)
outstring =  ('g04077400gain = ' + '  {0:.4f}'.format(g04077400gain) + '\n')
output_file.write(outstring)
outstring =  ('p04077595gain = ' + '  {0:.4f}'.format(p04077595gain) + '\n')
output_file.write(outstring)
outstring = ('p04076080gain = ' + '  {0:.4f}'.format(p04076080gain) + '\n')
output_file.write(outstring)
outstring = ('p04077675gain = ' + '  {0:.4f}'.format(p04077675gain) + '\n')
output_file.write(outstring)
outstring = ('p04075350gain = ' + '  {0:.4f}'.format(p04075350gain) + '\n')
output_file.write(outstring)
outstring = ('p04070950gain = ' + '  {0:.4f}'.format(p04070950gain) + '\n')
output_file.write(outstring)
outstring = ('p04070800gain = ' + '  {0:.4f}'.format(p04070800gain) + '\n')
output_file.write(outstring)
outstring = ('p04070720gain = ' + '  {0:.4f}'.format(p04070720gain) + '\n')
output_file.write(outstring)
outstring = ('p04075850gain = ' + '  {0:.4f}'.format(p04075850gain) + '\n')
output_file.write(outstring)
'''outstring = ('TC3_midUSgain = ' + '  {0:.4f}'.format(TC3_midUSgain) + '\n')
output_file.write(outstring)
outstring = ('TC2_midDSgain = ' + '  {0:.4f}'.format(TC2_midDSgain) + '\n')
output_file.write(outstring)
outstring = ('TC1_DSgain =    ' + '  {0:.4f}'.format(TC1_DSgain) + '\n')
output_file.write(outstring)'''
output_file.close()