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
        self.audios = {}
        self.provider = provider.lower()
        if self.provider == "forvo":
            if not self.config['APIs']['forvo']:
                #Load modal dialog to setup API
                pass
            #self.servant = forvoffvdb.ForvoDownloader(self.config['APIs']['forvo'])
        super().__init__("pronunciation")

    def downloadAudio(self, word):
        if not word in self.audios:
            self.audios[word] = self.getAudio(word, 1)

    def downloadAudios(self, wordList):
        for word in wordList:
            self.downloadAudio(word)

    def showGallery(self, word, nThumbs=5):
        """Creates an html gallery for the pronunciation tracks.

        Show radio buttons to choose among the different pronuciation tracks
        and for each track display a play button which is used to reproduce the track.
        """
        #Load our javascript code
        #FIXME: Add this to an activate function

        if not word in self.audios:
            self.downloadAudio(word)
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
        if self.currentSound != "":
            gallery += u'<input class="container" onclick="setFfvdbPronunciation(-2)" type="radio" name="pronunciation" value="{0}">' \
                       u'<img class="container" src="{1}/ffvocdeckbuilder/icons/no_sound.png" style="max-width: 32px; max-height: 1em; min-height:24px;"/>'.format(self.currentSound, self.editor.mw.pm.addonFolder())
            gallery += u'<input class="container" onclick="setFfvdbPronunciation(-1)" type="radio" name="pronunciation" value="{0}" checked>' \
                       u'<a href="soundCurrent"><img class="container" src="{1}/ffvocdeckbuilder/icons/current_sound.png" alt="play"' \
                       u'style="max-width: 32px; max-height: 1em; min-height:24px;" /></a>'.format(self.currentSound, self.editor.mw.pm.addonFolder())
        else:
            gallery += u'<input class="container" onclick="setFfvdbPronunciation(-2)" type="radio" name="pronunciation" value="{0}" checked>' \
                       u'<img class="container" src="{1}/ffvocdeckbuilder/icons/no_sound.png" style="max-width: 32px; max-height: 1em; min-height:24px;"/>'.format(self.currentSound, self.editor.mw.pm.addonFolder())
        for i, af in enumerate(self.audios[word]):
            gallery += u'<input class="container" onclick="setFfvdbPronunciation({0})" type="radio" name="pronunciation" value="{1}">' \
                       u'<a href="sound{0}"><img class="container" src="{2}/ffvocdeckbuilder/icons/play.png" alt="play"' \
                       u'style="max-width: 32px; max-height: 1em; min-height:24px;" /></a>'.format(i, self.audios[word][i], self.editor.mw.pm.addonFolder())
                       #'style="max-width: 32px; max-height: 1em; min-height:24px;" /></a>' % (self.audios[i].file_path, i, self.editor.mw.pm.addonFolder())
        gallery += '</form>'
        gallery += '</div>'
        self.editor.web.eval('''$('{0}').replaceWith('{1}')'''.format(s_id, gallery))

    def getAudio(self, word, nThumbs):
        """Download, normalize and filter pronunciations track from the given service.

           Retrieve audio pronunciations of the given word using a single downloader.
           Using a bash script who calls sox and ffmpeg, performs normalization and noise
           removal on the downloaded tracks.

           Returns a list containing the full file name of the downloaded tracks.
        """
        field_data = FieldData('Pronunciation sound', 'Word', word)
        self.servant.download_files(field_data, self.config['Languages']['Primary'])
        ret = list()
        #Normalise and noise filter the downloaded audio tracks
        for i, el in enumerate(self.servant.downloads_list):
            #Verify that the file is a proper audio file
            #FIXME: This is forvo related. Shouldn't be managed in forvo servant?
            with open(el.file_path, 'r') as f:
                try:
                    errorMessageFromForvo = f.readline()
                    if errorMessageFromForvo == '["Audio request is expired."]':
                        print('{0}: {1}'.format(el.file_path, errorMessageFromForvo))
                        continue #Skip this audio pronunciation
                except:
                    pass

            #cleanAudioFile = self.cleanAudio(el.file_path)
            cleanAudioFile = el.file_path
            extension = os.path.splitext(cleanAudioFile)[1][1:].strip().lower()
            newfile = u"/tmp/ipa_voc_da_{0}{1}.{2}".format(word, i, extension)
            shutil.move(cleanAudioFile, newfile)
            ret.append(newfile)
        return ret

    def onBridgeCmd(self, n):
        n = int(n)
        """Callback called when a radio button is clicked. The first radio button (-2)
        means delete the sound, the second (-1) means keep current sound, they others (0..N) allow to
        select the downloaded sounds.
        """
        if n == -2:
            self.chosenSnd = ''
        elif n == -1:
            self.chosenSnd = u"[sound:{0}]".format(self.currentSound)
        else:
            sndName = self.editor.mw.col.media.addFile(self.audios[self.currentWord][n])
            self.chosenSnd = u"[sound:{0}]".format(sndName)

        self.currentNote['Pronunciation sound'] = self.chosenSnd
        self.currentNote.flush()

    def linkHandler(self, l):
        if re.match("sound[0-9]+", l) is not None:
            idx=int(l.replace("sound", ""))
            playSound = self.audios[self.currentWord][idx]
            play(playSound)
        elif l == 'soundCurrent':
            playSound = self.currentSound
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
