# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# vcdinfo.py - parse vcd track informations from cue/bin files
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2006 Thomas Schueppel, Dirk Meyer
#
# First Edition: Dirk Meyer <dmeyer@tzi.de>
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
import os

# kaa imports
from kaa.metadata import mediainfo
from kaa.metadata import factory

class VCDInfo(mediainfo.CollectionInfo):
    def __init__(self, file):
        mediainfo.CollectionInfo.__init__(self)
        self.context = 'video'
        self.offset = 0
        self.mime = 'video/vcd'
        self.type = 'vcd video'
        self.parseVCD(file)


    def parseVCD(self, file):
        type = None

        buffer = file.readline(300)

        if not buffer[:6] == 'FILE "':
            raise mediainfo.KaaMetadataParseError()

        bin = os.path.join(os.path.dirname(file.name),
                           buffer[6:buffer[6:].find('"')+6])
        if not os.path.isfile(bin):
            raise mediainfo.KaaMetadataParseError()

        # At this point this really is a cue/bin disc

        # brute force reading of the bin to find out if it is a VCD
        f = open(bin,'rb')
        f.seek(32768, 0)
        buffer = f.read(60000)
        f.close()

        if buffer.find('SVCD') > 0 and buffer.find('TRACKS.SVD') > 0 and \
               buffer.find('ENTRIES.SVD') > 0:
            type = 'SVCD'

        elif buffer.find('INFO.VCD') > 0 and buffer.find('ENTRIES.VCD') > 0:
            type = 'VCD'

        else:
            raise mediainfo.KaaMetadataParseError()

        counter = 0
        while 1:
            buffer = file.readline()
            if not len(buffer):
                return
            if buffer[:8] == '  TRACK ':
                counter += 1
                # the first track is the directory, that doesn't count
                if counter > 1:
                    vi = mediainfo.VideoInfo()
                    if type == 'VCD':
                        vi.codec = 'MPEG1'
                    else:
                        vi.codec = 'MPEG2'
                    self.tracks.append(vi)


factory.register( 'video/vcd', ('cue',), mediainfo.TYPE_AV, VCDInfo )
