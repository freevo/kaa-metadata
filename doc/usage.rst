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

The result behaves like a read-only dict in Python with some
additional methods depending on the parser used. The following
methods are available.

.. automethod:: metadata.core.Media.get
.. automethod:: metadata.core.Media.__getitem__
.. automethod:: metadata.core.Media.has_key
.. automethod:: metadata.core.Media.keys
.. automethod:: metadata.core.Media.convert

The list of keys the Media object supports depends on the type of
parser. E.g. a video parser supports the attribute audio for the audio
track information while an image parser does not provide that
information.


Attributes / Keys
-----------------

.. attribute:: Media.table

  Some parsers add additional information in the `tables` attribute of
  the result. This variable contains he EXIF header for JPEG images,
  the full list of ID3 tags for mp3 files and much more. The tables
  depend on the parsers and on the files parsed.

.. attribute:: Media.media

  Defines the basic media type.

Based on the media type the object has additional member
variables. These are also the keys in the dict. If you checked `media`
to be MEDIA_IMAGE, you can be sure that the object has an attribute
`people` (but it may be None).

**Media Core**: Basic sets of attributes most media objects have

  Attributes: `title`, `caption`, `comment`, `size`, `type`,
  `subtype`, `timestamp`, `keywords`, `country`, `language`,
  `langcode`, `url`, `media`, `artist`, `mime`

**MEDIA_IMAGE**: Image file

  Attributes: Core attributes, `description`, `people`, `location`,
  `event`, `width`, `height`, `thumbnail`, `software`, `hardware`,
  `dpi`, `city`, `rotation`, `author`

**MEDIA_AUDIO** Audio file or stream:

  Attributes: Core attributes, `channels`, `samplerate`, `length`,
  `encoder`, `codec`, `format`, `samplebits`, `bitrate`, `fourcc`,
  `trackno`, `id`, `userdate`

  Additional attributes for stand-alone audio files not inside a
  container: `trackof`, `album`, `genre`, `discs`, `thumbnail`

**MEDIA_AV**: A/V container with audio and video content

  Attributes: Core attributes, `length`, `encoder`, `trackno`,
  `trackof`, `copyright`, `product`, `genre`, `writer`, `producer`,
  `studio`, `rating`, `starring`, `thumbnail`, `delay`, `image`,
  `video`, `audio`, `subtitles`, `chapters`, `software`

  The attributes `video`, `audio`, `subtitles` and `chapters` are
  lists with additional media objects of different types.

  **MEDIA_VIDEO**: Video stream inside MEDIA_AV

    Attributes: Core attributes, `length`, `encoder`, `bitrate`,
    `samplerate`, `codec`, `format`, `samplebits`, `width`, `height`,
    `fps`, `aspect`, `trackno`, `fourcc`, `id`

  **MEDIA_CHAPTER**: Chapter in a container (e.g. MEDIA_AV)

    Attributes: `name`, `pos`, `enabled`, `id`

  **MEDIA_SUBTITLE**: Subtitle stream inside MEDIA_AV

    Attributes: `language`, `trackno`, `title`, `id`

**MEDIA_DISC**: Disc (dvd, audio disc, etc)

 DVD rips on hard-disc in iso file, as directory with a VIDEO_TS
 subtree or VCD cue/bin files are also of this type.

 Basic disc attributes: `id`, `tracks`, `mixed`, `label`

 Additional DVD attributes: `length`

 Additional DVD title (MEDIA_AV) attributes: `angles`

**MEDIA_DIRECTORY**: Directory

  Attributes: Core attributes

**MEDIA_GAME**: Game file on hard-disc

  Attributes: Core attributes

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
