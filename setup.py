#!/usr/bin/env python

"""Setup script for the kaa.metadata distribution."""

__revision__ = "$Id$"

from distutils.core import setup, Extension
import popen2
import os

try:
    from src import version
    version = version.VERSION
except ImportError:
    version = ''
    
extensions = [ Extension('src/disc/cdrom', ['src/disc/cdrommodule.c']) ]

# check for libdvdread (bad hack!)
# Windows does not have Popen4, so catch exception here
try:
    child = popen2.Popen4('gcc -ldvdread')
    if child.fromchild.readline().find('cannot find') == -1:
        # gcc failed, but not with 'cannot find', so libdvd must be
        # somewhere (I hope)
        extensions.append(Extension('kaa/metadata/disc/ifoparser',
                                    ['src/disc/ifomodule.c'],
                                    libraries=[ 'dvdread' ],
                                    library_dirs=['/usr/local/lib'],
                                    include_dirs=['/usr/local/include']))
    child.wait()
except AttributeError, e:
    print "No Popen4 found. This seems to be Windows."
    print "Installing without libdvdread support."
    # Hack: disable extensions for Windows.
    # This would better be done by a clean detect of windows. But how?
    extensions = []

# create fake kaa.__init__.py
open('__init__.py', 'w').close()

setup (name = "kaa-metadata",
       version = version,
       description = "Module for retrieving information about media files",
       author = "Thomas Schueppel, Dirk Meyer",
       author_email = "freevo-devel@lists.sourceforge.net",
       url = "http://freevo.sf.net/kaa",

       scripts     = [ 'bin/mminfo' ],

       package_dir = {'kaa.metadata.video': 'src/video',
                      'kaa.metadata.audio': 'src/audio',
                      'kaa.metadata.audio.eyeD3': 'src/audio/eyeD3',
                      'kaa.metadata.image': 'src/image',
                      'kaa.metadata.disc' : 'src/disc',
                      'kaa.metadata.misc' : 'src/misc',
                      'kaa.metadata'      : 'src',
                      'kaa'               : '.'},

       packages = [ 'kaa.metadata', 'kaa.metadata.video', 'kaa.metadata.audio',
                    'kaa.metadata.audio.eyeD3', 'kaa.metadata.image',
                    'kaa.metadata.disc', 'kaa.metadata.misc' ],

       py_modules  = [ 'kaa.__init__' ],
       ext_modules = extensions

      )

# delete fake kaa.__init__.py
os.unlink('__init__.py')
