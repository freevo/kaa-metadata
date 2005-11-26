# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# discinfo.py - basic class for any discs containing collections of media.
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-Metadata - Media Metadata for Python
# Copyright (C) 2003-2005 Thomas Schueppel, Dirk Meyer
#
# First Edition: Dirk Meyer <dmeyer@tzi.de>
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

# freevo imports
import os
import re
import time
import array
import md5
from struct import *
import logging
from fcntl import ioctl

# kaa imports
from kaa.metadata import mediainfo

# get logging object
log = logging.getLogger('metadata')

CREATE_MD5_ID = 0

import DiscID


def cdrom_disc_status(device, handle_mix = 0):
    """
    check the current disc in device
    return: no disc (0), audio cd (1), data cd (2), blank cd (3)
    """
    CDROM_DRIVE_STATUS=0x5326
    CDSL_CURRENT=( (int ) ( ~ 0 >> 1 ) )
    CDROM_DISC_STATUS=0x5327
    CDS_AUDIO=100
    CDS_MIXED=105
    CDS_DISC_OK=4

    # FreeBSD ioctls - there is no CDROM.py
    # XXX 0xc0086305 below creates a warning, but 0xc0086305L
    # doesn't work. Suppress that warning for Linux users,
    # until a better solution can be found.
    if os.uname()[0] == 'FreeBSD':
        CDIOREADTOCENTRYS = 0xc0086305L
        CD_MSF_FORMAT = 2

    try:
        fd = os.open(device, os.O_RDONLY | os.O_NONBLOCK)
        if os.uname()[0] == 'FreeBSD':
            try:
                cd_toc_entry = array.array('c', '\000'*4096)
                (address, length) = cd_toc_entry.buffer_info()
                buf = pack('BBHP', CD_MSF_FORMAT, 0, length, address)
                s = ioctl(fd, CDIOREADTOCENTRYS, buf)
                s = CDS_DISC_OK
            except:
                s = CDS_NO_DISC
        else:
            s = ioctl(fd, CDROM_DRIVE_STATUS, CDSL_CURRENT)
    except:
        log.error('ERROR: no permission to read %s' % device)
        log.error('Media detection not possible, set drive to \'empty\'')

        # maybe we need to close the fd if ioctl fails, maybe
        # open fails and there is no fd, maye we aren't running
        # linux and don't have ioctl
        try:
            os.close(fd)
        except:
            pass
        return 0

    if not s == CDS_DISC_OK:
        # no disc, error, whatever
        try:
            os.close(fd)
        except:
            pass
        return 0

    if os.uname()[0] == 'FreeBSD':
        s = 0
        # We already have the TOC from above
        for i in range(0, 4096, 8):
            control = unpack('B', cd_toc_entry[i+1])[0] & 4
            track = unpack('B', cd_toc_entry[i+2])[0]
            if track == 0:
                break
            if control == 0 and s != CDS_MIXED:
                s = CDS_AUDIO
            elif control != 0:
                if s == CDS_AUDIO:
                    s = CDS_MIXED
                else:
                    s = 100 + control # ugly, but encodes Linux ioctl returns
            elif control == 5:
                s = CDS_MIXED

    else:
        s = ioctl(fd, CDROM_DISC_STATUS)
    os.close(fd)

    if s == CDS_MIXED and handle_mix:
        return 4
    if s == CDS_AUDIO or s == CDS_MIXED:
        return 1

    try:
        fd = open(device, 'rb')
        # try to read from the disc to get information if the disc
        # is a rw medium not written yet

        fd.seek(32768) # 2048 multiple boundary for FreeBSD
        # FreeBSD doesn't return IOError unless we try and read:
        fd.read(1)
    except IOError:
        # not readable
    	fd.close()
	return 3

    # disc ok
    fd.close()
    return 2


id_cache = {}

def cdrom_disc_id(device, handle_mix=0):
    """
    return the disc id of the device or None if no disc is there
    """
    global id_cache
    try:
        if id_cache[device][0] + 0.9 > time.time():
            return id_cache[device][1:]
    except:
        pass

    disc_type = cdrom_disc_status(device, handle_mix=handle_mix)
    if disc_type == 0 or disc_type == 3:
        return 0, None

    elif disc_type == 1 or disc_type == 4:
        # audio disc
        cdrom = DiscID.open(device)
        id = DiscID.disc_id(cdrom)
        id = '%08lx_%d' % (id[0], id[1])
        cdrom.close()
    else:
        f = open(device,'rb')

        if os.uname()[0] == 'FreeBSD':
            # FreeBSD can only seek to 2048 multiple boundaries.
            # Below works on Linux and FreeBSD:
            f.seek(32768)
            id = f.read(829)
            label = id[40:72]
            id = id[813:829]
        else:
            f.seek(0x0000832d)
            id = f.read(16)
            f.seek(32808, 0)
            label = f.read(32)

        if CREATE_MD5_ID:
            id_md5 = md5.new()
            id_md5.update(f.read(51200))
            id = id_md5.hexdigest()

        f.close()

        m = re.match("^(.*[^ ]) *$", label)
        if m:
            id = '%s%s' % (id, m.group(1))
        id = re.compile('[^a-zA-Z0-9()_-]').sub('_', id)


    id_cache[device] = time.time(), disc_type, id
    id = id.replace('/','_')
    return disc_type, id


class DiscInfo(mediainfo.CollectionInfo):
    def isDisc(self, device):
        (type, self.id) = cdrom_disc_id(device, handle_mix=1)
        if type != 2:
            if type == 4:
                self.keys.append('mixed')
                self.mixed = 1
                type = 1
            return type

        if CREATE_MD5_ID:
            if len(self.id) == 32:
                self.label = ''
            else:
                self.label = self.id[32:]
        else:
            if len(self.id) == 16:
                self.label = ''
            else:
                self.label = self.id[16:]

        self.keys.append('label')
        return type
