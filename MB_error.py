#  This program reads the message.out file and reports the MB error for resistance LS.
#
#  -Paul Juckem, 2/1/2013

namfile = 'message.log'
indat = open(namfile,'r').readlines()
outfilename = 'MB_error.out'
output_file = open(outfilename,'w')

line = []
k=0
for cline in indat: # looping ensures we pull the last MB error.
	k += 1
	line = cline.split()
	if len(line) > 5:
		if line[1] == 'line' and line[2] == 'sinks' and line[3] =='with':
			MBerror = float(line[7])

outstring = ('* \n' + 'MB_error = ' + '  {0:.4f}'.format(MBerror) + '\n')
output_file.write(outstring)
output_file.close()