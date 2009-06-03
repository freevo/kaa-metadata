Parser
======

Current Parser
--------------

The following parser are available right now. Most parsers have no
docstring, so the documentation is very bad. Feel free to send in a
patch.

Audio
^^^^^
.. autoclass:: metadata.audio.ac3.Parser
.. autoclass:: metadata.audio.adts.Parser
.. autoclass:: metadata.audio.mp3.Parser
.. autoclass:: metadata.audio.flac.Parser
.. autoclass:: metadata.audio.m4a.Parser
.. autoclass:: metadata.audio.ogg.Parser
.. autoclass:: metadata.audio.pcm.Parser
.. autoclass:: metadata.audio.webradio.Parser
.. autoclass:: metadata.video.asf.AsfAudio


Image
^^^^^
.. autoclass:: metadata.image.bmp.Parser
.. autoclass:: metadata.image.gif.Parser
.. autoclass:: metadata.image.jpg.Parser
.. autoclass:: metadata.image.png.Parser
.. autoclass:: metadata.image.tiff.Parser


Video
^^^^^
.. autoclass:: metadata.video.asf.Asf
.. autoclass:: metadata.video.flv.Parser
.. autoclass:: metadata.video.mkv.Parser
.. autoclass:: metadata.video.mp4.Parser
.. autoclass:: metadata.video.mpeg.Parser
.. autoclass:: metadata.video.ogm.Parser
.. autoclass:: metadata.video.real.Parser
.. autoclass:: metadata.video.riff.Parser
.. autoclass:: metadata.video.vcd.Parser


Disc
^^^^
.. autoclass:: metadata.disc.audio.Parser
.. autoclass:: metadata.disc.dvd.Parser
.. autoclass:: metadata.disc.vcd.Parser


Games
^^^^^
.. autoclass:: metadata.games.gameboy.Parser
.. autoclass:: metadata.games.snes.Parser


Misc
^^^^
.. autoclass:: metadata.misc.directory.Parser
.. autoclass:: metadata.misc.xmlfile.Parser


How to add a Parser
-------------------

PleaseUpdate: add some doc here 
