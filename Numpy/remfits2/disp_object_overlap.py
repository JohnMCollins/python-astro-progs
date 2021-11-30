#!  /usr/bin/env python3

"""Display overlaps in find results"""

import argparse
import sys
import remdefaults
import find_results
import objdata


class clashreq:
    """Remember what clashed with what"""
    
    def __init__(self, fr):
        self.name = fr.name
        self.dispname = fr.dispname
        self.clist = dict()
        
#     def __hash__(self):
#         return str.__hash__(self.name)
#     
#     def __eq__(self, other):
#         return isinstance(other, clashreq) and self.name == other.name
    
    def accum(self, name):
        """Accumulate counts of name"""      
        try:
            self.clist[name] += 1
        except KeyError:
            self.clist[name] = 1

# def pfound(flist, level):
#     """Recursively print levels of overlap.
#     There shouldn't be any loops"""
#     for name in sorted(flist.keys()):
#         if name in foundcount:
#             print("\t" * level, ":", foundcount[name].dispname, sep="")
#             pfound(foundcount[name].clist, level + 1)
#         else:
#             print("\t" * level, name, sep="")


parsearg = argparse.ArgumentParser(description='Display overlaps in find results', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('files', nargs='+', type=str, help='Find results files')
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--filter', type=str, help='Filter name to restrict to')

resargs = vars(parsearg.parse_args())
files = resargs['files']
remdefaults.getargs(resargs)
filt = resargs['filter']

foundcount = dict()
objdets = dict()
dispnames = dict()

for fil in files:
    try:
        findres = find_results.load_results_from_file(fil)
    except find_results.FindResultErr as e:
        print(fil, "gave error", e.args[0], file=sys.stderr)
        continue
    if filt and filt != findres.filter:
        continue
    clash_list = findres.overlap_check()
    for first, second in clash_list:
        fobj = findres[first]
        sobj = findres[second]
        if fobj.not_identified():
            continue
        dispnames[fobj.name] = fobj.dispname
        objdets[fobj.name] = (fobj.radeg, fobj.decdeg, fobj.gmag, fobj.apsize)
        sname = sobj.name
        if sobj.not_identified():
            sname = "Other"
        else:
            dispnames[sname] = sobj.dispname
            objdets[sname] = (sobj.radeg, sobj.decdeg, sobj.gmag, sobj.apsize)
        if fobj.name not in foundcount:
            foundcount[fobj.name] = clashreq(fobj)
        foundcount[fobj.name].accum(sname)

try:
    for name in sorted(foundcount.keys()):
        cl = foundcount[name]
        mra, mdec, mmag, maps = objdets[name]
        if mmag is None:
            mmag = 0.0
        print("{dname:s}: {aps:2d} {mag:8.2f} ({rad:10.3f},{decd:10.3f})".format(aps=maps, dname=cl.dispname, mag=mmag, rad=mra, decd=mdec))
        nwid = max([5] + [len(dispnames[n]) for n in cl.clist.keys() if n in dispnames])
        for so in sorted(cl.clist.keys()):
            try:
                sra, sdec, smag, saps = objdets[so]
                if smag is None:
                    smag = 0.0
                sdname = dispnames[so]
                print("\t{dname:s}: {n:5d} {aps:2d} {mag:8.2f} ({rad:.3f},{decd:.3f})".format(aps=saps, dname=sdname, n=cl.clist[so], mag=smag, rad=abs(sra - mra), decd=abs(sdec - mdec)))
            except KeyError:
                print("{dname:<{nwid}s} {n:5d}".format(dname=so, n=cl.clist[so], nwid=nwid))
except KeyboardInterrupt:
    pass
