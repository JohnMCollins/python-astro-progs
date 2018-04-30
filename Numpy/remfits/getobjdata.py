#!  /usr/bin/env python

# Get object data and maintain XML Database

import xml.etree.ElementTree as ET
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning
from astroquery.simbad import Simbad
from astropy import coordinates
from astropy.time import Time
import datetime
import astropy.units as u
import astroquery.utils as autils
import numpy as np
import os.path
import argparse
import warnings
import xmlutil

SPI_DOC_NAME = "OBJINFO"
SPI_DOC_ROOT = "objinfo"

# Shut up warning messages

warnings.simplefilter('ignore', AstropyWarning)
warnings.simplefilter('ignore', AstropyUserWarning)
warnings.simplefilter('ignore', UserWarning)
autils.suppress_vo_warnings()

parsearg = argparse.ArgumentParser(description='Get object info into database', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parsearg.add_argument('objects', nargs='+', type=str, help='Object names to process')
parsearg.add_argument('--libfile', type=str, default='~/lib/stellar_objdata.xml', help='File to use for database')
parsearg.add_argument('--update', action='store_true', help='Update existing names')
parsearg.add_argument('--delete', action='store_true', help='Delete names')

resargs = vars(parsearg.parse_args())

objnames = resargs['objects']
libfile = os.path.expanduser(resargs['libfile'])
update = resargs['update']
delete = resargs['delete']

if os.path.isfile(libfile):
    doc, root = xmlutil.load_file(libfile, SPI_DOC_ROOT)
else:
    doc, root = xmlutil.init_save(SPI_DOC_NAME, SPI_DOC_ROOT)


