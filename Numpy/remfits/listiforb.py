#!  /usr/bin/env python3

# @Author: John M Collins <jmc>
# @Date:   2018-08-24T22:41:12+01:00
# @Email:  jmc@toad.me.uk
# @Filename: listobs.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T23:00:35+00:00

import dbops
import remdefaults
import argparse
import datetime
import re
import sys
import parsetime
import remfield
import numpy as np

Format_keys = ('ind', 'iforbind', 'filter', 'type', 'date', 'gain',
               'minval', 'nsminval', 'ansminval', 'maxval', 'nsmaxval', 'ansmaxval',
               'median', 'nsmeidan', 'ansmedian', 'mean', 'nsmean', 'ansmean',
               'std', 'nsstd', 'ansstd', 'skew', 'nsskew', 'ansskew',
               'kurt', 'nskurt', 'anskurt')

Format_header = ('^FITS', '^Serial', '<Filter', '<Type', '<Date/Time', '>Gain',
               '^Minimum', '^Ns min', '^Abs ns min',
               '^Maximum', '^Ns max', '^Abs ns max',
               '^Median', '>Ns meidan', '>Abs ns median',
               '^Mean', '>Ns mean', '>Abs ns mean',
               '^Std', '>Ns std', '>Abs ns std',
               '^Skew', '>Ns skew', '>Abs ns skew',
               '^Kurtosis', '>Ns kurtosis', '>Abs ns kurtosis')

Format_codes = ('d', 'd', 's', '.1s', '%Y-%m-%d %H:%M:%S', '.1f',
                'd', '.3g', '.3g', 'd', '.3g', '.3g',
                '.2f', '.3g', '.3g', '.2f', '.3g', '.3g',
                '.3g', '.3g', '.3g', '.3g', '.3g', '.3g', '.3g', '.3g', '.3g')

Format_accum = (False, False, False, False, False, False,
                True, True, True, True, True, True,
                True, True, True, True, True, True,
                True, True, True, True, True, True, True, True, True)

Fc_dict = dict(zip(Format_keys, Format_codes))
Fh_dict = dict(zip(Format_keys, Format_header))
Facc_dict = dict(zip(Format_keys, Format_accum))

parsearg = argparse.ArgumentParser(description='List flat or bias',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg)
parsetime.parseargs_daterange(parsearg)
parsearg.add_argument('--filter', type=str, nargs='*', help='filters to limit to')
parsearg.add_argument('--type', type=str, default='any', help='Type wanted flat, bias, any')
parsearg.add_argument('--gain', type=float, help='Restrict to given gain value')
remfield.parseargs(parsearg, multstd=True)
parsearg.add_argument('--idonly', action='store_true', help='Just give ids no other data')
parsearg.add_argument('--skprint', action='store_true', help='Print skew and kurtosis')
parsearg.add_argument('--fitsind', action='store_true', help='Print FITS ind not iforbind')
parsearg.add_argument('--format', type=str, help='Specify which fields to display')
parsearg.add_argument('--header', action='store_true', help='Provide a header')
parsearg.add_argument('--totals', action='store_true', help='Print totals')
parsearg.add_argument('--debug', action='store_true', help='Debug SQL query')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)

fieldselect = ["rejreason is NULL"]
fieldselect.append("ind!=0")

try:
    parsetime.getargs_daterange(resargs, fieldselect)
except ValueError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(20)

try:
    remfield.getargs(resargs, fieldselect)
except remfield.RemFieldError as e:
    print(e.args[0], file=sys.stderr)
    sys.exit(21)

idonly = resargs['idonly']
filters = resargs['filter']
typereq = resargs['type']
gain = resargs["gain"]
skprint = resargs['skprint']
fitsind = resargs['fitsind']
format = resargs['format']
header = resargs['header']
ptots = resargs['totals']

if format is None:
    format = []
    if fitsind:
        format.append('ind')
    else:
        format.append('iforbind')
    if not idonly:
        format.append('filter')
        format.append('type')
        format.append('date')
        if gain is None:
            format.append('gain')
        format.append('minval')
        format.append('maxval')
        format.append('median')
        format.append('mean')
        format.append('std')
        if skprint:
            format.append('skew')
            format.append('kurt')
else:
    fbits = format.split(',')
    errors = 0
    for fb in fbits:
        if fb not in Fc_dict:
            print("Format code", fb, "not known", file=sys.stderr)
            errors += 1
    if errors != 0:
        sys.exit(30)
    format = fbits

# See if we need to work out extra fields

extras_reqd = False
for f in format:
    if f[0:3] == "ans" or f[0:2] == "ns":
        extras_reqd = True
        break

mydb, dbcurs = remdefaults.opendb()

if filters is not None:
    qfilt = [ "filter='" + o + "'" for o in filters]
    fieldselect.append("(" + " OR ".join(qfilt) + ")")

if typereq[0] == 'f':
    fieldselect.append("typ='flat'")
elif typereq[0] == 'b':
    fieldselect.append("typ='bias'")

if gain is not None:
    fieldselect.append("ABS(gain-%.3g) < %.3g" % (gain, gain * 1e-3))

sel = remfield.get_extended_args(resargs, "iforbinf", "SELECT ind,iforbind,filter,UPPER(typ),date_obs,gain", fieldselect, extras_reqd)
sel += " ORDER BY date_obs"
if resargs['debug']:
    print("Selection statement:\n", sel, sep="\t", file=sys.stderr)

dbcurs.execute(sel)

dbrows = dbcurs.fetchall()

if header:
    headers = [Fh_dict[i] for i in format]
    maxwids = [len(h[1:]) for h in headers]
else:
    maxwids = [0] * len(format)

accums = []
for f in format:
    if Facc_dict[f]:
        accums.append([])
    else:
        accums.append(None)

# First run through to get widths

Fcodes = ["{" + fc + ":" + Fc_dict[fc] + "}" for fc in format]
for dbrow in dbrows:
    res = dict(zip(Format_keys, dbrow))
    rf = [fc.format(**res) for fc in Fcodes]
    maxwids = [max(n, len(p)) for n, p in zip(maxwids, rf)]

try:
    if header:
        print(" ".join(["{v:{a}{w}s}".format(a=h[0], v=h[1:], w=maxwids[n]) for n, h in enumerate(headers)]))

    Fcodes = []
    TFcodes = []
    for n, fc in enumerate(format):
        if fc == 'date':
            Fcodes.append("{" + fc + ":" + Fc_dict[fc] + "}")
        else:
            Fcodes.append("{" + fc + ":" + str(maxwids[n]) + Fc_dict[fc] + "}")
        TFcodes.append("{:" + str(maxwids[n]) + Fc_dict[fc] + "}")

    for dbrow in dbrows:
        res = dict(zip(Format_keys, dbrow))
        print(" ".join([f.format(**res) for f in Fcodes]))
        if ptots:
            for n, c in enumerate(format):
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
