# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# movinfo.py - mov file parser
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
import re
import struct
import string
import time
import zlib
import logging
import StringIO
from struct import unpack

# kaa imports
from kaa.metadata import factory
from kaa.metadata import mediainfo
from movlanguages import *

# get logging object
log = logging.getLogger('metadata')


# http://developer.apple.com/documentation/QuickTime/QTFF/index.html
# http://developer.apple.com/documentation/QuickTime/QTFF/QTFFChap4/\
#     chapter_5_section_2.html#//apple_ref/doc/uid/TP40000939-CH206-BBCBIICE
# Note: May need to define custom log level to work like ATOM_DEBUG did here

QTUDTA = {
    'nam': 'title',
    'aut': 'artist',
    'cpy': 'copyright'
}

class MovInfo(mediainfo.AVInfo):

    table_mapping = { 'QTUDTA': QTUDTA }

    def __init__(self,file):
        mediainfo.AVInfo.__init__(self)
        self._references = []

        self.mime = 'video/quicktime'
        self.type = 'Quicktime Video'
        h = file.read(8)
        (size,type) = unpack('>I4s',h)

        if type == 'ftyp':
            # file type information
            if size >= 12:
                # this should always happen
                if file.read(4) != 'qt  ':
                    # not a quicktime movie, it is a mpeg4 container
                    self.mime = 'video/mp4'
                    self.type = 'MPEG-4 Video'
                size -= 4
            file.seek(size-8, 1)
            h = file.read(8)
            (size,type) = unpack('>I4s',h)

        while type == 'mdat':
            # movie data at the beginning, skip
            file.seek(size-8, 1)
            h = file.read(8)
            (size,type) = unpack('>I4s',h)

        if not type in ('moov', 'wide', 'free'):
            log.debug('invalid header: %s' % type)
            raise mediainfo.KaaMetadataParseError()

        # Extended size
        if size == 1:
            size = unpack('>Q', file.read(8))
        while self._readatom(file):
            pass

        if self._references:
            self._set('references', self._references)


    def _readatom(self, file):
        s = file.read(8)
        if len(s) < 8:
            return 0

        atomsize,atomtype = unpack('>I4s', s)
        if not str(atomtype).decode('latin1').isalnum():
            # stop at nonsense data
            return 0

        log.debug('%s [%X]' % (atomtype,atomsize))

        if atomtype == 'udta':
            # Userdata (Metadata)
            pos = 0
            tabl = {}
            i18ntabl = {}
            atomdata = file.read(atomsize-8)
            while pos < atomsize-12:
                (datasize, datatype) = unpack('>I4s', atomdata[pos:pos+8])
                if ord(datatype[0]) == 169:
                    # i18n Metadata...
                    mypos = 8+pos
                    while mypos < datasize+pos:
                        # first 4 Bytes are i18n header
                        (tlen, lang) = unpack('>HH', atomdata[mypos:mypos+4])
                        i18ntabl[lang] = i18ntabl.get(lang, {})
                        l = atomdata[mypos+4:mypos+tlen+4]
                        i18ntabl[lang][datatype[1:]] = l
                        mypos += tlen+4
                elif datatype == 'WLOC':
                    # Drop Window Location
                    pass
                else:
                    if ord(atomdata[pos+8:pos+datasize][0]) > 1:
                        tabl[datatype] = atomdata[pos+8:pos+datasize]
                pos += datasize
            if len(i18ntabl.keys()) > 0:
                for k in i18ntabl.keys():
                    if QTLANGUAGES.has_key(k) and QTLANGUAGES[k] == 'en':
                        self._appendtable('QTUDTA', i18ntabl[k])
                        self._appendtable('QTUDTA', tabl)
            else:
                log.debug('NO i18')
                self._appendtable('QTUDTA', tabl)

        elif atomtype == 'trak':
            atomdata = file.read(atomsize-8)
            pos = 0
            trackinfo = {}
            tracktype = None
            while pos < atomsize-8:
                (datasize, datatype) = unpack('>I4s', atomdata[pos:pos+8])

                if datatype == 'tkhd':
                    tkhd = unpack('>6I8x4H36xII', atomdata[pos+8:pos+datasize])
                    trackinfo['width'] = tkhd[10] >> 16
                    trackinfo['height'] = tkhd[11] >> 16
                    trackinfo['id'] = tkhd[3]
                    
                    try:
                        # XXX Date number of Seconds is since January 1st 1904!
                        # XXX 2082844800 is the difference between Unix and
                        # XXX Apple time. Fix me to work on Apple, too
                        self.date = int(tkhd[1]) - 2082844800
                        self.date = time.strftime('%y/%m/%d',
                                                  time.gmtime(self.date))
                    except Exception, e:
                        log.exception('There was trouble extracting the date')

                elif datatype == 'mdia':
                    pos      += 8
                    datasize -= 8
                    log.debug('--> mdia information')

                    while datasize:
                        mdia = unpack('>I4s', atomdata[pos:pos+8])
                        if mdia[1] == 'mdhd':
                            mdhd = unpack('>IIIIIhh', atomdata[pos+8:pos+8+24])
                            # duration / time scale
                            trackinfo['length'] = mdhd[4] / mdhd[3]
                            if mdhd[5] in QTLANGUAGES:
                                trackinfo['language'] = QTLANGUAGES[mdhd[5]]
                            # mdhd[6] == quality
                            self.length = max(self.length, mdhd[4] / mdhd[3])
                        elif mdia[1] == 'minf':
                            # minf has only atoms inside
                            pos -=      (mdia[0] - 8)
                            datasize += (mdia[0] - 8)
                        elif mdia[1] == 'stbl':
                            # stbl has only atoms inside
                            pos -=      (mdia[0] - 8)
                            datasize += (mdia[0] - 8)
                        elif mdia[1] == 'hdlr':
                            hdlr = unpack('>I4s4s', atomdata[pos+8:pos+8+12])
                            if hdlr[1] == 'mhlr':
                                if hdlr[2] == 'vide':
                                    tracktype = 'video'
                                if hdlr[2] == 'soun':
                                    tracktype = 'audio'
                        elif mdia[1] == 'stsd':
                            stsd = unpack('>2I', atomdata[pos+8:pos+8+8])
                            if stsd[1] > 0:
                                codec = atomdata[pos+16:pos+16+8]
                                codec = unpack('>I4s', codec)
                                trackinfo['codec'] = codec[1]
                                if codec[1] == 'jpeg':
                                    tracktype = 'image'
                        elif mdia[1] == 'dinf':
                            dref = unpack('>I4s', atomdata[pos+8:pos+8+8])
                            log.debug('  --> %s, %s (useless)' % mdia)
                            if dref[1] == 'dref':
                                num = unpack('>I', atomdata[pos+20:pos+20+4])[0]
                                rpos = pos+20+4
                                for ref in range(num):
                                    # FIXME: do somthing if this references
                                    ref = unpack('>I3s', atomdata[rpos:rpos+7])
                                    data = atomdata[rpos+7:rpos+ref[0]]
                                    rpos += ref[0]
                        else:
                            if mdia[1].startswith('st'):
                                log.debug('  --> %s, %s (sample)' % mdia)
                            elif mdia[1] in ('vmhd',) and not tracktype:
                                # indicates that this track is video
                                tracktype = 'video'
                            elif mdia[1] in ('vmhd', 'smhd') and not tracktype:
                                # indicates that this track is audio
                                tracktype = 'audio'
                            else:
                                log.debug('  --> %s, %s (unknown)' % mdia)

                        pos      += mdia[0]
                        datasize -= mdia[0]

                elif datatype == 'udta':
                    log.debug(unpack('>I4s', atomdata[:8]))
                else:
                    if datatype == 'edts':
                        log.debug('--> %s [%d] (edit list)' % \
                                  (datatype, datasize))
                    else:
                        log.debug('--> %s [%d] (unknown)' % \
                                  (datatype, datasize))
                pos += datasize

            info = None
            if tracktype == 'video':
                info = mediainfo.VideoInfo()
                self.video.append(info)
            if tracktype == 'audio':
                info = mediainfo.AudioInfo()
                self.audio.append(info)
            if info:
                for key, value in trackinfo.items():
                    setattr(info, key, value)

        elif atomtype == 'mvhd':
            # movie header
            mvhd = unpack('>6I2h', file.read(28))
            self.length = max(self.length, mvhd[4] / mvhd[3])
            self.volume = mvhd[6]
            file.seek(atomsize-8-28,1)


        elif atomtype == 'cmov':
            # compressed movie
            datasize, atomtype = unpack('>I4s', file.read(8))
            if not atomtype == 'dcom':
                return atomsize

            method = unpack('>4s', file.read(datasize-8))[0]

            datasize, atomtype = unpack('>I4s', file.read(8))
            if not atomtype == 'cmvd':
                return atomsize

            if method == 'zlib':
                data = file.read(datasize-8)
                try:
                    decompressed = zlib.decompress(data)
                except Exception, e:
                    try:
                        decompressed = zlib.decompress(data[4:])
                    except Exception, e:
                        log.exception('There was a proble decompressiong atom')
                        return atomsize

                decompressedIO = StringIO.StringIO(decompressed)
                while self._readatom(decompressedIO):
                    pass

            else:
                log.info('unknown compression %s' % method)
                # unknown compression method
                file.seek(datasize-8,1)

        elif atomtype == 'moov':
            # decompressed movie info
            while self._readatom(file):
                pass

        elif atomtype == 'mdat':
            pos = file.tell() + atomsize - 8
            # maybe there is data inside the mdat
            log.info('parsing mdat')
            while self._readatom(file):
                pass
            log.info('end of mdat')
            file.seek(pos, 0)


        elif atomtype == 'rmra':
            # reference list
            while self._readatom(file):
                pass

        elif atomtype == 'rmda':
            # reference
            atomdata = file.read(atomsize-8)
            pos   = 0
            url = ''
            quality = 0
            datarate = 0
            while pos < atomsize-8:
                (datasize, datatype) = unpack('>I4s', atomdata[pos:pos+8])
                if datatype == 'rdrf':
                    rflags, rtype, rlen = unpack('>I4sI', atomdata[pos+8:pos+20])
                    if rtype == 'url ':
                        url = atomdata[pos+20:pos+20+rlen]
                        if url.find('\0') > 0:
                            url = url[:url.find('\0')]
                elif datatype == 'rmqu':
                    quality = unpack('>I', atomdata[pos+8:pos+12])[0]

                elif datatype == 'rmdr':
                    datarate = unpack('>I', atomdata[pos+12:pos+16])[0]

                pos += datasize
            if url:
                self._references.append((url, quality, datarate))

        else:
            if not atomtype in ('wide', 'free'):
                log.info('unhandled base atom %s' % atomtype)

            # Skip unknown atoms
            try:
                file.seek(atomsize-8,1)
            except IOError:
                return 0

        return atomsize


exts = ('mov', 'qt', 'mp4', 'mp4a', '3gp', '3gp2', 'mk2')
factory.register( 'video/quicktime', exts, MovInfo)
