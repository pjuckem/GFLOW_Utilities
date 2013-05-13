import sys

def getPHI(MC_root,sel_real):
    REC_in = open(MC_root + '%d.rec' %(sel_real),'r').readlines()
    
    # find final objective function
    finalfun = False
    for cl,line in enumerate(REC_in):
        if 'objective function' in line.lower():
            finalfun = True
        if finalfun == True:
            if 'sum of squared' in line.lower():
                PHI = float(line.strip().split()[-1])
                break
    return PHI    
