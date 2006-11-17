/* -*- coding: iso-8859-1 -*-
 * ---------------------------------------------------------------------------
 * dvdinfo.py - parse dvd title structure
 * ---------------------------------------------------------------------------
 * $Id$
 *
 * ---------------------------------------------------------------------------
 * kaa-Metadata - Media Metadata for Python
 * Copyright (C) 2003-2005 Thomas Schueppel, Dirk Meyer
 *
 * First Edition: Dirk Meyer <dmeyer@tzi.de>
 * Maintainer:    Dirk Meyer <dmeyer@tzi.de>
 *
 * based on http://arnfast.net/projects/ifoinfo.php by Jens Arnfast
 * and lsdvd by by Chris Phillips
 *
 * Please see the file AUTHORS for a complete list of authors.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MER-
 * CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
 * Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 *
 * ---------------------------------------------------------------------------
*/

#include <Python.h>

#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>
#include <unistd.h>
#include <assert.h>
#include <inttypes.h>
#include <stdint.h>

#include <dvdread/dvd_reader.h>
#include <dvdread/ifo_types.h>
#include <dvdread/ifo_read.h>

static PyObject * ifoinfo_get_audio_tracks(ifo_handle_t *vtsfile, int id) {
    char audioformat[10];
    char audiolang[5];
    int audiochannels;
    int audiofreq;
    audio_attr_t *attr;

    if (!vtsfile->vts_pgcit || !vtsfile->vtsi_mat)
        return NULL;

    attr = &vtsfile->vtsi_mat->vts_audio_attr[id];

    if ( attr->audio_format == 0
         && attr->multichannel_extension == 0
         && attr->lang_type == 0
         && attr->application_mode == 0
         && attr->quantization == 0
         && attr->sample_frequency == 0
         && attr->channels == 0
         && attr->lang_extension == 0
         && attr->unknown1 == 0
         && attr->unknown1 == 0) {
        return NULL;
    }

    /* audio format */
    switch (attr->audio_format) {
    case 0:
        snprintf(audioformat, 10, "ac3");
        break;
    case 1:
        snprintf(audioformat, 10, "N/A");
        break;
    case 2:
        snprintf(audioformat, 10, "mpeg1");
        break;
    case 3:
        snprintf(audioformat, 10, "mpeg2ext");
        break;
    case 4:
        snprintf(audioformat, 10, "lpcm");
        break;
    case 5:
        snprintf(audioformat, 10, "N/A");
        break;
    case 6:
        snprintf(audioformat, 10, "dts");
        break;
    default:
        snprintf(audioformat, 10, "N/A");
    }

    switch (attr->lang_type) {
    case 0:
        assert(attr->lang_code == 0 || attr->lang_code == 0xffff);
        snprintf(audiolang, 5, "N/A");
        break;
    case 1:
        snprintf(audiolang, 5, "%c%c", attr->lang_code>>8,
                 attr->lang_code & 0xff);
        break;
    default:
        snprintf(audiolang, 5, "N/A");
    }

    switch(attr->sample_frequency) {
    case 0:
        audiofreq = 48000;
        break;
    case 1:
        audiofreq = -1;
        break;
    default:
        audiofreq = -1;
    }

    audiochannels = attr->channels + 1;

    //AUDIOTRACK: ID=%i; LANG=%s; FORMAT=%s; CHANNELS=%i; FREQ=%ikHz
    return Py_BuildValue("(ssii)", audiolang, audioformat, audiochannels,
                         audiofreq);
}

static PyObject * ifoinfo_get_subtitle_tracks(ifo_handle_t *vtsfile, int id) {
    char language[5];
    subp_attr_t *attr;

    if (!vtsfile->vts_pgcit)
        return NULL;

    attr = &vtsfile->vtsi_mat->vts_subp_attr[id];

    if ( attr->type == 0
         && attr->lang_code == 0
         && attr->zero1 == 0
         && attr->zero2 == 0
         && attr->lang_extension == 0 ) {
        return Py_BuildValue("s", "N/A");
    }

    /* language code */
    if (isalpha((int)(attr->lang_code >> 8)) &&
        isalpha((int)(attr->lang_code & 0xff))) {
        snprintf(language, 5, "%c%c", attr->lang_code >> 8,
                 attr->lang_code & 0xff);
    } else {
        snprintf(language, 5, "%02x%02x",
                 0xff & (unsigned)(attr->lang_code >> 8),
                 0xff & (unsigned)(attr->lang_code & 0xff));
    }

    return Py_BuildValue("s", language);
}

