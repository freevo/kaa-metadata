# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# dvdinfo.py - parse dvd title structure
# -----------------------------------------------------------------------------
# $Id$
#
# TODO: update the ifomodule and remove the lsdvd parser
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2005 Thomas Schueppel, Dirk Meyer
#
# First Edition: Dirk Meyer <dmeyer@tzi.de>
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
import os
import logging

# kaa imports
from kaa.metadata import mediainfo
from kaa.metadata import factory

# get logging object
log = logging.getLogger('metadata')


class DirInfo(mediainfo.MediaInfo):
    """
    Simple parser for reading a .directory file.
    """
    def __init__(self, directory):
        mediainfo.MediaInfo.__init__(self)

        self.media = 'directory'

        # search .directory
        info = os.path.join(directory, '.directory')
        if os.path.isfile(info):
            f = open(info)
            for l in f.readlines():
                if l.startswith('Icon='):
                    self.image = l[5:]
                    if self.image.startswith('./'):
                        self.image = self.image[2:]
                    self.keys.append('image')
            f.close()
        
factory.register('directory', mediainfo.EXTENSION_DIRECTORY,
                 mediainfo.TYPE_MISC, DirInfo)
