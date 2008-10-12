Usage
=====

The usage is very simple, you only need to call the "parse" function
with the filename as parameter to get a MediaInfo object back (or
None, if the media can't be detected. Detection of discs like an audio
cd, vcd or dvd works only with linux right now. Please send us a patch
if you can get it working with BSD, MaxOS or Windows. The DVD parser
needs libdvdread to be installed.

All internal data is unicode.

Example::

  import kaa.metadata
  info = kaa.metadata.parse('movie.avi')
  disc = kaa.metadata.parse('/dev/dvd')

The result of the parse function is a parser object inherting from a
Media class.

Methods
-------

The parse result has the following functions:

.. automethod:: metadata.core.Media.get
.. automethod:: metadata.core.Media.__getitem__
.. automethod:: metadata.core.Media.has_key
.. automethod:: metadata.core.Media.keys
.. automethod:: metadata.core.Media.convert

Attributes / Keys
-----------------

The list of keys the Media object supports depends on the type of
parser. E.g. a video parser supports the attribute audio for the audio
track information while an image parser does not provide that
information. The following is a (possible incomplete) list of keys
available.

    * artist
    * bitrate
    * caption
    * chapters
    * comment
    * copyright
    * country
    * delay
    * encoder
    * filename
    * genre
    * image
    * keywords
    * language
    * length
    * media
    * mime
    * mpeg_version
    * producer
    * product
    * rating
    * sequence_header_offset
    * size
    * software
    * starring
    * start
    * studio
    * subtype
    * table_mapping
    * timestamp
    * title
    * trackno
    * trackof
    * type
    * url
    * writer 

Arrays, e.g. info.video[0].width 

    * audio
    * subtitles
    * video 

mminfo
------

The module will install the script mminfo. It is a small example for
the module itself and a nice script to parse media files on the
command line.::

    -> mminfo star-wars-3-teaser.mov
    kaa media metadata info
    filename : star-wars-3-teaser.mov
    Attributes:
            title: Episode III Teaser Trailer
            artist: starwars.com Hyperspace
            type: Quicktime Video
            date: 04/11/04
            media: video
            length: 107
            copyright: Copright (c) 2004 Lucasfilm Ltd.
     Stream list:
       Video Stream:
            length: 107
            codec: SVQ3
            width: 480
            height: 206
       Audio Stream:
            length: 107
            codec: QDM2
            language: en
