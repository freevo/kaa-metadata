# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# setup.py - Setup script for kaa.metadata
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2005 Thomas Schueppel, Dirk Meyer
#
# First Edition: Thomas Schueppel <stain@acm.org>
# Maintainer:    Dirk Meyer <dmeyer@tzi.de>
#
# Please see the file doc/CREDITS for a complete list of authors.
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

# python imports
import sys
import popen2
import os

try:
    # kaa base imports
    from kaa.base.distribution import Extension, setup
except ImportError:
    print 'kaa.base not installed'
    sys.exit(1)
    
extensions = [ Extension('src/disc/cdrom', ['src/disc/cdrommodule.c']) ]

# check for libdvdread (bad hack!)
# Windows does not have Popen4, so catch exception here
try:
    child = popen2.Popen4('gcc -ldvdread')
    if child.fromchild.readline().find('cannot find') == -1:
        # gcc failed, but not with 'cannot find', so libdvd must be
        # somewhere (I hope)
        extensions.append(Extension('kaa/metadata/disc/ifoparser',
                                    ['src/disc/ifomodule.c'],
                                    libraries=[ 'dvdread' ],
                                    library_dirs=['/usr/local/lib'],
                                    include_dirs=['/usr/local/include']))
    child.wait()
except AttributeError, e:
    print "No Popen4 found. This seems to be Windows."
    print "Installing without libdvdread support."
    # Hack: disable extensions for Windows.
    # This would better be done by a clean detect of windows. But how?
    extensions = []

setup (module      = 'metadata',
       version     = '0.4.99.1',
       description = "Module for retrieving information about media files",
       author      = "Thomas Schueppel, Dirk Meyer",
       scripts     = [ 'bin/mminfo' ],
       ext_modules = extensions
      )
