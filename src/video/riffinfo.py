# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# riffinfo.py - riff (avi) file parser
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
import logging
import time

# kaa imports
from kaa.metadata import factory
from kaa.metadata import mediainfo

# get logging object
log = logging.getLogger('metadata')


# List of tags
# http://kibus1.narod.ru/frames_eng.htm?sof/abcavi/infotags.htm
# http://www.divx-digest.com/software/avitags_dll.html
# File Format: google for odmlff2.pdf

AVIINFO_tags = { 'title': 'INAM',
                 'artist': 'IART',
                 'product': 'IPRD',
                 'date': 'ICRD',
                 'comment': 'ICMT',
                 'language': 'ILNG',
                 'keywords': 'IKEY',
                 'trackno': 'IPRT',
                 'trackof': 'IFRM',
                 'producer': 'IPRO',
                 'writer': 'IWRI',
                 'genre': 'IGNR',
                 'copyright': 'ICOP',
                 'trackno': 'IPRT',
                 'trackof': 'IFRM',
                 'comment': 'ICMT',
               }

PIXEL_ASPECT = {  # Taken from libavcodec/mpeg4data.h (pixel_aspect struct)
    1: (1, 1),
    2: (12, 11),
    3: (10, 11),
    4: (16, 11),
    5: (40, 33)
}


