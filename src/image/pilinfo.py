# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# pilinfo.py - basic image parsing using Imaging (PIL)
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
import os

# kaa imports
from kaa.metadata import factory
from kaa.metadata import mediainfo
from core import ImageInfo, PIL

class PILInfo(ImageInfo):
    """
    Simple class getting informations based on PIL
    """
    def __init__(self, file):
        ImageInfo.__init__(self)
        if not os.path.splitext(file.name)[1].lower() in ('.gif', '.bmp'):
            raise mediainfo.KaaMetadataParseError()
        if not PIL:
            raise mediainfo.KaaMetadataParseError()
        self.mime  = ''
        self.type  = ''
        self.add_imaging_information(file.name)
        self.parse_external_files(file.name)

factory.register( 'image/gif', ('gif',), mediainfo.TYPE_IMAGE, PILInfo )
factory.register( 'image/bmp', ('bmp',), mediainfo.TYPE_IMAGE, PILInfo )
