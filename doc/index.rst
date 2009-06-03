.. kaa.metadata documentation master file, created by sphinx-quickstart
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

kaa.metadata
============

Kaa.metadata is a powerful media metadata parser. It can extract
metadata (such as id3 tags, for example) from a wide range of media
files. Attributes like codec, length, resolution, audio/video/subtitle
tracks, and chapters are also returned. The module has support for the
following formats:

    * Audio: ac3, dts, flac, mp3 (with id3 tag support), ogg, pcm, m4a, wma.
    * Video: avi, mkv, mpg, ogm, asf, wmv, flv, mov, dvd iso, vcd iso.
    * Media: vcd, cd, dvd.
    * Image: jpeg (with exif and iptc support), bmp, gif, png, tiff. 

The module is the successor of MMPython created by Thomas Schueppel
and maintained by the Freevo project for the last years.

    * Dependencies: libdvdread (optional; for dvd parsing)
    * License: GPL 

Contents:

.. toctree::
   :maxdepth: 2

   usage
   parser


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
