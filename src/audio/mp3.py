# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# mp3.py - mp3 file parser
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2006 Thomas Schueppel, Dirk Meyer
#
# First Edition: Thomas Schueppel <stain@acm.org>
# Maintainer:    Dirk Meyer <https://github.com/Dischi>
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

# python imports
import re
import sys
import os
import logging
import struct

# import kaa.metadata.audio core
from ..utils import tostr
from . import core
from . import ID3 as ID3

# stagger imports
sys.path.insert(0, os.path.dirname(__file__))
from . import stagger


# get logging object
log = logging.getLogger('metadata')

# http://www.omniscia.org/~vivake/python/MP3Info.py
# This maps ID3 frames to core attributes.
MP3_INFO_TABLE = { "LINK": "link",
                   "TALB": "album",
                   "TCOM": "composer",
                   "TCOP": "copyright",
                   "TDOR": "release",
                   "TYER": "userdate",
                   "TEXT": "text",
                   "TIT2": "title",
                   "TLAN": "language",
                   "TLEN": "length",
                   "TMED": "media_type",
                   "TPE1": "artist",
                   "TPE2": "artist",
                   "TRCK": "trackno",
                   "TPOS": "discs",
                   "TPUB": "publisher"}

# This maps ID3 frames to tag names (as per the Matroska Tags specification)
# to support the new core Tags API.  tag name -> attr, filter
ID3_TAGS_MAP = {
    'COMM': ('comment', tostr),
    'TALB': ('album', tostr),
    'TYER': ('date_recorded', None),
    'TDRC': ('date_recorded', None),
    'TDRL': ('date_released', None),
    'TDEN': ('date_encoded', None),
    'TENC': ('encoded_by', tostr),
    'TMOO': ('mood', tostr),
    'WXXX': ('url', tostr),
    'TIT2': ('title', tostr),
    'TOPE': ('artist', tostr),
    'TCOM': ('composer', tostr),
    'TEXT': ('lyricist', tostr),
    'TPE1': ('lead_performer', tostr),
    'TPE2': ('accompaniment', tostr),
    'TPE3': ('conductor', tostr),
    'TRCK': ('part_number', int),
    'TPOS': ('total_parts', int),
    'TCOP': ('copyright', tostr),
    'TPUB': ('publisher', tostr),
    # Treated specially
    #'TCON': (u'genre', tostr),
}

_bitrates = [
   [ # MPEG-2 & 2.5
   [0,32,48,56, 64, 80, 96,112,128,144,160,176,192,224,256,None], # Layer 1
   [0, 8,16,24, 32, 40, 48, 56, 64, 80, 96,112,128,144,160,None], # Layer 2
   [0, 8,16,24, 32, 40, 48, 56, 64, 80, 96,112,128,144,160,None]  # Layer 3
   ],

   [ # MPEG-1
   [0,32,64,96,128,160,192,224,256,288,320,352,384,416,448,None], # Layer 1
   [0,32,48,56, 64, 80, 96,112,128,160,192,224,256,320,384,None], # Layer 2
   [0,32,40,48, 56, 64, 80, 96,112,128,160,192,224,256,320,None]  # Layer 3
   ]
   ]

_samplerates = [
   [ 11025, 12000,  8000, None], # MPEG-2.5
   [  None,  None,  None, None], # reserved
   [ 22050, 24000, 16000, None], # MPEG-2
   [ 44100, 48000, 32000, None], # MPEG-1
   ]

_modes = [ "stereo", "joint stereo", "dual channel", "mono" ]

_MP3_HEADER_SEEK_LIMIT = 4096

