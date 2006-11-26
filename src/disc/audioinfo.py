# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# audioinfo.py - support for audio cds
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
import cdrom
import logging

# kaa imports
import kaa.metadata
from kaa.metadata import mediainfo
from kaa.metadata import factory

# disc imports
import discinfo
import DiscID
import CDDB

# get logging object
log = logging.getLogger('metadata')

class AudioDiscInfo(discinfo.DiscInfo):
    def __init__(self,device):
        discinfo.DiscInfo.__init__(self)
        self.context = 'audio'
        self.offset = 0
        # check disc
        if discinfo.DiscInfo.isDisc(self, device) != 1:
            raise mediainfo.KaaMetadataParseError()

        self.query(device)
        self.mime = 'audio/cd'
        self.type = 'CD'
        self.subtype = 'audio'


    def query(self, device):

        cdromfd = DiscID.open(device)
        disc_id = DiscID.disc_id(cdromfd)

        if kaa.metadata.USE_NETWORK:
            try:
                (query_stat, query_info) = CDDB.query(disc_id)
            except Exception, e:
                # Oops no connection
                query_stat = 404
        else:
            query_stat = 404

        if query_stat == 210 or query_stat == 211:
            # set this to success
            query_stat = 200

            for i in query_info:
                if i['title'] != i['title'].upper():
                    query_info = i
                    break
            else:
                query_info = query_info[0]

        elif query_stat != 200:
            log.error("failure getting disc info, status %i" % query_stat)

        if query_stat == 200:
            qi = query_info['title'].split('/')
            self.artist = qi[0].strip()
            self.title = qi[1].strip()
            for type in ('title', 'artist'):
                if getattr(self, type) and \
                       getattr(self, type)[0] in ('"', '\'') \
                       and getattr(self, type)[-1] in ('"', '\''):
                    setattr(self, type, getattr(self, type)[1:-1])
            (read_stat, read_info) = CDDB.read(query_info['category'],
                                               query_info['disc_id'])
            # id = disc_id + number of tracks
            #self.id = '%s_%s' % (query_info['disc_id'], disc_id[1])

            if read_stat == 210:
                for i in range(0, disc_id[1]):
                    mi = mediainfo.MusicInfo()
                    mi.title = read_info['TTITLE' + `i`]
                    mi.album = self.title
                    mi.artist = self.artist
                    mi.genre = query_info['category']
                    mi.codec = 'PCM'
                    mi.samplerate = 44.1
                    mi.trackno = i+1
                    mi.trackof = disc_id[1]
                    self.tracks.append(mi)
                    for type in ('title', 'album', 'artist', 'genre'):
                        if getattr(mi, type) and \
                               getattr(mi, type)[0] in ('"', '\'') \
                           and getattr(mi, type)[-1] in ('"', '\''):
                            setattr(mi, type, getattr(mi, type)[1:-1])
            else:
                log.error("failure getting track info, status: %i" % read_stat)
                # set query_stat to somthing != 200
                query_stat = 400


        if query_stat != 200:
            log.error("failure getting disc info, status %i" % query_stat)
            self.no_caching = 1
            for i in range(0, disc_id[1]):
                mi = mediainfo.MusicInfo()
                mi.title = 'Track %s' % (i+1)
                mi.codec = 'PCM'
                mi.samplerate = 44.1
                mi.trackno = i+1
                mi.trackof = disc_id[1]
                self.tracks.append(mi)


        # read the tracks to generate the title list
        (first, last) = cdrom.toc_header(cdromfd)

        lmin = 0
        lsec = 0

        num = 0
        for i in range(first, last + 2):
            if i == last + 1:
                min, sec, frames = cdrom.leadout(cdromfd)
            else:
                min, sec, frames = cdrom.toc_entry(cdromfd, i)
            if num:
                self.tracks[num-1].length = (min-lmin)*60 + (sec-lsec)
            num += 1
            lmin, lsec = min, sec

        # correct bad titles for the tracks, containing also the artist
        for t in self.tracks:
            if not self.artist or not t.title.startswith(self.artist):
                break
        else:
            for t in self.tracks:
                t.title = t.title[len(self.artist):].lstrip('/ \t-_')

        # correct bad titles for the tracks, containing also the title
        for t in self.tracks:
            if not self.title or not t.title.startswith(self.title):
                break
        else:
            for t in self.tracks:
                t.title = t.title[len(self.title):].lstrip('/ \t-_')

        cdromfd.close()


factory.register( 'audio/cd', mediainfo.EXTENSION_DEVICE,
                  mediainfo.TYPE_AUDIO, AudioDiscInfo )
