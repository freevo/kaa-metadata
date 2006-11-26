# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# snesinfo.py - Gameboy Advance ROM parsing
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2006 Thomas Schueppel, Dirk Meyer
#
# First Edition: Richard Mottershead <richard.mottershead@v21net.co.uk>
# Maintainer:    Richard Mottershead <richard.mottershead@v21net.co.uk>
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
import struct
import logging
import sys

# kaa imports
from kaa.metadata import mediainfo
from kaa.metadata import factory

from struct import *
from re import *

# get logging object
log = logging.getLogger('metadata')

# interesting file format info:
# http://www.classicgaming.com/epr/super/sneskart.html#embededcartridge

# Used to detect the internal rome information, as described in
# 'SNESKART.DOC v1.3'
snesromFileOffset = [33216, 32704, 65472, 65984]

#most of the code is imported from the old snesitem.py.

class SNESInfo(mediainfo.MediaInfo):

    def __init__(self,file):
        mediainfo.MediaInfo.__init__(self)

        romName= 'unknown'
        romHL = 0
        romMEM = 0
        romROM = 0
        romSRAM = 0
        romCountry = chr(255)
        romCountryTxt = 'unknown'
        romLic = chr(51)
        romLicTxt = 'unknown'
        romVer = 0
        romICHK = 0
        romCHK = 0
        romParsed = 0
        description = 'unknown'

        self.mime = 'games/snes'
        self.type = 'SuperNintendo game'

        for offset in snesromFileOffset:
            log.debug('Checking for rom header at offset: %d' % offset)
            file.seek(offset)
            romHeader = file.read(32)
            try:
                (romName,romHL,romMem,romROM,romSRAM,romCountry,romLic,romVer,romICHK,romCHK) = unpack('21scccccccHH', romHeader)
            except (KeyboardInterrupt, SystemExit):
                sys.exit(0)
            except:
                raise mediainfo.KaaMetadataParseError()
            log.debug('ROM NAME: %s' % romName)
            # Break now if CHECKSUM is OK
            if (romICHK | romCHK) == 0xFFFF:
                log.debug('SNES rom header detected at offset : %d!!!!' % offset)
                break
            else:
                for offset in snesromFileOffset:
                    log.debug('Checking for rom header at offset: %d' % offset)
                    file.seek(offset)
                    romHeader = file.read(32)
                try:
                    (romName,romHL,romMem,romROM,romSRAM,romCountry,romLic,romVer,romICHK,romCHK) = unpack('21scccccccHH', romHeader)
                except (KeyboardInterrupt, SystemExit):
                    sys.exit(0)
                except:
                    raise mediainfo.KaaMetadataParseError()

                # Some times, the ROM is OK, but the checksum is incorrect, so we do a very dummy ASCII detection
                if match('[a-zA-Z0-9 ]{4}', romName[0:4]) != None:
                    log.debug('SNES rom header detected by ASCII name : %d!!!!' % offset)
                    break
                else:
                    raise mediainfo.KaaMetadataParseError()
        self.title = romName


factory.register( 'games/snes', ('smc', 'sfc', 'fig', ),
                  mediainfo.TYPE_MISC, SNESInfo )
