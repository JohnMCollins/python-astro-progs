#!  /usr/bin/env python3

"""List number of objservations for each filter"""

import argparse
import remdefaults


def thou(n):
    """Prinv n with ,s separating thousands"""
    if pthou:
        return  "{:,d}".format(n)
    return "{:d}".format(n)


parsearg = argparse.ArgumentParser(description='List number by filter',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, libdir=False, tempdir=False)
parsearg.add_argument('--objects', type=str, nargs='*', help='Objects to limit to')
parsearg.add_argument('--gain', type=float, help='Restrict to given gain value')
parsearg.add_argument('--latex', action='store_true', help='Latex output')
parsearg.add_argument('--thousands', action='store_false', help='Print thousand separators')

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
objlist = resargs['objects']
latex = resargs['latex']
gain = resargs['gain']
pthou = resargs['thousands']

mydb, dbcurs = remdefaults.opendb()

fields = []

if objlist is not None:
    qobj = [ "object='" + o + "'" for o in objlist]
    fields.append("(" + " OR ".join(qobj) + ")")
if gain is not None:
    fields.append("ABS(gain-{:.3g}) < {:.3g}".format(gain, gain * 1e-3))

sel = ''
if len(fields) != 0:
    sel = " WHERE " + " AND ".join(fields)

dbcurs.execute("SELECT filter,COUNT(*) FROM obsinf" + sel + " GROUP BY filter")

results = dict()

total = 0
for row in dbcurs.fetchall():
    filt, count = row
    results[filt] = count
    total += count

if latex:
    for filt in 'girzHJK':
        try:
            print(filt, thou(results[filt]), sep=' & ', end=' \\\\\n')
        except KeyError:
            pass
    try:
        print('GRISM', thou(results['GRI']), sep=' & ', end=' \\\\\n')
    except KeyError:
        pass
    print("\\hline")
    print('Total', thou(total), sep=' & ', end=' \\\\\n')

else:
    fnames = []
    tots = []
    for filt in 'girzHJK':
        try:
            tots.append(thou(results[filt]))
            fnames.append(filt)
        except KeyError:
            pass
    try:
        tots.append(thou(results['GRI']))
        fnames.append('GRISM')
    except KeyError:
        pass

    fnames.append("Total")
    tots.append(thou(total))
    nlength = max([len(f) for f in fnames])
    tlength = max([len(t) for t in tots])
    for f, t in zip(fnames, tots):
        print("{f:{nl}s} {t:>{tl}s}".format(f=f, t=t, nl=nlength, tl=tlength))
