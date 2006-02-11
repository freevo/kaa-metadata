# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# core.py - basic image parsing using Imaging
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2005 Thomas Schueppel, Dirk Meyer
#
# First Edition: Thomas Schueppel <stain@acm.org>
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
import gzip
import logging
import libxml2

# kaa imports
from kaa.metadata import factory
from kaa.metadata import mediainfo

# get logging object
log = logging.getLogger('metadata')

# attributes for image files
ATTRIBUTES = ['description', 'people', 'location', 'event', 'width', 'height',
              'thumbnail','software','hardware', 'dpi']


class ImageInfo(mediainfo.MediaInfo):
    """
    Digital Images, Photos, Pictures.
    """
    def __init__(self):
        mediainfo.MediaInfo.__init__(self)
        for k in ATTRIBUTES:
            setattr(self,k,None)
            self.keys.append(k)

    def correct_data(self):
        """
        Add additional information and correct data.
        FIXME: parse_external_files here is very wrong
        """
        if self.url and self.url.startswith('file://'):
            self.parse_external_files(self.url[7:])
        mediainfo.MediaInfo.correct_data(self)


    def parse_external_files(self, filename):
        """
        Parse external files like bins and .comments.
        """
        self.parse_bins(filename)
        self.parse_dot_comment(filename)
        
    def parse_bins(self, filename):
        """
        Parse bins xml files
        """
        binsxml = filename + '.xml'
        if not os.path.isfile(binsxml):
            return
        for node in libxml2.parseFile(binsxml).children:
            if not node.name == 'description':
                continue
            for child in node.children:
                if not child.name == 'field':
                    continue
                value = unicode(child.getContent(), 'utf-8').strip()
                key = child.prop('name')
                if key and value:
                    self[key] = value
                    if not key in ATTRIBUTES + mediainfo.MEDIACORE:
                        # if it's in desc it must be important
                        self.keys.append(key)


    def parse_dot_comment(self, filename):
        """
        Parse info in .comments.
        """
        comment_file = os.path.join(os.path.dirname(filename), '.comments',
                                    os.path.basename(filename) + '.xml')
        if not os.path.isfile(comment_file):
            return
        for node in libxml2.parseFile(comment_file).children:
            if not node.name == 'Comment':
                continue
            for child in node.children:
                value = unicode(child.getContent(), 'utf-8')
                if not value or value == '0':
                    continue
                if child.name == 'Place':
                    self.location = value
                if child.name == 'Note':
                    self.description = value
