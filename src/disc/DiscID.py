#!/usr/bin/env python

# Module for fetching information about an audio compact disc and
# returning it in a format friendly to CDDB.

# If called from the command line, will print out disc info in a
# format identical to Robert Woodcock's 'cd-discid' program.

# Written 17 Nov 1999 by Ben Gertzfield <che@debian.org>
# This work is released under the GNU GPL, version 2 or later.

# Release version 1.3
# CVS ID: $Id$

import cdrom, sys

def cddb_sum(n):
    ret = 0
    
    while n > 0:
	ret = ret + (n % 10)
	n = n / 10

    return ret

def open(device=None, flags=None):
    # Allow this function to be called with no arguments,
    # specifying that we should call cdrom.open() with
    # no arguments.
    if device == None:
        return cdrom.open()
    elif flags == None:
        return cdrom.open(device)
    else:
        return cdrom.open(device, flags)

def disc_id(device):
    (first, last) = cdrom.toc_header(device)

    track_frames = []
    checksum = 0
    
    for i in range(first, last + 1):
	(min, sec, frame) = cdrom.toc_entry(device, i)
	checksum = checksum + cddb_sum(min*60 + sec)
	track_frames.append(min*60*75 + sec*75 + frame)

    (min, sec, frame) = cdrom.leadout(device)
    track_frames.append(min*60*75 + sec*75 + frame)

    total_time = (track_frames[-1] / 75) - (track_frames[0] / 75)
	       
    discid = ((checksum % 0xff) << 24 | total_time << 8 | last)

    return [discid, last] + track_frames[:-1] + [ track_frames[-1] / 75 ]

if __name__ == '__main__':

    dev_name = None
    device = None
    
    if len(sys.argv) >= 2:
	dev_name = sys.argv[1]

    if dev_name:
        device = open(dev_name)
    else:
        device = open()
        
    disc_info = disc_id(device)

    print ('%08lx' % disc_info[0]),

    for i in disc_info[1:]:
	print ('%d' % i),