class RiffInfo(mediainfo.AVInfo):
    def __init__(self,file):
        mediainfo.AVInfo.__init__(self)
        # read the header
        h = file.read(12)
        if h[:4] != "RIFF" and h[:4] != 'SDSS':
            raise mediainfo.KaaMetadataParseError()

        self.mime = 'application/x-wave'
        self.has_idx = False
        self.header = {}
        self.junkStart = None
        self.infoStart = None
        self.type = h[8:12]
        self.tag_map = { ('AVIINFO', 'en') : AVIINFO_tags }
        if self.type == 'AVI ':
            self.mime = 'video/avi'
        elif self.type == 'WAVE':
            self.mime = 'application/x-wave'
        try:
            while self.parseRIFFChunk(file):
                pass
        except IOError:
            log.exception('error in file, stop parsing')

        self.find_subtitles(file.name)

        # Copy Metadata from tables into the main set of attributes
        for k in self.tag_map.keys():
            map(lambda x:self.setitem(x,self.gettable(k[0],k[1]),
                                      self.tag_map[k][x]),
                self.tag_map[k].keys())
        if not self.has_idx:
            log.debug('WARNING: avi has no index')
            self.corrupt = 1
            self.keys.append('corrupt')


    def _extractHeaderString(self,h,offset,len):
        return h[offset:offset+len]


    def parseAVIH(self,t):
        retval = {}
        v = struct.unpack('<IIIIIIIIIIIIII',t[0:56])
        ( retval['dwMicroSecPerFrame'],
          retval['dwMaxBytesPerSec'],
          retval['dwPaddingGranularity'],
          retval['dwFlags'],
          retval['dwTotalFrames'],
          retval['dwInitialFrames'],
          retval['dwStreams'],
          retval['dwSuggestedBufferSize'],
          retval['dwWidth'],
          retval['dwHeight'],
          retval['dwScale'],
          retval['dwRate'],
          retval['dwStart'],
          retval['dwLength'] ) = v
        if retval['dwMicroSecPerFrame'] == 0:
            log.warning("ERROR: Corrupt AVI")
            raise mediainfo.KaaMetadataParseError()

        return retval


    def parseSTRH(self,t):
        retval = {}
        retval['fccType'] = t[0:4]
        log.debug("parseSTRH(%s) : %d bytes" % ( retval['fccType'], len(t)))
        if retval['fccType'] != 'auds':
            retval['fccHandler'] = t[4:8]
            v = struct.unpack('<IHHIIIIIIIII',t[8:52])
            ( retval['dwFlags'],
              retval['wPriority'],
              retval['wLanguage'],
              retval['dwInitialFrames'],
              retval['dwScale'],
              retval['dwRate'],
              retval['dwStart'],
              retval['dwLength'],
              retval['dwSuggestedBufferSize'],
              retval['dwQuality'],
              retval['dwSampleSize'],
              retval['rcFrame'], ) = v
        else:
            try:
                v = struct.unpack('<IHHIIIIIIIII',t[8:52])
                ( retval['dwFlags'],
                  retval['wPriority'],
                  retval['wLanguage'],
                  retval['dwInitialFrames'],
                  retval['dwScale'],
                  retval['dwRate'],
                  retval['dwStart'],
                  retval['dwLength'],
                  retval['dwSuggestedBufferSize'],
                  retval['dwQuality'],
                  retval['dwSampleSize'],
                  retval['rcFrame'], ) = v
                self.delay = float(retval['dwStart']) / \
                             (float(retval['dwRate']) / retval['dwScale'])
            except (KeyError, IndexError, ValueError, ZeroDivisionError):
                pass

        return retval


    def parseSTRF(self,t,strh):
        fccType = strh['fccType']
        retval = {}
        if fccType == 'auds':
            ( retval['wFormatTag'],
              retval['nChannels'],
              retval['nSamplesPerSec'],
              retval['nAvgBytesPerSec'],
              retval['nBlockAlign'],
              retval['nBitsPerSample'],
            ) = struct.unpack('<HHHHHH',t[0:12])
            ai = mediainfo.AudioInfo()
            ai.samplerate = retval['nSamplesPerSec']
            ai.channels = retval['nChannels']
            ai.samplebits = retval['nBitsPerSample']
            ai.bitrate = retval['nAvgBytesPerSec'] * 8
            # TODO: set code if possible
            # http://www.stats.uwa.edu.au/Internal/Specs/DXALL/FileSpec/\
            #    Languages
            # ai.language = strh['wLanguage']
            ai.codec = retval['wFormatTag']
            self.audio.append(ai)
        elif fccType == 'vids':
            v = struct.unpack('<IIIHH',t[0:16])
            ( retval['biSize'],
              retval['biWidth'],
              retval['biHeight'],
              retval['biPlanes'],
              retval['biBitCount'], ) = v
            v = struct.unpack('IIIII',t[20:40])
            ( retval['biSizeImage'],
              retval['biXPelsPerMeter'],
              retval['biYPelsPerMeter'],
              retval['biClrUsed'],
              retval['biClrImportant'], ) = v
            vi = mediainfo.VideoInfo()
            vi.codec = t[16:20]
            vi.width = retval['biWidth']
            vi.height = retval['biHeight']
            vi.bitrate = strh['dwRate']
            vi.fps = float(strh['dwRate']) / strh['dwScale']
            vi.length = strh['dwLength'] / vi.fps
            self.video.append(vi)
        return retval


    def parseSTRL(self,t):
        retval = {}
        size = len(t)
        i = 0
        key = t[i:i+4]
        sz = struct.unpack('<I',t[i+4:i+8])[0]
        i+=8
        value = t[i:]

        if key == 'strh':
            retval[key] = self.parseSTRH(value)
            i += sz
        else:
            log.debug("parseSTRL: Error")
        key = t[i:i+4]
        sz = struct.unpack('<I',t[i+4:i+8])[0]
        i+=8
        value = t[i:]

        if key == 'strf':
            retval[key] = self.parseSTRF(value, retval['strh'])
            i += sz
        return ( retval, i )


    def parseODML(self,t):
        retval = {}
        size = len(t)
        i = 0
        key = t[i:i+4]
        sz = struct.unpack('<I',t[i+4:i+8])[0]
        i += 8
        value = t[i:]
        if key != 'dmlh':
            log.debug("parseODML: Error")

        i += sz - 8
        return ( retval, i )


    def parseVPRP(self,t):
        retval = {}
        v = struct.unpack('<IIIIIIIIII',t[:4*10])

        ( retval['VideoFormat'],
          retval['VideoStandard'],
          retval['RefreshRate'],
          retval['HTotalIn'],
          retval['VTotalIn'],
          retval['FrameAspectRatio'],
          retval['wPixel'],
          retval['hPixel'] ) = v[1:-1]

        # I need an avi with more informations
        # enum {FORMAT_UNKNOWN, FORMAT_PAL_SQUARE, FORMAT_PAL_CCIR_601,
        #    FORMAT_NTSC_SQUARE, FORMAT_NTSC_CCIR_601,...} VIDEO_FORMAT;
        # enum {STANDARD_UNKNOWN, STANDARD_PAL, STANDARD_NTSC, STANDARD_SECAM}
        #    VIDEO_STANDARD;
        #
        r = retval['FrameAspectRatio']
        r = float(r >> 16) / (r & 0xFFFF)
        retval['FrameAspectRatio'] = r
        if self.video:
            map(lambda v: setattr(v, 'aspect', r), self.video)
        return ( retval, v[0] )


    def parseLISTmovi(self, size, file):
        """
        Digs into movi list, looking for a Video Object Layer header in an 
        mpeg4 stream in order to determine aspect ratio.
        """
        i = 0
        n_dc = 0
        done = False
        # If the VOL header doesn't appear within 5MB or 5 video chunks,
        # give up.  The 5MB limit is not likely to apply except in
        # pathological cases.
        while i < min(1024*1024*5, size - 8) and n_dc < 5:
            data = file.read(8)
            if ord(data[0]) == 0:
                # Eat leading nulls.
                data = data[1:] + file.read(1)
                i += 1

            key, sz = struct.unpack('<4sI', data)
            if key[2:] != 'dc' or sz > 1024*500:
                # This chunk is not video or is unusually big (> 500KB); 
                # skip it.
                file.seek(sz, 1)
                i += 8 + sz
                continue

            n_dc += 1
            # Read video chunk into memory
            data = file.read(sz)

            #for p in range(0,min(80, sz)):
            #    print "%02x " % ord(data[p]),
            #print "\n\n"

            # Look through the picture header for VOL startcode.  The basic
            # logic for this is taken from libavcodec, h263.c
            pos = 0
            startcode = 0xff
            def bits(v, o, n): 
                # Returns n bits in v, offset o bits.
                return (v & 2**n-1 << (64-n-o)) >> 64-n-o

            while pos < sz:
                startcode = ((startcode << 8) | ord(data[pos])) & 0xffffffff
                pos += 1
                if startcode & 0xFFFFFF00 != 0x100:
                    # No startcode found yet
                    continue

                if startcode >= 0x120 and startcode <= 0x12F:
                    # We have the VOL startcode.  Pull 64 bits of it and treat
                    # as a bitstream
                    v = struct.unpack(">Q", data[pos : pos+8])[0]
                    offset = 10
                    if bits(v, 9, 1):
                        # is_ol_id, skip over vo_ver_id and vo_priority
                        offset += 7
                    ar_info = bits(v, offset, 4)
                    if ar_info == 15:
                        # Extended aspect
                        num = bits(v, offset + 4, 8)
                        den = bits(v, offset + 12, 8)
                    else:
                        # A standard pixel aspect
                        num, den = PIXEL_ASPECT.get(ar_info, (0, 0))

                    # num/den indicates pixel aspect; convert to video aspect,
                    # so we need frame width and height.
                    if 0 not in (num, den):
                        width, height = self.video[-1].width, self.video[-1].height
                        self.video[-1].aspect = num / float(den) * width / height

                    done = True
                    break

                startcode = 0xff

            i += 8 + len(data)

            if done:
                # We have the aspect, no need to continue parsing the movi
                # list, so break out of the loop.
                break


        if i < size:
            # Seek past whatever might be remaining of the movi list.
            file.seek(size-i,1)
 


    def parseLIST(self,t):
        retval = {}
        i = 0
        size = len(t)

        while i < size-8:
            # skip zero
            if ord(t[i]) == 0: i += 1
            key = t[i:i+4]
            sz = 0

            if key == 'LIST':
                sz = struct.unpack('<I',t[i+4:i+8])[0]
                i+=8
                key = "LIST:"+t[i:i+4]
                value = self.parseLIST(t[i:i+sz])
                if key == 'strl':
                    for k in value.keys():
                        retval[k] = value[k]
                else:
                    retval[key] = value
                i+=sz
            elif key == 'avih':
                sz = struct.unpack('<I',t[i+4:i+8])[0]
                i += 8
                value = self.parseAVIH(t[i:i+sz])
                i += sz
                retval[key] = value
            elif key == 'strl':
                i += 4
                (value, sz) = self.parseSTRL(t[i:])
                key = value['strh']['fccType']
                i += sz
                retval[key] = value
            elif key == 'odml':
                i += 4
                (value, sz) = self.parseODML(t[i:])
                i += sz
            elif key == 'vprp':
                i += 4
                (value, sz) = self.parseVPRP(t[i:])
                retval[key] = value
                i += sz
            elif key == 'JUNK':
                sz = struct.unpack('<I',t[i+4:i+8])[0]
                i += sz + 8
            else:
                sz = struct.unpack('<I',t[i+4:i+8])[0]
                i+=8
                if key not in ('IDIT', 'ISFT'):
                    log.debug("Unknown Key: %s, len: %d" % (key,sz))
                value = self._extractHeaderString(t,i,sz)
                if key == 'ISFT':
                    if value.find('\0') > 0:
                        # works for Casio S500 camera videos
                        value = value[:value.find('\0')]
                    value = value.replace('\0', '').lstrip().rstrip()
                    if value:
                        self.product = value
                value = value.replace('\0', '').lstrip().rstrip()
                if value:
                    retval[key] = value
                    if key == 'IDIT':
                        # Date the video was created
                        try:
                            # The doc says it should be a format like
                            # "Wed Jan 02 02:03:55 1990"
                            date = time.strptime(value, "%a %b %d %Y %H:%M:%S")
                        except ValueError:
                            try:
                                # The Casio S500 uses "2005/12/24/ 14:11"
                                date = time.strptime(value, "%Y/%m/%d/ %H:%M")
                            except ValueError, e:
                                # FIXME: something different
                                log.debug('no support for time format %s', value)
                                date = 0
                        if date:
                            # format date to something similar to a date in an
                            # EXIF header. This creates one unique way in
                            # kaa.metadata to handle this.
                            self.date = time.strftime("%Y:%m:%d %H:%M:%S", date)
                i+=sz
        return retval


    def parseRIFFChunk(self,file):
        h = file.read(8)
        if len(h) < 4:
            return False
        name = h[:4]
        size = struct.unpack('<I',h[4:8])[0]

        if name == 'LIST':
            pos = file.tell() - 8
            key = file.read(4)
            if key == 'movi' and self.video and not self.video[-1].aspect and \
               self.video[-1].width and self.video[-1].height and \
               self.video[-1].format in ('DIVX', 'XVID', 'FMP4'): # any others?
                # If we don't have the aspect (i.e. it isn't in odml vprp
                # header), but we do know the video's dimensions, and
                # we're dealing with an mpeg4 stream, try to get the aspect 
                # from the VOL header in the mpeg4 stream.
                self.parseLISTmovi(size-4, file)
                return True
            elif size > 80000:
                log.debug('RIFF LIST "%s" to long to parse: %s bytes' % (key, size))
                t = file.seek(size-4,1)
                return True
                
            t = file.read(size-4)
            log.debug('parse RIFF LIST "%s": %d bytes' % (key, size))
            value = self.parseLIST(t)
            self.header[key] = value
            if key == 'INFO':
                self.infoStart = pos
                self.appendtable( 'AVIINFO', value )
            elif key == 'MID ':
                self.appendtable( 'AVIMID', value )
            elif key in ('hdrl', ):
                # no need to add this info to a table
                pass
            else:
                log.debug('Skipping table info %s' % key)

        elif name == 'JUNK':
            self.junkStart = file.tell() - 8
            self.junkSize  = size
            file.seek(size, 1)
        elif name == 'idx1':
            self.has_idx = True
            log.debug('idx1: %s bytes' % size)
            # no need to parse this
            t = file.seek(size,1)
        elif name == 'RIFF':
            log.debug("New RIFF chunk, extended avi [%i]" % size)
            type = file.read(4)
            if type != 'AVIX':
                log.debug("Second RIFF chunk is %s, not AVIX, skipping", type)
                file.seek(size-4, 1)
            # that's it, no new informations should be in AVIX
            return False
        elif not name.strip(string.printable + string.whitespace):
            # check if name is something usefull at all, maybe it is no
            # avi or broken
            t = file.seek(size,1)
            log.debug("Skipping %s [%i]" % (name,size))
        else:
            # bad avi
            log.debug("Bad or broken avi")
            return False
        return True

    def buildTag(self,key,value):
        text = value + '\0'
        l = len(text)
        return struct.pack('<4sI%ds'%l, key[:4], l, text[:l])


    def setInfo(self,file,hash):
        if self.junkStart == None:
            raise "junkstart missing"
        tags = []
        size = 4 # Length of 'INFO'
        # Build String List and compute req. size
        for key in hash.keys():
            tag = self.buildTag( key, hash[key] )
            if (len(tag))%2 == 1: tag += '\0'
            tags.append(tag)
            size += len(tag)
            log.debug("Tag [%i]: %s" % (len(tag),tag))
        if self.infoStart != None:
            log.debug("Infostart found. %i" % (self.infoStart))
            # Read current info size
            file.seek(self.infoStart,0)
            s = file.read(12)
            (list, oldsize, info) = struct.unpack('<4sI4s',s)
            self.junkSize += oldsize + 8
        else:
            self.infoStart = self.junkStart
            log.debug("Infostart computed. %i" % (self.infoStart))
        file.seek(self.infoStart,0)
        if ( size > self.junkSize - 8 ):
            raise "Too large"
        file.write( "LIST" + struct.pack('<I',size) + "INFO" )
        for tag in tags:
            file.write( tag )
        log.debug("Junksize %i" % (self.junkSize-size-8))
        file.write( "JUNK" + struct.pack('<I',self.junkSize-size-8) )



factory.register( 'video/avi', ('avi',), mediainfo.TYPE_AV, RiffInfo )
