#  This program computes a difference between two target water levels from data output to the XTR file.
#  This allows the difference in WL to be computed and used as a target in PEST.
#
#  -Paul Juckem, 4/12/2012
import sys
import math

echo = False

namfile = sys.argv[1]

#  List of TP name representing the targets of interest
HIGH1 = 'TP_000097'
LOW1 = 'TP_000098'

namdat = open(namfile,'r').readlines()
outfilename = namdat[0].strip().split()[0]
xtrfilename = namdat[1].strip().split()[0].upper()
output_file = open(outfilename,'w')

# read in the entire XTR file
indat = open(xtrfilename,'r').readlines()

# Searches line by line through the data file and returns (stind & endind) the index number for the lines of interest
# Then uses those indexes to re-write the input for only the data of interest between these lines
k=-1
for cline in indat:
	k += 1
	if '*      x'  in cline:
		stind = k
	elif '@ gage' in cline:
		endind = k 
		break
# keep only the relevant bits
indat = indat[stind+1:endind]

# goes through each line and looks for the label
for each_line in indat:
	line_stripped = each_line.strip()  #removes leading and trailing whitespace
	line_split = line_stripped.split(',')  # splits a string at commas
	LABEL = line_split[14]
	if LABEL == HIGH1:
		HEAD1h = float(line_split[8])

	elif LABEL == LOW1:
		HEAD1l = float(line_split[8])
	

	# format output for writing to disk and screen
DIFF1 = HEAD1h - HEAD1l  
outstring = ('* \n' + "HEAD DIFFERENCE TARGET #1 = " + '  {0:.4f}'.format(DIFF1) + '\n')

output_file.write(outstring)

output_file.close()

