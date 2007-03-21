# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# kaa.metadata.__init__.py
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

# import factory code for kaa.metadata access
from factory import *
import disc.cdrom as cdrom

from core import Media, MEDIA_AUDIO, MEDIA_VIDEO, MEDIA_IMAGE, \
     MEDIA_AV, MEDIA_SUBTITLE, MEDIA_CONTAINER, MEDIA_DIRECTORY, MEDIA_DISC, \
     MEDIA_GAME, EXTENSION_STREAM, EXTENSION_DEVICE, EXTENSION_DIRECTORY

# use network functions
USE_NETWORK = 1

# Audio parsers
register('audio/mpeg', ('mp3',), 'audio.mp3.MP3')
register('audio/ac3', ('ac3',), 'audio.ac3.AC3')
register('application/adts', ('aac',), 'audio.adts.ADTS')
register('application/flac', ('flac',), 'audio.flac.Flac')
register('audio/m4a', ('m4a',), 'audio.m4a.Mpeg4Audio')
register('application/ogg', ('ogg',), 'audio.ogg.Ogg')
register('application/pcm', ('aif','voc','au'), 'audio.pcm.PCM')
register('text/plain', EXTENSION_STREAM, 'audio.webradio.WebRadio')

# Video parsers
register('video/asf', ('asf','wmv','wma'), 'video.asf.Asf')
register('video/flv', ('flv',), 'video.flv.FlashVideo')
register('application/mkv', ('mkv', 'mka'), 'video.mkv.Matroska')
register('video/quicktime', ('mov', 'qt', 'mp4', 'mp4a', '3gp', '3gp2', 'mk2'), 'video.mp4.MPEG4')
register('video/mpeg', ('mpeg','mpg','mp4', 'ts'), 'video.mpeg.MPEG')
register('application/ogg', ('ogm', 'ogg'), 'video.ogm.Ogm')
register('video/real', ('rm', 'ra', 'ram'), 'video.real.RealVideo')
register('video/avi', ('wav','avi'), 'video.riff.Riff')
register('video/vcd', ('cue',), 'video.vcd.VCDFile')

# Disc parsers
register('audio/cd', EXTENSION_DEVICE, 'disc.audio.AudioDisc')
register('cd/unknown', EXTENSION_DEVICE, 'disc.data.DataDisc')
register('video/dvd', EXTENSION_DEVICE, 'disc.dvd.DVDInfo')
register('video/dvd', EXTENSION_DIRECTORY, 'disc.dvd.DVDInfo')
register('video/dvd', ('iso',), 'disc.dvd.DVDInfo')
register('video/vcd', EXTENSION_DEVICE, 'disc.vcd.VCD')

# Image parsers
register('image/bmp', ('bmp', ), 'image.bmp.BMP')
register('image/gif', ('gif', ), 'image.gif.GIF')
register('image/jpeg', ('jpg','jpeg'), 'image.jpg.JPG')
register('image/png', ('png',), 'image.png.PNG')
register('image/tiff', ('tif','tiff'), 'image.tiff.TIFF')

# Games parsers
register('games/gameboy', ('gba', 'gb', 'gbc'), 'games.gameboy.Gameboy')
register('games/snes', ('smc', 'sfc', 'fig'), 'games.snes.SNES')

# Misc parsers
register('directory', EXTENSION_DIRECTORY, 'misc.directory.Directory')
register('text/xml', ('xml', 'fxd', 'html', 'htm'), 'misc.xmlfile.XML')
