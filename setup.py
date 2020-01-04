# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# setup.py - Setup script for kaa.metadata
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2006 Thomas Schueppel, Dirk Meyer
#
# First Edition: Thomas Schueppel <stain@acm.org>
# Maintainer:    Dirk Meyer <https://github.com/Dischi>
#
# Please see the file AUTHORS for a complete list of authors.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------------

MODULE = 'metadata'
VERSION = '0.7.8'
REQUIRES = ['kaa-base']


# python imports
import sys

if 'pip-egg-info' in sys.argv:
    # Installing via pip; ensure dependencies are visible.
    from setuptools import setup
    setup(name='kaa-' + MODULE, version=VERSION, install_requires=REQUIRES)
    sys.exit(0)


try:
    # kaa base imports
    from kaa.base.distribution.core import Extension, setup
except ImportError:
    print 'kaa.base not installed'
    sys.exit(1)


# cdrom extension, FIXME: check if it will compile
cdrom = Extension('kaa/metadata/disc/_cdrom', ['src/disc/cdrommodule.c'])

# check for libdvdread
ifoparser = Extension('kaa.metadata.disc._ifoparser', ['src/disc/ifomodule.c'],
                      libraries=[ 'dvdread' ])

try:
    if not ifoparser.check_cc([], '', '-ldvdread'):
        print 'Warning: libdvdread is missing.'
        raise AttributeError()

    if not ifoparser.check_cc(['<dvdread/dvd_reader.h>'], '', '-ldvdread'):
        print 'Warning: libdvdread header file is missing.'
        raise AttributeError()

    ext_modules = [ cdrom, ifoparser ]
except AttributeError:
    print 'The DVD parser will be disabled'
    ext_modules = [ cdrom ]

if not cdrom.has_python_h():
    print "---------------------------------------------------------------------"
    print "Python headers not found; please install python development package."
    print "Rom drive support will be unavailable"
    print "---------------------------------------------------------------------"
    ext_modules = [ ]

exiv2 = Extension('kaa.metadata.image.exiv2', ['src/image/exiv2.cpp'])
if exiv2.check_library('exiv2', '0.18'):
    print 'Building experimental exiv2 parser'
    ext_modules.append(exiv2)
    
setup(
    module = MODULE,
    version = VERSION,
    license = 'GPL',
    summary = 'Module for retrieving information about media files',
    author = 'Thomas Schueppel, Dirk Meyer, Jason Tackaberry',
    scripts = [ 'bin/mminfo' ],
    rpminfo = {
        'requires': 'python-kaa-base >= 0.1.2, libdvdread >= 0.9.4',
        'build_requires': 'python-kaa-base >= 0.1.2, libdvdread-devel >= 0.9.4, python-devel >= 2.3.0',
        'obsoletes': 'mmpython'
    },
    ext_modules = ext_modules,
    install_requires = REQUIRES,
    namespace_packages = ['kaa']
)

