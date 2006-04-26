# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# riffinfo.py - riff (avi) file parser
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
import fourcc
import logging

# kaa imports
from kaa.metadata import factory
from kaa.metadata import mediainfo

# get logging object
log = logging.getLogger('metadata')


# List of tags
# http://kibus1.narod.ru/frames_eng.htm?sof/abcavi/infotags.htm
# http://www.divx-digest.com/software/avitags_dll.html
# File Format
# http://www.taenam.co.kr/pds/documents/odmlff2.pdf

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
            try:
                ai.codec = fourcc.RIFFWAVE[retval['wFormatTag']]
            except (KeyError, IndexError):
                ai.codec = "Unknown"
            ai.format = retval['wFormatTag']
            self.audio.append(ai)
        elif fccType == 'vids':
            v = struct.unpack('<IIIHH',t[0:16])
            ( retval['biSize'],
              retval['biWidth'],
              retval['biHeight'],
              retval['biPlanes'],
              retval['biBitCount'], ) = v
            retval['fourcc'] = t[16:20]
            v = struct.unpack('IIIII',t[20:40])
            ( retval['biSizeImage'],
              retval['biXPelsPerMeter'],
              retval['biYPelsPerMeter'],
              retval['biClrUsed'],
              retval['biClrImportant'], ) = v
            vi = mediainfo.VideoInfo()
            try:
                vi.codec = fourcc.RIFFCODEC[t[16:20]]
            except (KeyError, IndexError):
                vi.codec = "Unknown"
            vi.width = retval['biWidth']
            vi.height = retval['biHeight']
            vi.bitrate = strh['dwRate']
            vi.fps = round(float(strh['dwRate'] * 100) / strh['dwScale']) / 100
            vi.length = strh['dwLength'] / vi.fps
            vi.format = retval['fourcc']
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
        if key == 'dmlh':
            pass
        else:
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
                log.debug("Unknown Key: %s, len: %d" % (key,sz))
                i+=8
                value = self._extractHeaderString(t,i,sz)
                value = value.replace('\0', '').lstrip().rstrip()
                if value:
                    retval[key] = value
                i+=sz
        return retval


    def parseRIFFChunk(self,file):
        h = file.read(8)
        if len(h) < 4:
            return False
        name = h[:4]
        size = struct.unpack('<I',h[4:8])[0]

        if name == 'LIST' and size < 80000:
            pos = file.tell() - 8
            t = file.read(size)
            key = t[:4]
            log.debug('parse RIFF LIST: %d bytes' % (size))
            value = self.parseLIST(t[4:])
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
        elif name == 'LIST':
            log.debug('RIFF LIST to long to parse: %s bytes' % size)
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
