# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# lsdvdinfo.py - parse dvd title structure using lsdvd
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
import popen2
import logging
import re

# kaa imports
from kaa.metadata import mediainfo
from kaa.metadata import factory
from discinfo import DiscInfo

# get logging object
log = logging.getLogger('metadata')

LSDVD_EXE='lsdvd'

class DVDAudio(mediainfo.AudioInfo):
    def __init__(self, data):
        mediainfo.AudioInfo.__init__(self)
        self.number   = int(data[1])
        if data[3] != 'xx':
            self.language = data[3]
            try:
                # some DVDs have a very bad language setting
                self.language.encode()
            except UnicodeError:
                self.language = ''

        try:
            self.codec = data[7]
            try:
                self.samplerate = int(data[9])
            except ValueError, e:
                if data[9].lower().find('khz') > 0:
                    pos = data[9].lower().find('khz')
                    self.samplerate = int(data[9][:pos]) * 1000
                else:
                    raise e
            self.channels = data[13]
        except Exception, e:
            # WTF, strange DVD, now try to find the bug (may not work)
            self.codec = data[data.index('Format:') + 1]
            try:
                freq = data[data.index('Frequency:') + 1]
                self.samplerate = int(freq)
            except ValueError:
                if freq.lower().find('khz') > 0:
                    self.samplerate = int(freq[:freq.lower().find('khz')])*1000
            self.channels = int(data[data.index('Channels:') + 1])


class DVDVideo(mediainfo.VideoInfo):
    def __init__(self, data):
        mediainfo.VideoInfo.__init__(self)
        self.width  = int(data[12])
        self.height = int(data[14])
        self.fps    = float(data[5])
        self.aspect = data[10]


class DVDTitle(mediainfo.AVInfo):
    def __init__(self, data):
        mediainfo.AVInfo.__init__(self)
        self.number = int(data[1])

        self.keys.append('subtitles')
        self.keys.append('chapters')

        self.mime = 'video/mpeg'

        l = re.split('[:.]', data[3])
        self.length   = (int(l[0])*60+int(l[1]))*60+int(l[2])
        self.trackno  = int(data[1])
        self.chapters = int(data[5])


class DVDInfo(DiscInfo):
    def __init__(self, device):
        DiscInfo.__init__(self)
        self.context = 'video'
        self.offset = 0

        log.info('trying lsdvd for scanning the disc')

        if os.path.isdir(device):
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

        log.info('lsdvd detection ok')

        self.mime    = 'video/dvd'
        self.type    = 'DVD'
        self.subtype = 'video'


    def lsdvd(self, path):
        """
        use lsdvd to get informations about this disc
        """
        child = popen2.Popen3('%s -v -n -a -s "%s"' % \
                              (LSDVD_EXE, path), 1, 100)
        for line in child.fromchild.readlines():
            data = line.replace(',', '').replace('\t', '').\
                   replace('\n', '').lstrip(' ').split(' ')
            if len(data) > 2:
                if data[0] == 'Title:':
                    ti = DVDTitle(data)
                    self.appendtrack(ti)
                elif data[0] == 'Audio:':
                    self.tracks[-1].audio.append(DVDAudio(data))
                elif data[0] == 'Subtitle:':
                    self.tracks[-1].subtitles.append(data[3])
                elif data[0] == 'VTS:':
                    self.tracks[-1].video.append(DVDVideo(data))
                    self.tracks[-1].video[-1].length = self.tracks[-1].length
                elif data[:3] == ['Number', 'of', 'Angles:']:
                    self.tracks[-1].angles = int(data[3])
                    self.tracks[-1].keys.append('angles')

        child.wait()
        child.fromchild.close()
        child.childerr.close()
        child.tochild.close()

        if len(self.tracks) == 0:
            raise mediainfo.KaaMetadataParseError()

        for ti in self.tracks:
            ti.trackof = len(self.tracks)


    def parseDVDdir(self, dirname):
        if os.path.isdir(dirname+'/VIDEO_TS') or \
               os.path.isdir(dirname+'/video_ts') or \
               os.path.isdir(dirname+'/Video_ts'):
            self.lsdvd(dirname)
            return
        raise mediainfo.KaaMetadataParseError()


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

        try:
            self.lsdvd(device)
        except mediainfo.KaaMetadataParseError:
            # we are very sure this is a DVD, maybe the drive was not
            # ready, let's try again
            self.lsdvd(device)


if os.environ.has_key('LSDVD') and os.environ['LSDVD']:
    LSDVD_EXE = os.environ['LSDVD']
else:
    for path in os.environ['PATH'].split(':'):
        if os.path.isfile(os.path.join(path, 'lsdvd')):
            LSDVD_EXE = os.path.join(path, 'lsdvd')
            break
    else:
        log.info('ImportError: lsdvd not found')
        raise ImportError

factory.register( 'video/dvd', mediainfo.EXTENSION_DEVICE,
                       mediainfo.TYPE_AV, DVDInfo )
factory.register( 'video/dvd', mediainfo.EXTENSION_DIRECTORY,
                       mediainfo.TYPE_AV, DVDInfo )