class MP3(core.Music):

    fileName       = str()
    fileSize       = int()

    def __init__(self, file):
        core.Music.__init__(self)
        self.fileName = file.name
        self.codec = 0x0055 # fourcc code of mp3
        self.mime = 'audio/mpeg'

        id3 = None
        try:
            id3 = stagger.read_tag(file.name)
        except stagger.NoTagError:
            # File is not an MP3
            raise core.ParseError()
        #except eyeD3_tag.TagException:
        except stagger.TagError:
            # The MP3 tag decoder crashed, assume the file is still
            # MP3 and try to play it anyway
            if log.level < 30:
                log.exception('mp3 tag parsing %s failed!' % file.name)
            log.exception('mp3 tag parsing %s failed!' % file.name)
        except Exception:
            # The MP3 tag decoder crashed, assume the file is still
            # MP3 and try to play it anyway
            if log.level < 30:
                log.exception('mp3 tag parsing %s failed!' % file.name)

        if not id3:
            # let's take a look at the header
            s = file.read(4096)
            if not s[:3] == b'ID3':
                # no id3 tag header, not good
                if not re.compile(rb'0*\xFF\xFB\xB0\x04$').search(s):
                    # again, not good
                    if not re.compile(rb'0*\xFF\xFA\xB0\x04$').search(s):
                        # that's it, it is no mp3 at all
                        raise core.ParseError()

        try:
            if id3:
                self.tags = core.Tags()
                log.debug(id3.frames())
                # Grip unicode bug workaround: Grip stores text data as UTF-8
                # and flags it as latin-1.  This workaround tries to decode
                # these strings as utf-8 instead.
                # http://sourceforge.net/tracker/index.php?func=detail&aid=1196919&group_id=3714&atid=103714
                if 'COMM' in id3:
                    for frame in id3.frames('COMM'):
                        if "created by grip" not in frame.text.lower():
                            continue
                        for frame in id3.frames():
                            if hasattr(frame, "text") and isinstance(frame.text, str):
                                try:
                                    frame.text = [t.encode('latin-1').decode('utf-8') for t in frame.text]
                                except UnicodeError:
                                    pass
                        break

                for k, var in list(MP3_INFO_TABLE.items()):
                    if k in id3:
                        self._set(var,''.join(id3.frames(k)[0].text))
                if 'APIC' in id3:
                    pic = id3.frames('APIC')[0]
                    if pic.data:
                        self.thumbnail = pic.data
                if id3.date:
                    self.userdate = id3.date
                tab = {}
                for f in id3.frames():
                    tag = core.Tag()
                    if isinstance(f, stagger.Frame) and hasattr(f, 'text'):
                        text = ''.join(f.text)
                        tab[f.frameid] = text
                        tag.value = text
                    elif isinstance(f, stagger.URLFrame):
                        tab[f.frameid] = f.url
                        tag.value = f.url
                    elif isinstance(f, stagger.PictureFrame):
                        tab[f.frameid] = f
                        if f.data:
                            tag.binary = True
                            tag.value = f.data
                    elif getattr(f, 'frameid', None) == 'TXXX':
                        tab[f.description] = f.value
                        tag.value = f.value
                        self.tags['_' + f.description.replace(' ', '_')] = tag
                        continue
                    else:
                        log.debug(f.__class__)

                    if f.frameid in ID3_TAGS_MAP and tag.value:
                        tagname, filter = ID3_TAGS_MAP[f.frameid]
                        try:
                            if filter:
                                tag.value = filter(tag.value)
                        except Exception as e:
                            log.warning('skipping tag %s: %s', tagname, e)
                        else:
                            self.tags[tagname] = tag
                self._appendtable('id3v2', tab)

                if id3.frames('TCON'):
                    genre = None
                    tcon = ''.join(id3.frames('TCON')[0].text)
                    # TODO: could handle id3v2 genre refinements.
                    try:
                        # Assume integer.
                        genre = int(tcon)
                    except ValueError:
                        # Nope, maybe it's in '(N)' format.
                        try:
                            genre = int(tcon[1:tcon.find(')')])
                        except ValueError:
                            # Nope.  Treat as a string.
                            self.genre = tostr(tcon)

                    if genre is not None:
                        try:
                            self.genre = ID3.GENRE_LIST[genre]
                        except KeyError:
                            # Numeric genre specified but not one of the known genres,
                            # use 'Unknown' as per ID3v1.
                            self.genre = 'Unknown'

                    self.tags['genre'] = core.Tag(self.genre)

                # and some tools store it as trackno/trackof in TRCK
                if not self.trackof and self.trackno and \
                       self.trackno.find('/') > 0:
                    self.trackof = self.trackno[self.trackno.find('/')+1:]
                    self.trackno = self.trackno[:self.trackno.find('/')]
           #if id3:
           #     self.length = id3.getPlayTime()
        except Exception:
            if log.level < 30:
                log.exception('parse error')

        offset, header = self._find_header(file)
        if offset == -1 or header is None:
            return

        self._parse_header(header)

        #if id3:
        #    # Note: information about variable bitrate or not should
        #    # be handled somehow.
        #    (vbr, self.bitrate) = id3.getBitRate()

    def _find_header(self, file):
        file.seek(0, 0)
        amount_read = 0

        # see if we get lucky with the first four bytes
        amt = 4

        while amount_read < _MP3_HEADER_SEEK_LIMIT:
            header = file.read(amt)
            if len(header) < amt:
                # awfully short file. just give up.
                return -1, None

            amount_read = amount_read + len(header)

            # on the next read, grab a lot more
            amt = 500

            # look for the sync byte
            offset = header.find(bytes([255]))
            if offset == -1:
                continue

            # looks good, make sure we have the next 3 bytes after this
            # because the header is 4 bytes including sync
            if offset + 4 > len(header):
                more = file.read(4)
                if len(more) < 4:
                    # end of file. can't find a header
                    return -1, None
                amount_read = amount_read + 4
                header = header + more

            # the sync flag is also in the next byte, the first 3 bits
            # must also be set
            if header[offset+1] >> 5 != 7:
                continue

            # ok, that's it, looks like we have the header
            return amount_read - len(header) + offset, header[offset:offset+4]

        # couldn't find the header
        return -1, None


    def _parse_header(self, header):
        # http://mpgedit.org/mpgedit/mpeg_format/MP3Format.html
        bytes = struct.unpack('>i', header)[0]
        mpeg_version =    (bytes >> 19) & 3
        layer =           (bytes >> 17) & 3
        bitrate =         (bytes >> 12) & 15
        samplerate =      (bytes >> 10) & 3
        mode =            (bytes >> 6)  & 3

        if mpeg_version == 0:
            self.version = 2.5
        elif mpeg_version == 2:
            self.version = 2
        elif mpeg_version == 3:
            self.version = 1
        else:
            return

        if layer > 0:
            layer = 4 - layer
        else:
            return

        self.bitrate = _bitrates[mpeg_version & 1][layer - 1][bitrate]
        self.samplerate = _samplerates[mpeg_version][samplerate]

        if self.bitrate is None or self.samplerate is None:
            return

        self._set('mode', _modes[mode])


Parser = MP3
