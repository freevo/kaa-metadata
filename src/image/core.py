# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# core.py - basic image class
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

# python imports
import os
import sys
import gzip
import logging

# kaa imports
from kaa import xml

# kaa.metadata imports
from kaa.metadata.factory import register
from kaa.metadata import mediainfo

ParseError = mediainfo.ParseError

# get logging object
log = logging.getLogger('metadata')

# attributes for image files
ATTRIBUTES = ['description', 'people', 'location', 'event', 'width', 'height',
              'thumbnail','software','hardware', 'dpi', 'city', 'rotation' ]


class Image(mediainfo.Media):
    """
    Digital Images, Photos, Pictures.
    """

    _keys = mediainfo.Media._keys + ATTRIBUTES
    media = mediainfo.MEDIA_IMAGE
    
    def _finalize(self):
        """
        Add additional information and correct data.
        FIXME: parse_external_files here is very wrong
        """
        if self.url and self.url.startswith('file://'):
            self.parse_external_files(self.url[7:])
        mediainfo.Media._finalize(self)


    def parse_external_files(self, filename):
        """
        Parse external files like bins and .comments.
        """
        for func in (self.parse_bins, self.parse_dot_comment):
            try:
                func(filename)
            except (KeyboardInterrupt, SystemExit):
                sys.exit(0)
            except:
                pass


    def parse_bins(self, filename):
        """
        Parse bins xml files
        """
        binsxml = filename + '.xml'
        if not os.path.isfile(binsxml):
            return
        doc = xml.Document(binsxml, 'image')
        for child in doc.get_child('description').children:
            key = str(child.getattr('name'))
            if not key or not child.content:
                continue
            self._set(key, child.content)


    def parse_dot_comment(self, filename):
        """
        Parse info in .comments.
        """
        comment_file = os.path.join(os.path.dirname(filename), '.comments',
                                    os.path.basename(filename) + '.xml')
        if not os.path.isfile(comment_file):
            return
        doc = xml.Document(comment_file, 'Comment')
        for child in doc.children:
            if child.name == 'Place':
                self.location = child.content
            if child.name == 'Note':
                self.description = child.content
