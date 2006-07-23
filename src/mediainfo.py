# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# mediainfo.py
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
import os
import logging
import copy
import sys

# kaa imports
from kaa.strutils import str_to_unicode, unicode_to_str

# kaa metadata imports
import table

UNPRINTABLE_KEYS = [ 'thumbnail']

# type definitions
TYPE_NONE      = 0
TYPE_AUDIO     = 1
TYPE_VIDEO     = 2
TYPE_IMAGE     = 4
TYPE_AV        = 5
TYPE_MUSIC     = 6
TYPE_HYPERTEXT = 8
TYPE_MISC      = 10

MEDIACORE = ['title', 'caption', 'comment', 'artist', 'size', 'type', 'cover',
             'subtype', 'date', 'keywords', 'country', 'language', 'url']

AUDIOCORE = ['channels', 'samplerate', 'length', 'encoder', 'codec', 'format',
             'samplebits', 'bitrate', 'language' ]

VIDEOCORE = ['length', 'encoder', 'bitrate', 'samplerate', 'codec', 'format',
             'samplebits', 'width', 'height', 'fps', 'aspect', 'trackno']

MUSICCORE = ['trackno', 'trackof', 'album', 'genre','discs', 'image',
             'thumbnail']

AVCORE    = ['length', 'encoder', 'trackno', 'trackof', 'copyright', 'product',
             'genre', 'secondary genre', 'subject', 'writer', 'producer',
             'cinematographer', 'production designer', 'edited by',
             'costume designer', 'music by', 'studio', 'distributed by',
             'rating', 'starring', 'ripped by', 'digitizing date',
             'internet address', 'source form', 'medium', 'source',
             'archival location', 'commisioned by', 'engineer', 'cropped',
             'sharpness', 'dimensions', 'lightness', 'dots per inch',
             'palette setting', 'default audio stream', 'logo url',
             'watermark url', 'info url', 'banner image', 'banner url',
             'infotext', 'delay', 'image']


EXTENSION_DEVICE    = 'device'
EXTENSION_DIRECTORY = 'directory'
EXTENSION_STREAM    = 'stream'

# get logging object
log = logging.getLogger('metadata')


class KaaMetadataParseError:
    pass

class MediaInfo:
    """
    MediaInfo is the base class to all Media Metadata Containers. It defines
    the basic structures that handle metadata. MediaInfo and its derivates
    contain a common set of metadata attributes that is listed in keys.
    Specific derivates contain additional keys to the dublin core set that is
    defined in MediaInfo.
    MediaInfo also contains tables of addional metadata. These tables are maps
    of keys to values. The keys themselves should remain in the format that is
    defined by the metadata (I.E. Hex-Numbers, FOURCC, ...) and will be
    translated to more readable and i18nified values by an external entity.
    """
    def __init__(self):
        self.keys = []
        self._tables = {}
        for k in MEDIACORE:
            setattr(self,k,None)
            self.keys.append(k)
        # get media type by parsing the __class__ information
        media = str(self.__class__)
        media = media[media.find('kaa.metadata.') + 13:]
        self.media = media[:media.find('.')]
        self.keys.append('media')


    def __unicode__(self):
        keys = copy.copy(self.keys)
        hidden = []
        for k in UNPRINTABLE_KEYS:
            if k in keys:
                keys.remove(k)
                hidden.append(k)

        result = reduce( lambda a,b: self[b] and b != u'url' and \
                         u'%s\n        %s: %s' % \
                         (a, unicode(b), unicode(self[b])) or a, keys, u'' )
        for h in hidden:
            if self[h]:
                result += u'\n        %s: <unprintable data>' % h
        if log.level < 30:
            try:
                for i in self._tables.keys():
                    try:
                        result += unicode(self._tables[i])
                    except AttributeError:
                        pass
            except AttributeError:
                pass
        return result


    def __str__(self):
        return unicode_to_str(unicode(self))

    
    def appendtable(self, name, hashmap, language='en'):
        """
        Appends a tables of additional metadata to the Object.
        If such a table already exists, the given tables items are
        added to the existing one.
        """
        if not self._tables.has_key((name, language)):
            self._tables[(name, language)] = \
                                table.Table(hashmap, name, language)
        else:
            # Append to the already existing table
            for k in hashmap.keys():
                self._tables[(name, language)][k] = hashmap[k]


    def correct_data(self):
        """
        Correct same data based on specific rules
        """
        # make sure all strings are unicode
        for key in self.keys:
            if key in UNPRINTABLE_KEYS:
                continue
            value = getattr(self, key)
            if isinstance(value, str):
                setattr(self, key, str_to_unicode(value))
            if isinstance(value, unicode):
                setattr(self, key, value.strip().rstrip().replace(u'\0', u''))


    def gettable(self, name, language='en'):
        """
        returns a table of the given name and language
        """
        return self._tables.get((name, language), {})


    def setitem(self, item, dict, key, convert_to_str=False):
        """
        set item to a specific value for the dict
        """
        try:
            if self.__dict__.has_key(item):
                if not dict[key]:
                    return
                if convert_to_str and not isinstance(dict[key], unicode):
                    self.__dict__[item] = str_to_unicode(str(dict[key]))
                else:
                    self.__dict__[item] = dict[key]
            else:
                log.error("Unknown key: %s" % item)
        except KeyError:
            pass
        except (KeyboardInterrupt, SystemExit):
            sys.exit(0)
        except:
            if log.level < 30:
                log.exception('setkey')


    def __contains__(self, key):
        """
        Test if key exists in the dict
        """
        return key in self.__dict__


    def get(self, key, default = None):
        """
        Returns key in dict, otherwise defaults to 'default' if key doesn't
        exist.
        """
        if key not in self:
            return default
        return self[key]


    def __getitem__(self,key):
        """
        get the value of 'key'
        """
        if self.__dict__.has_key(key):
            return self.__dict__[key]
        elif hasattr(self, key):
            return getattr(self, key)
        return None


    def __setitem__(self, key, val):
        """
        set the value of 'key' to 'val'
        """
        self.__dict__[key] = val


    def has_key(self, key):
        """
        check if the object has a key 'key'
        """
        return self.__dict__.has_key(key) or hasattr(self, key)


    def __delitem__(self, key):
        """
        delete informations about 'key'
        """
        try:
            del self.__dict__[key]
        except (KeyboardInterrupt, SystemExit):
            sys.exit(0)
        except:
            pass
        if hasattr(self, key):
            setattr(self, key, None)


