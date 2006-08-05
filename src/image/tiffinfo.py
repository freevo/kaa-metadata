# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# tiffinfo.py - tiff file parsing
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

# python imports
import struct
import zlib
import logging

# kaa imports
from kaa.metadata import mediainfo
from kaa.metadata import factory

# image imports
import IPTC
import EXIF
import core

# get logging object
log = logging.getLogger('metadata')


MOTOROLASIGNATURE = 'MM\x00\x2a'
INTELSIGNATURE = 'II\x2a\x00'

# http://partners.adobe.com/asn/developer/pdfs/tn/TIFF6.pdf

class TIFFInfo(core.ImageInfo):

    def __init__(self,file):
        core.ImageInfo.__init__(self)
        self.iptc = None
        self.mime = 'image/tiff'
        self.type = 'TIFF image'
        self.intel = 0
        iptc = {}
        header = file.read(8)

        if header[:4] == MOTOROLASIGNATURE:
            self.intel = 0
            (offset,) = struct.unpack(">I", header[4:8])
            file.seek(offset)
            (len,) = struct.unpack(">H", file.read(2))
            app = file.read(len*12)
            for i in range(len):
                (tag, type, length, value, offset) = \
                      struct.unpack('>HHIHH', app[i*12:i*12+12])
                if tag == 0x8649:
                    file.seek(offset,0)
                    iptc = IPTC.parseiptc(file.read(1000))
                elif tag == 0x0100:
                    if value != 0:
                        self.width = value
                    else:
                        self.width = offset
                elif tag == 0x0101:
                    if value != 0:
                        self.height = value
                    else:
                        self.height = offset

        elif header[:4] == INTELSIGNATURE:
            self.intel = 1
            (offset,) = struct.unpack("<I", header[4:8])
            file.seek(offset,0)
            (len,) = struct.unpack("<H", file.read(2))
            app = file.read(len*12)
            for i in range(len):
                (tag, type, length, offset, value) = \
                      struct.unpack('<HHIHH', app[i*12:i*12+12])
                if tag == 0x8649:
                    file.seek(offset)
                    iptc = IPTC.parseiptc(file.read(1000))
                elif tag == 0x0100:
                    if value != 0:
                        self.width = value
                    else:
                        self.width = offset
                elif tag == 0x0101:
                    if value != 0:
                        self.height = value
                    else:
                        self.height = offset
        else:
            raise mediainfo.KaaMetadataParseError()

        if iptc:
            self.setitem( 'title', iptc, 'by-line title')
            self.setitem( 'title', iptc, 'headline')
            self.setitem( 'date' , iptc, 'date created')
            self.setitem( 'keywords', iptc, 'keywords')
            self.setitem( 'artist', iptc, 'writer/editor')
            self.setitem( 'artist', iptc, 'credit')
            self.setitem( 'country', iptc, 'country/primary location name')
            self.setitem( 'caption', iptc, 'caption/abstract')
            self.setitem( 'city', iptc, 'city')
            self.appendtable( 'IPTC', iptc )


factory.register( 'image/tiff', ('tif','tiff'), mediainfo.TYPE_IMAGE, TIFFInfo)
