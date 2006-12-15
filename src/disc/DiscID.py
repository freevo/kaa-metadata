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
