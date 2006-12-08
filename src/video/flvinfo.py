# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# flvinfo.py - parser for flash video files
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

# python imports
import struct
import string
import logging

# kaa imports
from kaa.metadata import mediainfo
from kaa.metadata import factory

# get logging object
log = logging.getLogger('metadata')

FLV_TAG_TYPE_AUDIO = 0x08
FLV_TAG_TYPE_VIDEO = 0x09
FLV_TAG_TYPE_META  = 0x12

# audio flags
FLV_AUDIO_CHANNEL_MASK = 0x01
FLV_AUDIO_SAMPLERATE_MASK = 0x0c
FLV_AUDIO_CODECID_MASK = 0xf0

FLV_AUDIO_SAMPLERATE_OFFSET = 2
FLV_AUDIO_CODECID_OFFSET = 4
FLV_AUDIO_CODECID = ( 0x0001, 0x0002, 0x0055, 0x0001 )

# video flags
FLV_VIDEO_CODECID_MASK = 0x0f
FLV_VIDEO_CODECID = ( 'FLV1', 'MSS1', 'VP60') # wild guess


class FlashInfo(mediainfo.AVInfo):
    def __init__(self,file):
        mediainfo.AVInfo.__init__(self)
        self.mime = 'video/flv'
        self.type = 'Flash Video'
        header = struct.unpack('>3sBBII', file.read(13))
        if not header[0] == 'FLV':
            raise mediainfo.KaaMetadataParseError()

        for i in range(10):
            if self.audio and self.video:
                break
            data = file.read(11)
            if len(data) < 11:
                break
            chunk = struct.unpack('>BH4BI', data)
            size = (chunk[1] << 8) + chunk[2]

            if chunk[0] == FLV_TAG_TYPE_AUDIO:
                flags = ord(file.read(1))
                if not self.audio:
                    a = mediainfo.AudioInfo()
                    a.channels = (flags & FLV_AUDIO_CHANNEL_MASK) + 1
                    srate = (flags & FLV_AUDIO_SAMPLERATE_MASK)
                    a.samplerate = (44100 << (srate >> FLV_AUDIO_SAMPLERATE_OFFSET) >> 3)
                    codec = (flags & FLV_AUDIO_CODECID_MASK) >> FLV_AUDIO_CODECID_OFFSET
                    if codec < len(FLV_AUDIO_CODECID):
                        a.codec = FLV_AUDIO_CODECID[codec]
                    self.audio.append(a)

                file.seek(size - 1, 1)

            elif chunk[0] == FLV_TAG_TYPE_VIDEO:
                flags = ord(file.read(1))
                if not self.video:
                    v = mediainfo.VideoInfo()
                    codec = (flags & FLV_VIDEO_CODECID_MASK) - 2
                    if codec < len(FLV_VIDEO_CODECID):
                        v.codec = FLV_VIDEO_CODECID[codec]
                    # width and height are in the meta packet, but I have
                    # no file with such a packet inside. So maybe we have
                    # to decode some parts of the video.
                    self.video.append(v)

                file.seek(size - 1, 1)

            elif chunk[0] == FLV_TAG_TYPE_META:
                log.info('metadata %s', str(chunk))
                file.seek(size, 1)

            else:
                log.info('unkown %s', str(chunk))
                file.seek(size, 1)

            file.seek(4, 1)

factory.register( 'video/flv', ('flv',), FlashInfo )