class AudioInfo(MediaInfo):
    """
    Audio Tracks in a Multiplexed Container.
    """
    def __init__(self):
        self.keys = []
        for k in AUDIOCORE:
            setattr(self,k,None)
            self.keys.append(k)


class MusicInfo(AudioInfo):
    """
    Digital Music.
    """
    def __init__(self):
        MediaInfo.__init__(self)
        for k in AUDIOCORE+MUSICCORE:
            setattr(self,k,None)
            self.keys.append(k)


    def correct_data(self):
        """
        correct trackof to be two digest
        """
        AudioInfo.correct_data(self)
        if self['trackof']:
            try:
                # XXX Why is this needed anyway?
                if int(self['trackno']) < 10:
                    self['trackno'] = '0%s' % int(self['trackno'])
            except (KeyboardInterrupt, SystemExit):
                sys.exit(0)
            except:
                pass


class VideoInfo(MediaInfo):
    """
    Video Tracks in a Multiplexed Container.
    """
    def __init__(self):
        self.keys = []
        for k in VIDEOCORE:
            setattr(self,k,None)
            self.keys.append(k)


class ChapterInfo(MediaInfo):
    """
    Chapter in a Multiplexed Container.
    """
    def __init__(self, name="", pos=0):
        self.keys = ['name', 'pos', 'enabled']
        setattr(self,'name', name)
        setattr(self,'pos', pos)
        setattr(self,'enabled', True)


class SubtitleInfo(MediaInfo):
    """
    Subtitle Tracks in a Multiplexed Container.
    """
    def __init__(self):
        self.keys = ['language', 'trackno', 'title']
        for k in self.keys:
            setattr(self, k, None)


class AVInfo(MediaInfo):
    """
    Container for Audio and Video streams. This is the Container Type for
    all media, that contain more than one stream.
    """
    def __init__(self):
        MediaInfo.__init__(self)
        for k in AVCORE:
            setattr(self,k,None)
            self.keys.append(k)
        self.audio = []
        self.video = []
        self.subtitles = []
        self.chapters  = []


    def correct_data(self):
        """
        correct length to be an int
        """
        MediaInfo.correct_data(self)
        if not self['length'] and len(self.video) and self.video[0]['length']:
            self['length'] = self.video[0]['length']
        for container in [ self ] + self.video + self.audio:
            if container['length']:
                container['length'] = int(container['length'])


    def find_subtitles(self, filename):
        """
        Search for subtitle files. Right now only VobSub is supported
        """
        base = os.path.splitext(filename)[0]
        if os.path.isfile(base+'.idx') and \
               (os.path.isfile(base+'.sub') or os.path.isfile(base+'.rar')):
            file = open(base+'.idx')
            if file.readline().find('VobSub index file') > 0:
                for line in file.readlines():
                    if line.find('id') == 0:
                        sub = SubtitleInfo()
                        sub.language = line[4:6]
                        sub.trackno = base + '.idx'  # Maybe not?
                        self.subtitles.append(sub)
            file.close()


    def __unicode__(self):
        result = u'Attributes:'
        result += MediaInfo.__unicode__(self)
        if len(self.video) + len(self.audio) + len(self.subtitles) > 0:
            result += "\n Stream list:"
            if len(self.video):
                result += reduce( lambda a,b: a + u'  \n   Video Stream:' + \
                                  unicode(b), self.video, u'' )
            if len(self.audio):
                result += reduce( lambda a,b: a + u'  \n   Audio Stream:' + \
                                  unicode(b), self.audio, u'' )
            if len(self.subtitles):
                result += reduce( lambda a,b: a + u'  \n   Subtitle Stream:' +\
                                  unicode(b), self.subtitles, u'' )

        if not isinstance(self.chapters, int) and len(self.chapters) > 0:
            result += u'\n Chapter list:'
            for i in range(len(self.chapters)):
                pos = self.chapters[i]['pos']
                result += u'\n   %2s: "%s" %02d:%02d:%02d.%03d' % \
                          (i+1, unicode(self.chapters[i]['name']),
                           int(pos)/60/60, int(pos/60) % 60, 
                           int(pos)%60, (pos-int(pos))*1000)
        return result


class CollectionInfo(MediaInfo):
    """
    Collection of Digial Media like CD, DVD, Directory, Playlist
    """
    def __init__(self):
        MediaInfo.__init__(self)
        self.tracks = []
        self.keys.append('id')
        self.id = None

    def __unicode__(self):
        result = MediaInfo.__unicode__(self)
        result += u'\nTrack list:'
        for counter in range(0,len(self.tracks)):
             result += u' \nTrack %d:\n%s' % \
                       (counter+1, unicode(self.tracks[counter]))
        return result

    def appendtrack(self, track):
        self.tracks.append(track)
