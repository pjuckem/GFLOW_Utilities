# quickly copy all output from a PEST run with a new name so it can be saved without over
# writing it on the next run.
# "python   rename.py   file_name   additional_text_to_add_to_the_name"

import os
import sys
import shutil
import time

exclude = ['ins','in', 'bat', 'tpl', 'rsd',
            'rst', 'rmr', 'rmf', 'py','cnd', 'mtr'
            'prf', 'res', 'exe', 'xtr', 'dec', 'jst']
currdir = os.getcwd() #determine the current working directory for later moving about

#oldfile = 'menom6c'
#addtext = '_021513'
oldfile = sys.argv[1]
addtext = sys.argv[2]
addtext = str(addtext)
for root,dirs,files in os.walk(currdir):
	for curfile in files:
		curfile = curfile.lower()
		prefix,suffix = curfile.split('.')
		skip = True
		for bad in exclude: # Don't copy files of the type specified above
			if suffix == bad:
				skip = False
				break
		if skip:
			if prefix == oldfile:
				newfile = prefix + addtext + '.' + suffix
				shutil.copy(curfile,newfile)
