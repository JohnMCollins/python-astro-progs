#!  /usr/bin/env python3

"""List observations in various formats"""

import argparse
import sys
import remdefaults
import remtargets
import parsetime
import remfield
import numpy as np

Format_keys = ('ind', 'obsind', "object", 'filter', 'dither', 'date', 'gain', 'orient',
               'startx', 'starty', 'cols', 'rows', 'airmass',
               'minval', 'nsminval', 'ansminval', 'maxval', 'nsmaxval', 'ansmaxval',
               'median', 'nsmeidan', 'ansmedian', 'mean', 'nsmean', 'ansmean',
               'std', 'nsstd', 'ansstd', 'skew', 'nsskew', 'ansskew',
               'kurt', 'nskurt', 'anskurt', 'orient')

Format_header = ('^FITS', '^Serial', "<Object", '<Filter', '>Dither', '<Date/Time', '>Gain', '>Orient',
               '>startx', '>starty', '>cols', '>rows', '>airmass'
               '^Minimum', '^Ns min', '^Abs ns min',
               '^Maximum', '^Ns max', '^Abs ns max',
               '^Median', '>Ns meidan', '>Abs ns median',
               '^Mean', '>Ns mean', '>Abs ns mean',
               '^Std', '>Ns std', '>Abs ns std',
               '^Skew', '>Ns skew', '>Abs ns skew',
               '^Kurtosis', '>Ns kurtosis', '>Abs ns kurtosis')

Format_codes = ('d', 'd', 's', 's', 'd', '%Y-%m-%d %H:%M:%S', '.1f', 'd',
                'd', 'd', 'd', 'd', '.4f',
                'd', '.3g', '.3g', 'd', '.3g', '.3g',
                '.2f', '.3g', '.3g', '.2f', '.3g', '.3g',
                '.3g', '.3g', '.3g', '.3g', '.3g', '.3g', '.3g', '.3g', '.3g')

Format_accum = (False, False, False, False, False, False, False,
                False, False, False, False, False,
                True, True, True, True, True, True,
                True, True, True, True, True, True,
                True, True, True, True, True, True, True, True, True, False)

Fc_dict = dict(zip(Format_keys, Format_codes))
Fh_dict = dict(zip(Format_keys, Format_header))
Facc_dict = dict(zip(Format_keys, Format_accum))

parsearg = argparse.ArgumentParser(description='List available observations',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('obsinds', type=int, nargs='*', help='Observation ids to restrict to')
remdefaults.parseargs(parsearg)
parsetime.parseargs_daterange(parsearg)
parsearg.add_argument('--objects', type=str, nargs='*', help='Objects to limit to')
parsearg.add_argument('--targets', action='store_false', help='Add targets to objects to limit to')
parsearg.add_argument('--dither', type=int, nargs='*', default=[0], help='Dither ID to limit to')
parsearg.add_argument('--filter', type=str, nargs='*', help='filters to limit to')
parsearg.add_argument('--gain', type=float, help='Restrict to given gain value')
parsearg.add_argument('--airmass', type=str, help='Restrict to min:max airmass values')
parsearg.add_argument('--orientation', type=int, help='Restrict to given orientation value (quarter turns)')
parsearg.add_argument('--startx', type=int, help='Restrict to given startx value on CCD')
parsearg.add_argument('--starty', type=int, help='Restrict to given starty value on CCD')
parsearg.add_argument('--rows', type=int, help='Restrict to given rows value on CCD')
parsearg.add_argument('--cols', type=int, help='Restrict to given cols value on CCD')
parsearg.add_argument('--summary', action='store_true', help='Just summarise objects and number of obs')
parsearg.add_argument('--idonly', action='store_true', help='Just give ids no other data')
parsearg.add_argument('--fitsind', action='store_true', help='Show fits ind not obs ind')
parsearg.add_argument('--hasfile', action='store_false', help='Only display obs which have FITS files')
remfield.parseargs(parsearg, multstd=True)
parsearg.add_argument('--debug', action='store_true', help='Display selection command')
parsearg.add_argument('--format', type=str, help='Specify which fields to display')
parsearg.add_argument('--header', action='store_true', help='Provide a header')
parsearg.add_argument('--totals', action='store_true', help='Print totals'
                      )
resargs = vars(parsearg.parse_args())
obsinds = resargs['obsinds']
remdefaults.getargs(resargs)

fieldselect = ["rejreason is NULL"]
try:
    parsetime.getargs_daterange(resargs, fieldselect)
except ValueError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)

idonly = resargs['idonly']
objlist = resargs['objects']
list_targets = resargs['targets']
dither = resargs['dither']
filters = resargs['filter']
summary = resargs['summary']
fitsind = resargs['fitsind']
orient = resargs['orientation']
disp_startx = resargs['startx']
disp_starty = resargs['starty']
disp_rows = resargs['rows']
disp_cols = resargs['cols']
gain = resargs["gain"]
hasfile = resargs['hasfile']
debug = resargs['debug']
formatlines = resargs['format']
header = resargs['header']
ptots = resargs['totals']

if idonly and (summary or formatlines is not None or header):
    print("Cannot have idonly and specify format or header or summary", file=sys.stderr)
    sys.exit(10)

if idonly:
    if summary:
        print("Cannot have --idonly and --summary together", file=sys.stderr)
        sys.exit(10)
    if header:
        print("Cannot have --idonly and --header together", file=sys.stderr)
        sys.exit(11)
    if formatlines is not None:
        print("Cannot have --idonly and --format together", file=sys.stderr)
        sys.exit(12)
elif summary:
    if header:
        print("Cannot have --summary and --header together", file=sys.stderr)
        sys.exit(13)
    if formatlines is not None:
        print("Cannot have --summary and --format together", file=sys.stderr)
        sys.exit(14)

