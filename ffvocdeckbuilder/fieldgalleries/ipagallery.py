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

import json
import os
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup

from .fieldgallery import FieldGallery

class IpaGallery(FieldGallery):
    def __init__(self, editor, config):
        self.editor = editor
        self.config = config
        self.ipa = {}
        self.loadLanguageCodes()
        super().__init__("ipa")

    def loadLanguageCodes(self):
        self.languageCodes = {}
        fileName = u"{0}/ffvocdeckbuilder/files/iso-639-1-language-codes" \
            .format(self.editor.mw.pm.addonFolder())
        with open(fileName) as f:
            for line in f:
                (key, val) = line.split(',')
                self.languageCodes[key] = val.rstrip('\n')

    def downloadIpa(self, word):
        if not word in self.ipa:
            found = list()

            #Wiktionary
            url = 'https://en.wiktionary.org/wiki/{0}'.format(word)
            r = urlopen(url).read()
            soup = BeautifulSoup(r, 'html.parser')
            rawIpa = soup.find_all("span", class_="IPA")
            for s in rawIpa:
                foundIpaLanguage = s.findPrevious('h2').span.get_text()
                if re.match(self.languageCodes[self.config['Languages']['Primary']], foundIpaLanguage):
                    found.append({'provider': 'Wiktionary (en)', 'ipa' : s.get_text().rstrip(' ')})
                    a = s.findPrevious('span', id=re.compile('Etymology_\d+'))
                    if a:
                        found[-1]['spec'] = a.get_text()
            self.ipa[word] = found

    def downloadIpas(self, wordList):
        for word in wordList:
            self.downloadIpa(word)

    def showGallery(self, word, nThumbs=5):
        self.currentNote = self.editor.note
        self.currentWord = word
        if not word in self.ipa:
            self.downloadIpa(word)
        #Find pos in model & make searchid
        pos=[i for i,sr in enumerate(self.currentNote.model()['flds']) \
                if re.match('IPA transcription',sr['name'])]
        s_id="#f"+str(pos[0])
        #Find IPAs currently in the note
        self.currentIpas = re.findall('\[[^\]]+\]|\/[^\/]+\/', self.currentNote['IPA transcription'])
        gallery = '<div id="ipagallery">'
        gallery += '''<select onchange="getSelectValues(this)" onfocus="enableButtons();" id="ipaselector" name="ipa" multiple>''' #FIXME: onfocus="pycmd('focus:6');"
        #Add the current IPAs as red text and selected
        for i, c in enumerate(self.currentIpas):
            gallery += '<option selected="selected" style="color:red;" value="ipac{2}">{0}; {1}'.format(c, 'Current IPA', i)
        for i, v in enumerate(self.ipa[word]):
            if 'gender' in v:
                gallery += '<option value="ipa{3}">{0}; {2} {1}'.format(v['ipa'], v['provider'], v['gender'], i)
            else:
                gallery += '<option value="ipa{2}">{0}; {1}'.format(v['ipa'], v['provider'], i)
            if 'spec' in v:
                gallery += ', {0}'.format(v['spec'])
            gallery += '</option>'
        gallery += '</select></div>'
        self.editor.web.eval('''$('{0}').replaceWith('{1}')'''.format(s_id, gallery))

    def setIpa(self, ipaTxt):
        if re.match("ipa", ipaTxt) is not None:
            self.currentNote['IPA transcription'] = ''
            for i in re.findall("ipac([0-9]+)", ipaTxt):
                self.currentNote['IPA transcription'] += self.currentIpas[int(i)] + ' '
            for i in re.findall("ipa([0-9]+)", ipaTxt):
                self.currentNote['IPA transcription'] += self.ipa[self.currentWord][int(i)]['ipa'] + ' '
                #FIXME: Flush only once at the end from noteeditor
            self.currentNote.flush()
