# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# generic.py - Generic Image Parser based on Exiv2
# -----------------------------------------------------------------------------
# $Id$
#
# Note: this parser supports all image types supported by exiv2. An
# application based on kaa.metadata (or kaa.beacon) MUST check if it
# supports the given mime type. E.g. exiv2 supports camera raw files
# while an aplication like Freevo does not.
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python Copyright (C) 2009 Thomas
# Schueppel, Dirk Meyer
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

__all__ = ['Parser']

# import kaa.metadata.image core
import core
import exiv2

# TODO: improve the mapping
# use 'mminfo -d 2 filename' to get a list of detected attributes
mapping = {
    # generic mapping
    'Image.Width': 'width',
    'Image.Height': 'height',
    'Image.Mimetype': 'mime',
    'Image.Thumbnail': 'thumbnail',
    'Image.Keywords': 'keywords',
    # exif mapping
    'Exif.Image.Model': 'hardware',
    'Exif.Image.Software': 'software',
    'Exif.Canon.OwnerName': 'artist',
    # iptc mapping
    'Iptc.Application2.Byline': 'artist'
}

class Generic(core.Image):

    table_mapping = { 'exiv2': mapping }

    def __init__(self, file):
        core.Image.__init__(self)
        self.type = 'image'
        # The exiv2 parser just dumps everything it sees in a dict.
        # The mapping from above is used to convert the exiv2 keys to
        # kaa.metadata keys.
        self._appendtable('exiv2', exiv2.parse(file.name))

Parser = Generic
