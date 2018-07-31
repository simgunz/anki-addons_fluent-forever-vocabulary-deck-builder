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

import os
import re
import shutil
import subprocess

from anki.sound import play

from downloadaudio.downloaders import downloaders
from downloadaudio.field_data import FieldData
#import sox #External dep

from .fieldgallery import FieldGallery

class PronunciationGallery(FieldGallery):
    def __init__(self, editor, config, provider):
        self.editor = editor
        self.config = config
        self.provider = provider.lower()
        if self.provider == "forvo":
            if not self.config['APIs']['forvo']:
                #Load modal dialog to setup API
                pass
            #self.servant = forvoffvdb.ForvoDownloader(self.config['APIs']['forvo'])
        super().__init__("pronunciation")

    def showGallery(self, word, nThumbs=5):
        """Creates an html gallery for the pronunciation tracks.

        Show radio buttons to choose among the different pronuciation tracks
        and for each track display a play button which is used to reproduce the track.
        """
        #Load our javascript code
        #FIXME: Add this to an activate function

        self.download(word)
        self.currentNote = self.editor.note
        #Find pos in model & make searchid
        pos=[i for i,sr in enumerate(self.currentNote.model()['flds']) \
                if re.match('Pronunciation sound',sr['name'])]
        s_id="#f"+str(pos[0])
        m = re.match(r'\[sound:(.*)\]', self.currentNote['Pronunciation sound'])
        if m:
            self.currentSound = m.group(1)
        else:
            self.currentSound = ""
        self.currentWord = word
        #Build html gallery
        gallery = '<div id="audiogallery">'
        gallery += '<form action="">'
        icon_no_sound = self.editor.resourceToData('{0}/ffvocdeckbuilder/icons/no_sound.png'.format(self.editor.mw.pm.addonFolder()))
        icon_current_sound = self.editor.resourceToData('{0}/ffvocdeckbuilder/icons/current_sound.png'.format(self.editor.mw.pm.addonFolder()))
        icon_sound = self.editor.resourceToData('{0}/ffvocdeckbuilder/icons/play.png'.format(self.editor.mw.pm.addonFolder()))
        if self.currentSound != "":
            gallery += '<input class="container" onclick="setFfvdbPronunciation(-2)" type="radio" name="pronunciation" value="{0}">' \
                       '<img class="container" src="{1}" style="max-width: 32px; max-height: 1em; min-height:24px;"/>'.format(self.currentSound, icon_no_sound)
            gallery += '<input class="container" onclick="setFfvdbPronunciation(-1)" type="radio" name="pronunciation" value="{0}" checked>' \
                       '<a onclick="playPronunciation(-1);" href="#"><img class="container" src="{1}" alt="play"' \
                       'style="max-width: 32px; max-height: 1em; min-height:24px;" /></a>'.format(self.currentSound, icon_current_sound)
        else:
            gallery += '<input class="container" onclick="setFfvdbPronunciation(-2)" type="radio" name="pronunciation" value="{0}" checked>' \
                       '<img class="container" src="{1}" style="max-width: 32px; max-height: 1em; min-height:24px;"/>'.format(self.currentSound, icon_current_sound)
        for i, af in enumerate(self._downloadedItems[word]):
            gallery += '<input class="container" onclick="setFfvdbPronunciation({0})" type="radio" name="pronunciation" value="{1}">' \
                       '<a onclick="playPronunciation({0});" href="#"><img class="container" src="{2}" alt="play"' \
                       'style="max-width: 32px; max-height: 1em; min-height:24px;" /></a>'.format(i, self._downloadedItems[word][i], icon_sound)
                       #'style="max-width: 32px; max-height: 1em; min-height:24px;" /></a>' % (self.audios[i].file_path, i, self.editor.mw.pm.addonFolder())
        gallery += '</form>'
        gallery += '</div>'
        self._insertGalleryInHTML(s_id, gallery)

    def _download(self, word):
        """Download, normalize and filter pronunciations track from the given service.

           Retrieve audio pronunciations of the given word using a single downloader.
           Using a bash script who calls sox and ffmpeg, performs normalization and noise
           removal on the downloaded tracks.

           Returns a list containing the full file name of the downloaded tracks.
           
           Not-thread safe: reuses the same downloaders objects
        """
        ret = list()
        
        retrieved_entries = []
        field_data = FieldData('Pronunciation sound', 'Word', word)
        for dloader in downloaders[0:2]:
            # Use a public variable to set the language.
            dloader.language = self.config['Languages']['Primary']
            try:
                # Make it easer inside the downloader. If anything
                # goes wrong, don't catch, or raise whatever you want.
                dloader.download_files(field_data)
            except:
                #  # Uncomment this raise while testing a new
                #  # downloaders.  Also use the “For testing”
                #  # downloaders list with your downloader in
                #  # downloaders.__init__
                # raise
                continue
            retrieved_entries += dloader.downloads_list
                
        #Normalise and noise filter the downloaded audio tracks
        for i, el in enumerate(retrieved_entries):
            #Verify that the file is a proper audio file
            #FIXME: This is forvo related. Shouldn't be managed in forvo servant?
            with open(el.file_path, 'r') as f:
                try:
                    errorMessageFromForvo = f.readline()
                    if errorMessageFromForvo == '["Audio request is expired."]':
                        print(('{0}: {1}'.format(el.file_path, errorMessageFromForvo)))
                        continue #Skip this audio pronunciation
                except:
                    pass

            #cleanAudioFile = self.cleanAudio(el.file_path)
            cleanAudioFile = el.file_path
            extension = os.path.splitext(cleanAudioFile)[1][1:].strip().lower()
            newfile = "/tmp/ipa_voc_da_{0}{1}.{2}".format(word, i, extension)
            shutil.move(cleanAudioFile, newfile)
            ret.append(newfile)
        return ret

    def onBridgeCmd(self, cmd):
        """Callback called when a radio button is clicked. The first radio button (-2)
        means delete the sound, the second (-1) means keep current sound, they others (0..N) allow to
        select the downloaded sounds.
        """
        action, n = tuple(cmd.split('.'))
        n = int(n)
        if action == "set":
            if n == -2:
                self.chosenSnd = ''
            elif n == -1:
                self.chosenSnd = "[sound:{0}]".format(self.currentSound)
            else:
                sndName = self.editor.mw.col.media.addFile(self._downloadedItems[self.currentWord][n])
                self.chosenSnd = "[sound:{0}]".format(sndName)

            self.currentNote['Pronunciation sound'] = self.chosenSnd
            self.currentNote.flush()
        elif action == "play":
            if n >= 0:
                playSound = self._downloadedItems[self.currentWord][n]
            else:
                playSound = self.currentSound #playSound = self.currentSound[-n-1]
            play(playSound)

    def cleanAudio(self, audioFile, noiseSampleLength=0.3):
        '''Process the audio track in order to improve the quality

        Remove noise, perform volume normalization, shorten the track by removing silence
        '''
        inputAudioStream = pysox.CSoxStream(audioFile)

        sigInfo = inputAudioStream.get_signal().get_signalinfo()
        audioLength = sigInfo['length']/sigInfo['rate'] #In seconds

        #If the audio track is too short we probably can't acquire a clean sample of noise, so it's better
        #to not perform noise removal
        if audioLength < 3*noiseSampleLength:
            performNoiseFiltering = 0
        else:
            performNoiseFiltering = 1

        #Acquire the noise profile from a piece of the audio track that contains only noise
        if performNoiseFiltering:
            #Extract part of track with only noise
            noiseStream = pysox.CSoxStream('noise.wav','w',inputAudioStream.get_signal())

            noiseExtractorChain = pysox.CEffectsChain(inputAudioStream, noiseStream)
            noiseExtractorChain.add_effect(pysox.CEffect("trim", [b'-{0}'.format(noiseSampleLength)]))
            noiseExtractorChain.flow_effects()
            noiseStream.close()

            #Noise profiler
            noiseStream = pysox.CSoxStream('noise.wav','r',inputAudioStream.get_signal())
            dummyoutfile = pysox.CSoxStream('dummyout.wav', 'w', inputAudioStream.get_signal())

            #The chain require an output file even if the noiseprof effect doesn't require it, so we create a dummy file
            noiseProfilerChain = pysox.CEffectsChain(noiseStream, dummyoutfile)
            noiseProfilerChain.add_effect(pysox.CEffect("noiseprof", [ b'noise.prof' ]))
            noiseProfilerChain.flow_effects()
            noiseStream.close()
            dummyoutfile.close()

        #We need to close and reopen the input audio or it doesn't work
        inputAudioStream.close()

        ##Apply all effects
        inputAudioStream = pysox.CSoxStream(audioFile)
        cleanedAudioFile = os.path.join(os.path.dirname(audioFile), 'cleaned-' + os.path.basename(audioFile))
        cleanedAudioStream = pysox.CSoxStream(cleanedAudioFile,'w',inputAudioStream.get_signal())

        noiseRemovalChain = pysox.CEffectsChain(inputAudioStream, cleanedAudioStream)

        #Filter noise
        if performNoiseFiltering:
            noiseRemovalChain.add_effect(pysox.CEffect("noisered", [ b'noise.prof' ]))

        #Remove silence
        noiseRemovalChain.add_effect(pysox.CEffect("silence", [ b'1', b'0.1', b'0.5%']))
        noiseRemovalChain.add_effect(pysox.CEffect("reverse", []))
        noiseRemovalChain.add_effect(pysox.CEffect("silence", [ b'1', b'0.1', b'0.5%']))
        noiseRemovalChain.add_effect(pysox.CEffect("reverse", []))

        #Normalize
        noiseRemovalChain.add_effect(pysox.CEffect("gain", [ b'-n', b'-2' ]))

        noiseRemovalChain.flow_effects()
        inputAudioStream.close()
        cleanedAudioStream.close()

        if performNoiseFiltering:
            os.remove('noise.wav')
            os.remove('noise.prof')
            os.remove('dummyout.wav')

        return cleanedAudioFile
