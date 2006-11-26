# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# ogginfo.py - ogg file parser
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2006 Thomas Schueppel, Dirk Meyer
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
import re
import os
import stat
import struct
import logging

# kaa imports
from kaa.metadata import mediainfo
from kaa.metadata import factory

# get logging object
log = logging.getLogger('metadata')

VORBIS_PACKET_INFO = '\01vorbis'
VORBIS_PACKET_HEADER = '\03vorbis'
VORBIS_PACKET_SETUP = '\05vorbis'

class OggInfo(mediainfo.MusicInfo):
    def __init__(self,file):
        mediainfo.MusicInfo.__init__(self)
        h = file.read(4+1+1+20+1)
        if h[:5] != "OggS\00":
            log.info("Invalid header")
            raise mediainfo.KaaMetadataParseError()
        if ord(h[5]) != 2:
            log.info("Invalid header type flag (trying to go ahead anyway)")
        self.pageSegCount = ord(h[-1])
        # Skip the PageSegCount
        file.seek(self.pageSegCount,1)
        h = file.read(7)
        if h != VORBIS_PACKET_INFO:
            log.info("Wrong vorbis header type, giving up.")
            raise mediainfo.KaaMetadataParseError()

        self.mime = 'application/ogg'
        header = {}
        info = file.read(23)
        self.version, self.channels, self.samplerate, bitrate_max, \
                      self.bitrate, bitrate_min, blocksize, \
                      framing = struct.unpack('<IBIiiiBB',info[:23])
        # INFO Header, read Oggs and skip 10 bytes
        h = file.read(4+10+13)
        if h[:4] == 'OggS':
            (serial, pagesequence, checksum, numEntries) = \
                     struct.unpack( '<14xIIIB', h )
            # skip past numEntries
            file.seek(numEntries,1)
            h = file.read(7)
            if h != VORBIS_PACKET_HEADER:
                # Not a corrent info header
                return
            self.encoder = self._extractHeaderString(file)
            numItems = struct.unpack('<I',file.read(4))[0]
            for i in range(numItems):
                s = self._extractHeaderString(file)
                a = re.split('=',s)
                header[(a[0]).upper()]=a[1]
            # Put Header fields into info fields
            if header.has_key('TITLE'):
                self.title = header['TITLE']
            if header.has_key('ALBUM'):
                self.album = header['ALBUM']
            if header.has_key('ARTIST'):
                self.artist = header['ARTIST']
            if header.has_key('COMMENT'):
                self.comment = header['COMMENT']
            if header.has_key('DATE'):
                self.date = header['DATE']
            if header.has_key('ENCODER'):
                self.encoder = header['ENCODER']
            if header.has_key('TRACKNUMBER'):
                self.trackno = header['TRACKNUMBER']
            self.type = 'OGG Vorbis'
            self.subtype = ''
            self.length = self._calculateTrackLength(file)
            self.appendtable('VORBISCOMMENT',header)


    def _extractHeaderString(self,f):
        len = struct.unpack( '<I', f.read(4) )[0]
        return unicode(f.read(len), 'utf-8')


    def _calculateTrackLength(self,f):
        # seek to the end of the stream, to avoid scanning the whole file
        if (os.stat(f.name)[stat.ST_SIZE] > 20000):
            f.seek(os.stat(f.name)[stat.ST_SIZE]-10000)

        # read the rest of the file into a buffer
        h = f.read()
        granule_position = 0
        # search for each 'OggS' in h
        if len(h):
            idx = h.rfind('OggS')
            if idx < 0:
                return 0
            pageSize = 0
            h = h[idx+4:]
            (check, type, granule_position, absPos, serial, pageN, crc, \
             segs) = struct.unpack( '<BBIIIIIB', h[:23] )
            if check != 0:
                log.debug(h[:10])
                return
            log.debug("granule = %d / %d" % (granule_position, absPos))
        # the last one is the one we are interested in
        return (granule_position / self.samplerate)


factory.register( 'application/ogg', ('ogg',), mediainfo.TYPE_MUSIC, OggInfo)
