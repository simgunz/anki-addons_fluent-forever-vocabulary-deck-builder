# -*- coding: utf-8 -*-
#########################################################################
# Copyright (C) 2015 by Simone Gaiarin <simgunz@gmail.com>              #
#                                                                       #
# This program is free software; you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation; either version 3 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program; if not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

import re
import shutil
import subprocess

from anki.sound import play

from extmodules.tempdir import tempdir
from extmodules.downloadaudio.downloaders import forvoffvdb
from extmodules.downloadaudio.field_data import FieldData
from extmodules import ushlex

_language='XX'

class PronunciationManager:
    def __init__(self, editor, provider):
        self.editor = editor
        self.webMainFrame = self.editor.web.page().mainFrame()
        self.tempDir = tempdir.TempDir()
        self.provider = provider.lower()
        if self.provider == "forvo":
            self.servant = forvoffvdb.ForvoDownloader()

    def __del__(self):
        #self.servant.__del__()
        self.tempDir.dissolve()

    def buildGallery(self, word, nThumbs=5):
        """Creates an html gallery for the pronunciation tracks.

        Show radio buttons to choose among the different pronuciation tracks
        and for each track display a play button which is used to reproduce the track.
        """

        self.currentWord = word
        self.audios = self.getAudio(word, 1)
        #Build html gallery
        gallery = '<div id="audiogallery">'
        #gallery += '<div id="currentaudio">'
        #if self.currentImg != "":
            #gallery += '<img src="%s"/>' % self.currentImg
        #else:
            #gallery += '<img src="%s/ffvocdeckbuilder/images/no_image.png"/>' % self.editor.mw.pm.addonFolder()
        #gallery += '</div><div id="thumbs">'
        gallery += '<form action="">'
        for i, af in enumerate(self.audios):
            gallery += '<input class="container" type="radio" name="pronunciation" value="%s">' \
                       '<a href="sound%d"><img class="container" src="%s/ffvocdeckbuilder/images/replay.png" alt="play"' \
                           'style="max-width: 32px; max-height: 1em; min-height:24px;" /></a>' % (self.audios[i], i, self.editor.mw.pm.addonFolder())
                       #'style="max-width: 32px; max-height: 1em; min-height:24px;" /></a>' % (self.audios[i].file_path, i, self.editor.mw.pm.addonFolder())
        gallery += '</form>\n'
        gallery += '</div>\n'
        self.webMainFrame.findFirstElement("#f4").setOuterXml(gallery)

    def getAudio(self, word, nThumbs):
        """Download, normalize and filter pronunciations track from the given service.

           Retrieve audio pronunciations of the given word using a single downloader.
           Using a bash script who calls sox and ffmpeg, performs normalization and noise
           removal on the downloaded tracks.

           Returns a list containing the full file name of the downloaded tracks.
        """
        field_data = FieldData('Pronunciation sound', 'Word', word)
        self.servant.download_files(field_data, _language)
        ret = list()
        #Normalise and noise filter the downloaded audio tracks
        for i, el in enumerate(self.servant.downloads_list):
            newfile = u"/tmp/ipa_voc_da_%s%d.ogg" % (word, i)
            shutil.move(el.file_path, newfile)
            cmd = u"%s/ffvocdeckbuilder/scripts/filteraudio %s" % (self.editor.mw.pm.addonFolder(),
                                                    newfile)
            subprocess.call(ushlex.split(cmd))
            ret.append(newfile)
        return ret

    def linkHandler(self, l):
        if re.match("sound[0-9]+", l) is not None:
            idx=int(l.replace("sound", ""))
            playSound = self.audios[idx]
            play(playSound)
