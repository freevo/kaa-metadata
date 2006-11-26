# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# datainfo.py - info about a normal data disc
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2006 Thomas Schueppel, Dirk Meyer
#
# First Edition: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
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

# kaa imports
from kaa.metadata import mediainfo
from kaa.metadata import factory
from discinfo import DiscInfo

class DataDiscInfo(DiscInfo):
    def __init__(self,device):
        DiscInfo.__init__(self)
        if DiscInfo.isDisc(self, device) != 2:
            raise mediainfo.KaaMetadataParseError()
        self.context = 'unknown'
        self.offset = 0
        self.mime = 'unknown/unknown'
        self.type = 'CD'
        self.subtype = 'data'


factory.register( 'cd/unknown', mediainfo.EXTENSION_DEVICE,
                  mediainfo.TYPE_NONE, DataDiscInfo )
