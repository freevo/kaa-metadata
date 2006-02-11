# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# pnginfo.py - png file parsing
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

# interesting file format info:
# http://www.libpng.org/pub/png/png-sitemap.html#programming
# http://pmt.sourceforge.net/pngmeta/

PNGSIGNATURE = "\211PNG\r\n\032\n"


class PNGInfo(core.ImageInfo):

    def __init__(self,file):
        core.ImageInfo.__init__(self)
        self.iptc = None
        self.mime = 'image/png'
        self.type = 'PNG image'

        signature = file.read(8)
        if ( signature != PNGSIGNATURE ):
            raise mediainfo.KaaMetadataParseError()

        self.meta = {}
        while self._readChunk(file):
            pass
        if len(self.meta.keys()):
            self.appendtable( 'PNGMETA', self.meta )
        for key, value in self.meta.items():
            if key.startswith('Thumb:') or key == 'Software':
                setattr(self, key, value)
                if not key in self.keys:
                    self.keys.append(key)


    def _readChunk(self,file):
        try:
            (length, type) = struct.unpack('>I4s', file.read(8))
        except:
            return 0
        if ( type == 'tEXt' ):
          log.debug('latin-1 Text found.')
          (data, crc) = struct.unpack('>%isI' % length,file.read(length+4))
          (key, value) = data.split('\0')
          self.meta[key] = value

        elif ( type == 'zTXt' ):
          log.debug('Compressed Text found.')
          (data,crc) = struct.unpack('>%isI' % length,file.read(length+4))
          split = data.split('\0')
          key = split[0]
          value = "".join(split[1:])
          compression = ord(value[0])
          value = value[1:]
          if compression == 0:
              decompressed = zlib.decompress(value)
              log.debug("%s (Compressed %i) -> %s" % \
                        (key,compression,decompressed))
          else:
              log.debug("%s has unknown Compression %c" % (key,compression))
          self.meta[key] = value

        elif ( type == 'iTXt' ):
          log.debug('International Text found.')
          (data,crc) = struct.unpack('>%isI' % length,file.read(length+4))
          (key, value) = data.split('\0')
          self.meta[key] = value

        else:
          file.seek(length+4,1)
          log.debug("%s of length %d ignored." % (type, length))
        return 1


factory.register( 'image/png', ('png',), mediainfo.TYPE_IMAGE, PNGInfo )
