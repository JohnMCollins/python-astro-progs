#! /usr/bin/env python3

"""Display distribution of maximum values for target"""

import argparse
import sys
# import warnings
# from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
import matplotlib.pyplot as plt
import miscutils
import remdefaults
import remgeom
import objdata

# Shut up warning messages

# warnings.simplefilter('ignore', AstropyWarning)
# warnings.simplefilter('ignore', AstropyUserWarning)
# warnings.simplefilter('ignore', UserWarning)
# autils.suppress_vo_warnings()

rg = remgeom.load()

parsearg = argparse.ArgumentParser(description='Display maximum values different filters', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False)
parsearg.add_argument('target', type=str, nargs=1, help='Target analysis is for')
parsearg.add_argument('--bins', type=int, default=20, help='Histogram bins')
parsearg.add_argument('--colour', type=str, default='b', help='Histogram colour')
parsearg.add_argument('--maxlin', type=float, nargs='+', help='Maximum limit on linearity')

figout = rg.disp_argparse(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
target = resargs['target'][0]
histbins = resargs['bins']
histcolour = resargs['colour']
maxlin = resargs['maxlin']

figout = rg.disp_getargs(resargs)

db, dbcurs = remdefaults.opendb()

targobj = objdata.ObjData(target)
try:
    targobj.get(dbcurs)
except objdata.ObjDataError:
    print("Cannot find target object", target, file=sys.stderr)
    sys.exit(10)

if not targobj.is_target():
    print(target, "is not a target object in vicinity of", targobj.vicinity)
    sys.exit(11)

targnames = ["object=" + db.escape(m) for m in targobj.list_allnames(dbcurs)]
dbcurs.execute("SELECT filter,maxv FROM obsinf WHERE rejreason IS NULL AND filter REGEXP '[griz]' AND ("
               +" OR ".join(targnames) + ")")

filterobj = dict(g=[], r=[], i=[], z=[])

for filt, maxv in dbcurs.fetchall():
    filterobj[filt].append(maxv)

plotfigure = rg.plt_figure()
plotfigure.canvas.manager.set_window_title("Max values for each of 4 filters")

for filt, subp in ('i', 221), ('g', 222), ('z', 223), ('r', 224):

    arr = filterobj[filt]
    plt.subplot(subp)
    plt.hist(arr, bins=histbins, color=histcolour)
    if maxlin is not None:
        for m in maxlin:
            plt.axvline(m, color='k')
    plt.xlabel(filt + " filter")

plt.tight_layout()
if figout is None:
    plt.show()
else:
    figout = miscutils.replacesuffix(figout, ".png")
    plotfigure.savefig(figout)
    plt.close(plotfigure)