static PyObject *ifoinfo_read_title(dvd_reader_t *dvd, ifo_handle_t *ifofile,
                                    int id) {
    tt_srpt_t *tt_srpt;
    ifo_handle_t *vtsfile;
    video_attr_t *video_attr;
    long playtime;
    int fps;
    PyObject *ret;
    PyObject *audio;
    PyObject *subtitles;
    PyObject *tmp;
    int i;


    tt_srpt = ifofile->tt_srpt;
    Py_BEGIN_ALLOW_THREADS
    vtsfile = ifoOpen(dvd, tt_srpt->title[id].title_set_nr);
    Py_END_ALLOW_THREADS


    if (!vtsfile)
        return NULL;

    playtime = 0;
    fps = 0;
    if (vtsfile->vts_pgcit) {
        dvd_time_t *time;
        i = vtsfile->vts_ptt_srpt->title[tt_srpt->title[id].vts_ttn - 1].ptt[0].pgcn - 1;
        time = &vtsfile->vts_pgcit->pgci_srp[i].pgc->playback_time;
        playtime = (((time->hour &   0xf0) >> 3) * 5 + (time->hour   & 0x0f)) * 3600 +
            (((time->minute & 0xf0) >> 3) * 5 + (time->minute & 0x0f)) * 60 +
            ((time->second & 0xf0) >> 3) * 5 + (time->second & 0x0f);
        fps = (time->frame_u & 0xc0) >> 6;
    }

    audio = PyList_New(0);
    for (i=0; i < vtsfile->vtsi_mat->nr_of_vts_audio_streams; i++) {
        tmp = ifoinfo_get_audio_tracks(vtsfile, i);
        if (!tmp)
            break;
        PyList_Append(audio, tmp);
    }

    subtitles = PyList_New(0);
    for (i=0; i < vtsfile->vtsi_mat->nr_of_vts_subp_streams; i++) {
        tmp = ifoinfo_get_subtitle_tracks(vtsfile, i);
        if (!tmp)
            break;
        PyList_Append(subtitles, tmp);
    }

    video_attr = &vtsfile->vtsi_mat->vts_video_attr;

    /* chapters, angles, playtime, fps, format, aspect, width, height, audio,
       subtitles */
    ret = Py_BuildValue("(iiiiiiiiOO)",
                        tt_srpt->title[id].nr_of_ptts,
                        tt_srpt->title[id].nr_of_angles,
                        playtime,

                        fps,
                        video_attr->video_format,
                        video_attr->display_aspect_ratio,

                        video_attr->picture_size,
                        video_attr->video_format,
                        audio,
                        subtitles);
    ifoClose(vtsfile);
    return ret;
}


static PyObject *ifoinfo_parse(PyObject *self, PyObject *args) {
    char *dvddevice;
    dvd_reader_t *dvd;
    ifo_handle_t *ifofile;
    PyObject *ret;
    int i;

    if (!PyArg_ParseTuple(args, "s", &dvddevice))
        return Py_BuildValue("i", 0);

    Py_BEGIN_ALLOW_THREADS
    dvd = DVDOpen(dvddevice);
    Py_END_ALLOW_THREADS

    if (!dvd) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    Py_BEGIN_ALLOW_THREADS
    ifofile = ifoOpen(dvd, 0);
    Py_END_ALLOW_THREADS

    if (!ifofile) {
        DVDClose(dvd);
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = PyList_New(0);

    for (i=0; i<ifofile->tt_srpt->nr_of_srpts; i++) {
        PyObject *title = ifoinfo_read_title(dvd, ifofile, i);
        if (!title)
            break;
        PyList_Append(ret, title);
    }

    /* close */
    ifoClose(ifofile);
    DVDClose(dvd);
    return ret;

}


static PyMethodDef IfoMethods[] = {
    {"parse",  ifoinfo_parse, METH_VARARGS},
    {NULL, NULL}
};


void initifoparser(void) {
    (void) Py_InitModule("ifoparser", IfoMethods);
    PyEval_InitThreads();
}
