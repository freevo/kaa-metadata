# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# dvdinfo.py - parse dvd title structure
# -----------------------------------------------------------------------------
# $Id$
#
# TODO: update the ifomodule and remove the lsdvd parser
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

# python imports
import os
import logging

# kaa imports
import ifoparser
from kaa.metadata import mediainfo
from kaa.metadata import factory
from discinfo import DiscInfo

# get logging object
log = logging.getLogger('metadata')

_video_height = (480, 576, 0, 576)
_video_width  = (720, 704, 352, 352)
_video_fps    = (0, 25.00, 0, 29.97);
_video_format = ('NTSC', 'PAL')
_video_aspect = ("4/3", "16/9", None, "16/9");

class DVDVideo(mediainfo.VideoInfo):
    def __init__(self, data):
        mediainfo.VideoInfo.__init__(self)
        self.length = data[0]
        self.fps    = _video_fps[data[1]]
        self.format = _video_format[data[2]]
        self.aspect = _video_aspect[data[3]]
        self.width  = _video_width[data[4]]
        self.height = _video_height[data[5]]

class DVDAudio(mediainfo.AudioInfo):
    def __init__(self, pos, info):
        mediainfo.AudioInfo.__init__(self)
        self.id = 128 + pos
        self.language, self.codec, self.channels, self.samplerate = info


class DVDTitle(mediainfo.AVInfo):
    def __init__(self, info):
        mediainfo.AVInfo.__init__(self)
        self.chapters = info[0]
        self.angles = info[1]
        self.keys.append('chapters')
        self.keys.append('subtitles')
        self.keys.append('angles')

        self.mime = 'video/mpeg'
        self.video.append(DVDVideo(info[2:8]))
        self.length = self.video[0].length

        for pos, a in enumerate(info[-2]):
            self.audio.append(DVDAudio(pos, a))

        for pos, s in enumerate(info[-1]):
            self.subtitles.append(s)


class DVDInfo(DiscInfo):
    def __init__(self, device):
        DiscInfo.__init__(self)
        self.context = 'video'
        self.offset = 0

        if isinstance(device, file):
            self.parseDVDiso(device)
        elif os.path.isdir(device):
            self.parseDVDdir(device)
        else:
            self.parseDisc(device)

        self.keys.append('length')
        self.length = 0
        first       = 0

        for t in self.tracks:
            self.length += t.length
            if not first:
                first = t.length

        if self.length/len(self.tracks) == first:
            # badly mastered dvd
            self.length = first

        self.mime    = 'video/dvd'
        self.type    = 'DVD'
        self.subtype = 'video'


    def _parse(self, device):
        info = ifoparser.parse(device)
        if not info:
            raise mediainfo.KaaMetadataParseError()
        for pos, title in enumerate(info):
            ti = DVDTitle(title)
            ti.trackno = pos + 1
            ti.trackof = len(info)
            self.appendtrack(ti)


    def parseDVDdir(self, dirname):
        if not (os.path.isdir(dirname+'/VIDEO_TS') or \
                os.path.isdir(dirname+'/video_ts') or \
                os.path.isdir(dirname+'/Video_ts')):
            raise mediainfo.KaaMetadataParseError()
        # OK, try libdvdread
        self._parse(dirname)
        return 1


    def parseDisc(self, device):
        if DiscInfo.isDisc(self, device) != 2:
            raise mediainfo.KaaMetadataParseError()

        # brute force reading of the device to find out if it is a DVD
        f = open(device,'rb')
        f.seek(32768, 0)
        buffer = f.read(60000)

        if buffer.find('UDF') == -1:
            f.close()
            raise mediainfo.KaaMetadataParseError()

        # seems to be a DVD, read a little bit more
        buffer += f.read(550000)
        f.close()

        if buffer.find('VIDEO_TS') == -1 and \
               buffer.find('VIDEO_TS.IFO') == -1 and \
               buffer.find('OSTA UDF Compliant') == -1:
            raise mediainfo.KaaMetadataParseError()

        # OK, try libdvdread
        self._parse(device)


    def parseDVDiso(self, f):
        # brute force reading of the device to find out if it is a DVD
        f.seek(32768, 0)
        buffer = f.read(60000)

        if buffer.find('UDF') == -1:
            raise mediainfo.KaaMetadataParseError()

        # seems to be a DVD, read a little bit more
        buffer += f.read(550000)

        if buffer.find('VIDEO_TS') == -1 and \
               buffer.find('VIDEO_TS.IFO') == -1 and \
               buffer.find('OSTA UDF Compliant') == -1:
            raise mediainfo.KaaMetadataParseError()

        # OK, try libdvdread
        self._parse(f.name)


factory.register( 'video/dvd', mediainfo.EXTENSION_DEVICE,
                  mediainfo.TYPE_AV, DVDInfo )

factory.register('video/dvd', mediainfo.EXTENSION_DIRECTORY,
                 mediainfo.TYPE_AV, DVDInfo)

factory.register('video/dvd', ['iso'], mediainfo.TYPE_AV, DVDInfo)
