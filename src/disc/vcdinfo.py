# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# vcdinfo.py - parse vcd track informations
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2005 Thomas Schueppel, Dirk Meyer
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

# kaa imports
from kaa.metadata import factory
from kaa.metadata import mediainfo
from discinfo import DiscInfo
import cdrom

class VCDInfo(DiscInfo):
    def __init__(self,device):
        DiscInfo.__init__(self)
        self.context = 'video'
        self.offset = 0
        self.mime = 'video/vcd'
        self.type = 'CD'
        self.subtype = 'video'
        # parse disc
        self.parseDisc(device)


    def parseDisc(self, device):
        type = None
        if DiscInfo.isDisc(self, device) != 2:
            raise mediainfo.KaaMetadataParseError()

        # brute force reading of the device to find out if it is a VCD
        f = open(device,'rb')
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

        # read the tracks to generate the title list
        device = open(device)
        (first, last) = cdrom.toc_header(device)

        lmin = 0
        lsec = 0

        num = 0
        for i in range(first, last + 2):
            if i == last + 1:
                min, sec, frames = cdrom.leadout(device)
            else:
                min, sec, frames = cdrom.toc_entry(device, i)
            if num:
                vi = mediainfo.VideoInfo()
                # XXX add more static information here, it's also possible
                # XXX to scan for more informations like fps
                # XXX Settings to MPEG1/2 is a wild guess, maybe the track
                # XXX isn't playable at all (e.g. the menu)
                if type == 'VCD':
                    vi.codec = 'MPEG1'
                else:
                    vi.codec = 'MPEG2'
                vi.length = (min-lmin) * 60 + (sec-lsec)
                self.tracks.append(vi)
            num += 1
            lmin, lsec = min, sec
        device.close()


factory.register( 'video/vcd', mediainfo.EXTENSION_DEVICE,
                  mediainfo.TYPE_AV, VCDInfo )
