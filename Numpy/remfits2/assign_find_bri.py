#!  /usr/bin/env python3

"""Assign an pre-initial value of brightness for all objects based on find results"""

import argparse
import numpy as np
import remdefaults
import logs

indtodispname = dict()

def get_dispname(ind):
    """Get dispname from objind"""
    if ind in indtodispname:
        return  indtodispname[ind]
    mycu.execute("SELECT dispname FROM objdata WHERE ind={:d}".format(ind))
    r = mycu.fetchone()
    if r is None:
        r = "Unknown ind {:d}".format(ind)
    else:
        r = r[0]
    indtodispname[ind] = r
    return  r

parsearg = argparse.ArgumentParser(description='Set basic brightness values from findresult records in DB', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
remdefaults.parseargs(parsearg, tempdir=False, inlib=False)
parsearg.add_argument('--filter', type=str, required=True, help='Filter in question')
parsearg.add_argument('--minoccs', type=int, default=5, help='Minimum number of occurences to consider object')
# parsearg.add_argument('--nstds', type=float, help='Clip ADU calculations this number of STDs away')
parsearg.add_argument('--update', action='store_true', help='Update existing values else leave alone')
logs.parseargs(parsearg)

resargs = vars(parsearg.parse_args())
remdefaults.getargs(resargs)
filt = resargs['filter']
minoccs = resargs['minoccs']
# nstds = resargs['nstds']
update = resargs['update']
logging = logs.getargs(resargs)

mydb, mycu = remdefaults.opendb()

fieldselect = []
fieldselect.append('filter=' + mydb.escape(filt))
fieldselect.append("adus!=0")

if not update:
    fieldselect.append(filt + 'bri IS NULL')

selectstatement = "SELECT objind,adus " \
                    "FROM findresult INNER JOIN obsinf ON findresult.obsind=obsinf.obsind " \
                    "INNER JOIN objdata ON findresult.objind=objdata.ind " \
                    "WHERE " + " AND ".join(fieldselect)

mycu.execute(selectstatement)
rows = mycu.fetchall()

if len(rows) == 0:
    logging.die(0, "No brightnesses to be assigned")

resdict = dict()

for objind, adus in rows:
    if objind in resdict:
        resdict[objind].append(adus)
    else:
        resdict[objind] = [adus]

dbchanges = 0

for objind, lst in  resdict.items():
    if len(lst) < minoccs:
        logging.write("Skipping", get_dispname(objind), "only", len(lst), "items")
        continue
    mn = np.mean(lst)
    sd = np.std(lst)
    dbchanges += mycu.execute("UPDATE objdata SET {filt:s}bri={mean:.9e},{filt:s}brisd={std:.9e} WHERE ind={ind:d}".format(filt=filt, mean=mn, std=sd, ind=objind))

logging.write(dbchanges, "updates")
if dbchanges != 0:
    mydb.commit()
