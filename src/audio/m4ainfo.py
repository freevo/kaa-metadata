# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# m4ainfo.py - m4a file parser
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2005 Thomas Schueppel, Dirk Meyer
#
# First Edition: Aubin Paul <aubin@outlyer.org>
# Maintainer:    Dirk Meyer <dmeyer@tzi.de>
#
# Please see the file AUTHORS for a complete list of authors.
#
# Based on a sample implementation posted to daap-dev mailing list by
# Bob Ippolito <bob@redivi.com>
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
import struct
import logging

# kaa imports
from kaa.metadata import mediainfo
from kaa.metadata import factory

# get logging object
log = logging.getLogger('metadata')

class Mpeg4(mediainfo.MusicInfo):
    def __init__(self, file):
        self.containerTags = ('moov', 'udta', 'trak', 'mdia', 'minf', 'dinf',
                              'stbl', 'meta', 'ilst', '----')
        self.skipTags = {'meta':4 }

        mediainfo.MusicInfo.__init__(self)
        self.valid = 0
        returnval = 0
        while returnval == 0:
            try:
                self.readNextTag(file)
            except ValueError:
                returnval = 1
        if not self.valid:
            raise mediainfo.KaaMetadataParseError()


    def readNextTag(self, file):
        length, name = self.readInt(file), self.read(4, file)
        length -= 8
        if length < 0 or length > 1000:
            raise ValueError, "Oops?"

        if name in self.containerTags:
            self.read(self.skipTags.get(name, 0), file)
            data = '[container tag]'
        else:
            data = self.read(length, file)
        if name == '\xa9nam':
            self.title = data[8:]
            self.valid = 1
        if name == '\xa9ART':
            self.artist = data[8:]
            self.valid = 1
        if name == '\xa9alb':
            self.album = data[8:]
            self.valid = 1
        if name == 'trkn':
            # Fix this
            self.trackno = data
            self.valid = 1
        if name == '\xa9day':
            self.year = data[8:]
            self.valid = 1
        if name == '\xa9too':
            self.encoder = data[8:]
            self.valid = 1
        return 0

    def read(self, b, file):
        data = file.read(b)
        if len(data) < b:
            raise ValueError, "EOF"
        return data

    def readInt(self, file):
        return struct.unpack('>I', self.read(4, file))[0]


factory.register( 'application/m4a', ('m4a',), mediainfo.TYPE_MUSIC, Mpeg4)