if formatlines is None:
    formatlines = []
    if fitsind:
        formatlines.append('ind')
    else:
        formatlines.append('obsind')
    if not idonly:
        formatlines.append('date')
        formatlines.append('object')
        formatlines.append('filter')
        # formatlines.append('dither')
else:
    fbits = formatlines.split(',')
    errors = 0
    for fb in fbits:
        if fb not in Fc_dict:
            print("Format code", fb, "not known", file=sys.stderr)
            errors += 1
    if errors != 0:
        sys.exit(30)
    formatlines = fbits

extras_reqd = False
for f in formatlines:
    if f[0:3] == "ans" or f[0:2] == "ns":
        extras_reqd = True
        break

if len(obsinds) != 0:
    oil = []
    for oind in obsinds:
        oil.append("obsind=%d" % oind)
    fieldselect.append("(" + " OR ".join(oil) + ")")

mydb, dbcurs = remdefaults.opendb()

if hasfile:
    fieldselect.append("ind!=0")

qobj = []
if objlist is not None:
    for o in objlist:
        qobj.append("object=" + mydb.escape(o))
    # Only add targets if we haven't named a target in the objlist
    if list_targets and remtargets.notargets(objlist):
        remtargets.remtargets(dbcurs, qobj)
elif list_targets:
    remtargets.remtargets(dbcurs, qobj)
if len(qobj) != 0:
    if len(qobj) == 1:
        fieldselect += qobj
    else:
        fieldselect.append("(" + " OR ".join(qobj) + ")")

if filters is not None:
    qfilt = [ "filter='" + o + "'" for o in filters]
    fieldselect.append("(" + " OR ".join(qfilt) + ")")

if len(dither) != 0 and dither[0] != -1:
    qdith = [ "dithID=" + str(d) for d in dither]
    if len(qdith) == 1:
        fieldselect.append(qdith[0])
    else:
        fieldselect.append("(" + " OR ".join(qdith) + ")")

if gain is not None:
    fieldselect.append("ABS(gain-%.3g) < %.3g" % (gain, gain * 1e-3))

if orient is not None:
    fieldselect.append("orient=%d" % orient)

if disp_startx is not None:
    fieldselect.append("startx={:d}".format(disp_startx))
if disp_starty is not None:
    fieldselect.append("starty={:d}".format(disp_starty))
if disp_rows is not None:
    fieldselect.append("nrows={:d}".format(disp_rows))
if disp_cols is not None:
    fieldselect.append("ncols={:d}".format(disp_cols))

try:
    remfield.getargs(resargs, fieldselect)
    remfield.parsepair(resargs, "airmass", fieldselect, "airmass")
    if summary:
        sel = "SELECT object,COUNT(*) FROM obsinf WHERE " + " AND ".join(fieldselect) + " GROUP BY object ORDER BY object"
    else:
        sel = remfield.get_extended_args(resargs, "obsinf", "SELECT ind,obsind,object,filter,dithID,date_obs,gain,orient,startx,starty,ncols,nrows,airmass", fieldselect, extras_reqd)
        sel += " ORDER BY date_obs"
except remfield.RemFieldError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(21)

if debug:
    print("Selection statement:\n", sel, sep="\t", file=sys.stderr)

dbcurs.execute(sel)
dbrows = dbcurs.fetchall()
if summary:
    for row in dbrows:
        print("{:<12s}{:7d}".format(row[0], row[1]))
    sys.exit(0)

if header:
    headers = [Fh_dict[i] for i in formatlines]
    maxwids = [len(h[1:]) for h in headers]
else:
    maxwids = [0] * len(formatlines)

# First run through to get widths

Fcodes = ["{" + fc + ":" + Fc_dict[fc] + "}" for fc in formatlines]
for dbrow in dbrows:
    res = dict(zip(Format_keys, dbrow))
    rf = [fc.format(**res) for fc in Fcodes]
    maxwids = [max(n, len(p)) for n, p in zip(maxwids, rf)]

accums = []
for f in formatlines:
    if Facc_dict[f]:
        accums.append([])
    else:
        accums.append(None)

try:
    if header:
        print(" ".join(["{v:{a}{w}s}".format(a=h[0], v=h[1:], w=maxwids[n]) for n, h in enumerate(headers)]))

    Fcodes = []
    TFcodes = []
    for n, fc in enumerate(formatlines):
        if fc == 'date':
            Fcodes.append("{" + fc + ":" + Fc_dict[fc] + "}")
        else:
            Fcodes.append("{" + fc + ":" + str(maxwids[n]) + Fc_dict[fc] + "}")
        TFcodes.append("{:" + str(maxwids[n]) + Fc_dict[fc] + "}")

    for dbrow in dbrows:
        res = dict(zip(Format_keys, dbrow))
        print(" ".join([f.format(**res) for f in Fcodes]))
        if ptots:
            for n, c in enumerate(formatlines):
                try:
                    accums[n].append(res[c])
                except AttributeError:
                    pass
except (KeyboardInterrupt, BrokenPipeError):
    sys.exit(0)

if ptots and len(dbrows) > 1:
    aaccums = []
    for a in accums:
        if a is not None:
            aaccums.append(np.array(a))
        else:
            aaccums.append(None)
    for func, descr, fl in zip((np.min, np.max, np.median, np.mean, np.std), ("Minimum", "Maximum", "Median", "Mean", "Std"), (False, False, True, True, True)):
        outline = []
        for a, w, fc in zip(aaccums, maxwids, TFcodes):
            if a is None:
                outline.append(" " * w)
            elif fl and fc[-2] == 'd':
                outline.append(fc.format(int(round(func(a)))))
            else:
                outline.append(fc.format(func(a)))
        outline.append(descr)
        print(" ".join(outline))
