#! /usr/bin/env python

import sys
import os
import os.path
import locale
import argparse
import xml.etree.ElementTree as ET
import xmlutil
import datarange

parsearg = argparse.ArgumentParser(description='Get table of EWs from spectral data files')
parsearg.add_argument('--rangefile', type=str, help='Range file')
parsearg.add_argument('--specfile', type=str, help='Spectrum data control file')
parsearg.add_argument('--ewrange', type=str, default='halpha', help='Range to select for calculating EW')
parsearg.add_argument('--bluehorn', type=str, help='Range 1 for calculating sub-peaks')
parsearg.add_argument('--redhorn', type=str, help='Range 2 for calculating sub-peaks')

resargs = vars(parsearg.parse_args())

rangefile = resargs['rangefile']
specfile = resargs['specfile']
ewrangename = resargs['ewrange']
bhrangename = resargs['bluehorn']
rhrangename = resargs['redhorn']

