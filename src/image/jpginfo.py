# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# jpginfo.py - jpg file parsing
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
import logging

# kaa imports
from kaa.metadata import mediainfo
from kaa.metadata import factory

# image imports
import EXIF
import core
from iptcinfo import IPTCInfo, c_datasets as IPTCkeys

# get logging object
log = logging.getLogger('metadata')

# interesting file format info:
# http://www.dcs.ed.ac.uk/home/mxr/gfx/2d-hi.html
# http://www.funducode.com/freec/Fileformats/format3/format3b.htm

SOF = { 0xC0 : "Baseline",
        0xC1 : "Extended sequential",
        0xC2 : "Progressive",
        0xC3 : "Lossless",
        0xC5 : "Differential sequential",
        0xC6 : "Differential progressive",
        0xC7 : "Differential lossless",
        0xC9 : "Extended sequential, arithmetic coding",
        0xCA : "Progressive, arithmetic coding",
        0xCB : "Lossless, arithmetic coding",
        0xCD : "Differential sequential, arithmetic coding",
        0xCE : "Differential progressive, arithmetic coding",
        0xCF : "Differential lossless, arithmetic coding",
}

class JPGInfo(core.ImageInfo):

    def __init__(self,file):
        core.ImageInfo.__init__(self)
        self.mime = 'image/jpeg'
        self.type = 'jpeg image'

        if file.read(2) != '\xff\xd8':
            raise mediainfo.KaaMetadataParseError()

        file.seek(-2,2)
        if file.read(2) != '\xff\xd9':
            # Normally an JPEG should end in ffd9. This does not however
            # we assume it's an jpeg for now
            log.info("Wrong encode found for jpeg")

        file.seek(2)
        app = file.read(4)
        self.meta = {}
        iptc_info = None
        
        while (len(app) == 4):
            (ff,segtype,seglen) = struct.unpack(">BBH", app)
            if ff != 0xff: break
            log.debug("SEGMENT: 0x%x%x, len=%d" % (ff,segtype,seglen))
            if segtype == 0xd9:
                break
            elif SOF.has_key(segtype):
                data = file.read(seglen-2)
                (precision,self.height,self.width,\
                 num_comp) = struct.unpack('>BHHB', data[:6])
            elif segtype == 0xed:
                iptc_info = IPTCInfo(file.name, force=True)
                break
            elif segtype == 0xe7:
                # information created by libs like epeg
                data = file.read(seglen-2)
                if data.count('\n') == 1:
                    key, value = data.split('\n')
                    self.meta[key] = value
            elif segtype == 0xfe:
                self.comment = file.read(seglen-2)
            else:
                file.seek(seglen-2,1)
            app = file.read(4)
        file.seek(0)
        exif_info = EXIF.process_file(file)

        if exif_info:
            self.setitem( 'date', exif_info, 'Image DateTime', True )
            self.setitem( 'artist', exif_info, 'Image Artist', True )
            self.setitem( 'hardware', exif_info, 'Image Model', True )
            self.setitem( 'software', exif_info, 'Image Software', True )
            self.setitem( 'thumbnail', exif_info, 'JPEGThumbnail', False )
            self.appendtable( 'EXIF', exif_info )

        if iptc_info:
            i = iptc_info.data
            iptc_info = {}
            for key, value in IPTCkeys.items():
                if key in i and i[value]:
                    iptc_info[value] = i[value]
            self.setitem( 'title', iptc_info, 'by-line title', True )
            self.setitem( 'title', iptc_info, 'headline', True )
            self.setitem( 'date' , iptc_info, 'date created', True )
            self.setitem( 'keywords', iptc_info, 'keywords', False )
            self.setitem( 'artist', iptc_info, 'writer/editor', True )
            self.setitem( 'artist', iptc_info, 'credit', True )
            self.setitem( 'country', iptc_info, 'country/primary location name', True )
            self.setitem( 'caption', iptc_info, 'caption/abstract', True )
            self.setitem( 'city', iptc_info, 'city', True )
            self.appendtable( 'IPTC', iptc_info )

        if len(self.meta.keys()):
            self.appendtable( 'JPGMETA', self.meta )

        for key, value in self.meta.items():
            if key.startswith('Thumb:') or key == 'Software':
                setattr(self, key, value)
                if not key in self.keys:
                    self.keys.append(key)

    def IPTC(self):
        if not self.url.startswith('file://'):
            return None
        return IPTCInfo(self.url[6:], force=True)
    
factory.register( 'image/jpeg', ('jpg','jpeg'), mediainfo.TYPE_IMAGE, JPGInfo )
