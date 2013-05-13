import numpy as np

class convergence_critera:
    def __init__(self,name):
        if name.lower() == "linesinks with_resistance":
            self.name2 = "line sinks with resistance"
        elif name.lower == "linesinks no_resistance":
            self.name2 = "line sinks without resistance"
        else:
            self.name2 = name.lower()
        self.name = name.lower()
        self.convcrit = 0.0
        self.convval = 0.0
        self.checked = False
        


def getMB(conv_crits,read_conv=True):

    # flag to return indicating whether convergence was acheived
    allCONV = True
    
    indat = open('MESSAGE.LOG','r').readlines()
    # flip around to read from the end
    indat.reverse()
    
    crit_names = []
    for cc in conv_crits:
        crit_names.append(cc.name)
    crit_names2 = []
    for cc in conv_crits:
        crit_names2.append(cc.name2)        
    # first look for the convergence criteria if requested
    if read_conv:
        conv_data = open('Converge.tab','r').readlines()
        for line in conv_data:
            if '*' not in line:
                tmp = line.strip()
                for i,crit in enumerate(crit_names):
                    if crit in tmp:
                        conv_crits[i].convcrit = float(tmp.split()[-1])            
                        
    
    # now look for the various convergence data from MESSAGE.LOG
    for i,cc in enumerate(crit_names2):
        if 'waterbalance' in cc.lower():
            hajime = True
            for line in indat:
                tmp = line.strip()
                if (('water balance deficiency' in tmp.lower()) and ('%' in tmp.lower())):
                    if hajime == True:
                        hajime = False
                    else:
                        conv_crits[i].convval = float(tmp.split()[-2].lower().replace('d','e'))
                        conv_crits[i].checked = True
                        break
        else:
            for line in indat:
                tmp = line.strip()
                if cc in tmp:
                    conv_crits[i].convval = float(tmp.split()[-2].lower().replace('d','e'))
                    conv_crits[i].checked = True
                    break

    for cc in conv_crits:
        if cc.convval >= cc.convcrit:
            allCONV = False
            break
    return allCONV,conv_crits
    