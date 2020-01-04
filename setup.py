# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# setup.py - Setup script for kaa.metadata
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

# python imports
import os
from setuptools import setup

packages = []
package_dir = {}
for dirpath, dirnames, files in os.walk('src'):
    python_dirpath = 'kaa.metadata' + dirpath.replace('/', '.')[3:]
    if '__init__.py' in files:
        package_dir[python_dirpath] = dirpath
        packages.append(python_dirpath)

setup(
    name = 'kaa-metadata',
    version = VERSION,
    license = 'GPL',
    author = 'Thomas Schueppel, Dirk Meyer, Jason Tackaberry',
    package_dir = package_dir,
    packages = packages,
    scripts = [ 'bin/mminfo' ],
    zip_safe=False,
)
