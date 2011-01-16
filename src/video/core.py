# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# core.py - basic video class
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2006 Thomas Schueppel, Dirk Meyer
#
# First Edition: Thomas Schueppel <stain@acm.org>
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

import re

from kaa.metadata.core import ParseError, Media, MEDIA_VIDEO, MEDIA_SUBTITLE, \
     MEDIA_CHAPTER, MEDIA_AV, MEDIA_AUDIO, MEDIA_DISC, Collection, Tag, Tags, \
     feature_enabled, feature_config, register_feature

from kaa.metadata.audio.core import Audio as AudioStream


VIDEOCORE = ['length', 'encoder', 'bitrate', 'samplerate', 'codec', 'format',
             'samplebits', 'width', 'height', 'fps', 'aspect', 'trackno',
             'fourcc', 'id', 'enabled', 'default', 'codec_private' ]

AVCORE    = ['length', 'encoder', 'trackno', 'trackof', 'copyright', 'product',
             'genre', 'writer', 'producer', 'studio', 'rating', 'actors', 'thumbnail',
             'delay', 'image', 'video', 'audio', 'subtitles', 'chapters', 'software',
             'summary', 'synopsis', 'season', 'episode', 'show' ]

# Guess if a file is a recording of a TV show. It matches names in the
# style of 'show 1x01 episode' and show s1e01 episode' where the
# delimiter may not be a space but also point or minus.
register_feature('VIDEO_SHOW_PARSER',
    '.*/([^/]+)[ \._]+s?([0-9]|[0-9][0-9])[xe]([0-9]|[0-9][0-9])[ \-\._]+([^/]*)\.[^/\.]+$')

class VideoStream(Media):
    """
    Video Tracks in a Multiplexed Container.
    """
    _keys = Media._keys + VIDEOCORE
    media = MEDIA_VIDEO


class Chapter(Media):
    """
    Chapter in a Multiplexed Container.
    """
    _keys = ['enabled', 'name', 'pos', 'id']
    media = MEDIA_CHAPTER

    def __init__(self, name=None, pos=0):
        Media.__init__(self)
        self.name = name
        self.pos = pos
        self.enabled = True


class Subtitle(Media):
    """
    Subtitle Tracks in a Multiplexed Container.
    """
    _keys = ['enabled', 'default', 'langcode', 'language', 'trackno', 'title',
             'id', 'codec']
    media = MEDIA_SUBTITLE

    def __init__(self, language=None):
        Media.__init__(self)
        self.language = language


class AVContainer(Media):
    """
    Container for Audio and Video streams. This is the Container Type for
    all media, that contain more than one stream.
    """
    _keys = Media._keys + AVCORE
    media = MEDIA_AV

    def __init__(self):
        Media.__init__(self)
        self.audio = []
        self.video = []
        self.subtitles = []
        self.chapters  = []


    def _set_url(self, url):
        """
        Set the URL of the source
        """
        Media._set_url(self, url)
        if feature_enabled('VIDEO_SHOW_PARSER') and not self.show:
            # special tv show handling to detect the series and episode
            # name and number
            match = re.split(feature_config('VIDEO_SHOW_PARSER'), url)
            if match and len(match) == 6:
                self.show, self.season, self.episode, self.title = match[1:-1]

    def _finalize(self):
        """
        Correct same data based on specific rules
        """
        Media._finalize(self)
        if not self.length and len(self.video) and self.video[0].length:
            self.length = 0
            # Length not specified for container, so use the largest length
            # of its tracks as container length.
            for track in self.video + self.audio:
                if track.length:
                    self.length = max(self.length, track.length)
