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
import os
import logging

# kaa imports
import ifoparser
from kaa.metadata import mediainfo
from kaa.metadata import factory
from discinfo import DiscInfo

# get logging object
log = logging.getLogger('metadata')

class DVDAudio(mediainfo.AudioInfo):
    def __init__(self, title, number):
        mediainfo.AudioInfo.__init__(self)
        self.number = number
        self.title  = title
        self.id, self.language, self.codec, self.channels, self.samplerate = \
                 ifoparser.audio(title, number)


class DVDTitle(mediainfo.AVInfo):
    def __init__(self, number):
        mediainfo.AVInfo.__init__(self)
        self.number = number
        self.chapters, self.angles, self.length, audio_num, \
                       subtitles_num = ifoparser.title(number)

        self.keys.append('chapters')
        self.keys.append('subtitles')

        self.mime = 'video/mpeg'
        for a in range(1, audio_num+1):
            self.audio.append(DVDAudio(number, a))

        for s in range(1, subtitles_num+1):
            self.subtitles.append(ifoparser.subtitle(number, s)[0])


class DVDInfo(DiscInfo):
    def __init__(self, device):
        DiscInfo.__init__(self)
        self.context = 'video'
        self.offset = 0

        log.info('trying buggy dvd detection')

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


    def parseDVDdir(self, dirname):
        if not (os.path.isdir(dirname+'/VIDEO_TS') or \
                os.path.isdir(dirname+'/video_ts') or \
                os.path.isdir(dirname+'/Video_ts')):
            raise mediainfo.KaaMetadataParseError()

        # OK, try libdvdread
        title_num = ifoparser.open(dirname)
        if not title_num:
            raise mediainfo.KaaMetadataParseError()

        for title in range(1, title_num+1):
            ti = DVDTitle(title)
            ti.trackno = title
            ti.trackof = title_num
            self.appendtrack(ti)

        ifoparser.close()
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
        title_num = ifoparser.open(device)

        if not title_num:
            raise mediainfo.KaaMetadataParseError()

        for title in range(1, title_num+1):
            ti = DVDTitle(title)
            ti.trackno = title
            ti.trackof = title_num
            self.appendtrack(ti)

        ifoparser.close()


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
        title_num = ifoparser.open(f.name)

        if not title_num:
            raise mediainfo.KaaMetadataParseError()

        for title in range(1, title_num+1):
            ti = DVDTitle(title)
            ti.trackno = title
            ti.trackof = title_num
            self.appendtrack(ti)

        ifoparser.close()


if not factory.gettype('video/dvd', mediainfo.EXTENSION_DEVICE):
    factory.register( 'video/dvd', mediainfo.EXTENSION_DEVICE,
                      mediainfo.TYPE_AV, DVDInfo )

if not factory.gettype('video/dvd', mediainfo.EXTENSION_DIRECTORY):
    factory.register('video/dvd', mediainfo.EXTENSION_DIRECTORY,
                     mediainfo.TYPE_AV, DVDInfo)

factory.register('video/dvd', ['iso'], mediainfo.TYPE_AV, DVDInfo)
