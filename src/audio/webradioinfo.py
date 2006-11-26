# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# webradioinfo.py - read webradio attributes
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
import urlparse
import string
import urllib

# kaa imports
from kaa.metadata import mediainfo
from kaa.metadata import factory

# http://205.188.209.193:80/stream/1006

ICY_tags = { 'title': 'icy-name',
             'genre': 'icy-genre',
             'bitrate': 'icy-br',
             'caption': 'icy-url',
           }

class WebRadioInfo(mediainfo.MusicInfo):
    def __init__(self, url):
        mediainfo.MusicInfo.__init__(self)
        tup = urlparse.urlsplit(url)
        scheme, location, path, query, fragment = tup
        if scheme != 'http':
            raise mediainfo.KaaMetadataParseError()

        # Open an URL Connection
        fi = urllib.urlopen(url)

        # grab the statusline
        self.statusline = fi.readline()
        try:
            statuslist = string.split(self.statusline)
        except ValueError:
            # assume it is okay since so many servers are badly configured
            statuslist = ["ICY", "200"]

        if statuslist[1] != "200":
            if fi:
                fi.close()
            raise mediainfo.KaaMetadataParseError()

        self.type = 'audio'
        self.subtype = 'mp3'
        # grab any headers for a max of 10 lines
        linecnt = 0
        tab = {}
        lines = fi.readlines(512)
        for linecnt in range(0,11):
            icyline = lines[linecnt]
            icyline = icyline.rstrip('\r\n')
            if len(icyline) < 4:
                break
            cidx = icyline.find(':')
            if cidx != -1:
                # break on short line (ie. really should be a blank line)
                # strip leading and trailing whitespace
                tab[icyline[:cidx].strip()] = icyline[cidx+2:].strip()
        if fi:
            fi.close()
        self.appendtable('ICY', tab)
        self.tag_map = { ('ICY', 'en') : ICY_tags }
        # Copy Metadata from tables into the main set of attributes
        for k in self.tag_map.keys():
            map(lambda x:self.setitem(x,self.gettable(k[0],k[1]),
                                      self.tag_map[k][x]),
                self.tag_map[k].keys())
        self.bitrate = string.atoi(self.bitrate)*1000


factory.register( 'text/plain', mediainfo.EXTENSION_STREAM,
                  mediainfo.TYPE_MUSIC, WebRadioInfo )
