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
import os
import logging

# kaa.metadata imports
import kaa.metadata.video.core as video
import kaa.metadata.audio.core as audio

# kaa.metadata.disc imports
import core
import _ifoparser

# get logging object
log = logging.getLogger('metadata')

_video_height = (480, 576, 0, 576)
_video_width  = (720, 704, 352, 352)
_video_fps    = (0, 25.00, 0, 29.97)
_video_format = ('NTSC', 'PAL')
_video_aspect = (4.0 / 3, 16.0 / 9, 1.0, 16.0 / 9)

class DVDVideo(video.VideoStream):
    def __init__(self, data):
        video.VideoStream.__init__(self)
        self.length = data[0]
        self.fps    = _video_fps[data[1]]
        self.format = _video_format[data[2]]
        self.aspect = _video_aspect[data[3]]
        self.width  = _video_width[data[4]]
        self.height = _video_height[data[5]]
        self.codec  = 'MP2V'


class DVDAudio(audio.Audio):

    _keys = audio.Audio._keys + [ 'id' ]

    def __init__(self, pos, info):
        audio.Audio.__init__(self)
        self.id = 128 + pos
        self.language, self.codec, self.channels, self.samplerate = info
        if self.codec == '0x2001':      # DTS
            # dts uses the same counter as ac3 but is always +8
            self.id += 8


class DVDTitle(video.AVContainer):

    _keys = video.AVContainer._keys + [ 'angles' ]

    def __init__(self, info):
        video.AVContainer.__init__(self)
        self.chapters = []
        pos = 0
        for length in info[0]:
            chapter = video.Chapter()
            chapter.pos = pos
            pos += length
            self.chapters.append(chapter)

        self.angles = info[1]

        self.mime = 'video/mpeg'
        self.video.append(DVDVideo(info[2:8]))
        self.length = self.video[0].length

        for pos, a in enumerate(info[-2]):
            self.audio.append(DVDAudio(pos, a))

        for pos, s in enumerate(info[-1]):
            self.subtitles.append(video.Subtitle(s))


class DVDInfo(core.Disc):

    _keys = core.Disc._keys + [ 'length' ]

    def __init__(self, device):
        core.Disc.__init__(self)
        self.offset = 0

        if isinstance(device, file):
            self.parseDVDiso(device)
        elif os.path.isdir(device):
            self.parseDVDdir(device)
        else:
            self.parseDisc(device)

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
        info = _ifoparser.parse(device)
        if not info:
            raise core.ParseError()
        for pos, title in enumerate(info):
            ti = DVDTitle(title)
            ti.trackno = pos + 1
            ti.trackof = len(info)
            self.tracks.append(ti)


    def parseDVDdir(self, dirname):
        if not (os.path.isdir(dirname+'/VIDEO_TS') or \
                os.path.isdir(dirname+'/video_ts') or \
                os.path.isdir(dirname+'/Video_ts')):
            raise core.ParseError()
        # OK, try libdvdread
        self._parse(dirname)
        return 1


    def parseDisc(self, device):
        if self.is_disc(self, device) != 2:
            raise core.ParseError()

        # brute force reading of the device to find out if it is a DVD
        f = open(device,'rb')
        f.seek(32768, 0)
        buffer = f.read(60000)

        if buffer.find('UDF') == -1:
            f.close()
            raise core.ParseError()

        # seems to be a DVD, read a little bit more
        buffer += f.read(550000)
        f.close()

        if buffer.find('VIDEO_TS') == -1 and \
               buffer.find('VIDEO_TS.IFO') == -1 and \
               buffer.find('OSTA UDF Compliant') == -1:
            raise core.ParseError()

        # OK, try libdvdread
        self._parse(device)


    def parseDVDiso(self, f):
        # brute force reading of the device to find out if it is a DVD
        f.seek(32768, 0)
        buffer = f.read(60000)

        if buffer.find('UDF') == -1:
            raise core.ParseError()

        # seems to be a DVD, read a little bit more
        buffer += f.read(550000)

        if buffer.find('VIDEO_TS') == -1 and \
               buffer.find('VIDEO_TS.IFO') == -1 and \
               buffer.find('OSTA UDF Compliant') == -1:
            raise core.ParseError()

        # OK, try libdvdread
        self._parse(f.name)


core.register( 'video/dvd', core.EXTENSION_DEVICE, DVDInfo )
core.register('video/dvd', core.EXTENSION_DIRECTORY, DVDInfo)
core.register('video/dvd', ['iso'], DVDInfo)
