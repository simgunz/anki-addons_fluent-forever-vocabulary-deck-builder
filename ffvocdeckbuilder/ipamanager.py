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
import urllib
from urllib.request import urlretrieve
from bs4 import BeautifulSoup

from .extmodules.tempdir import tempdir

_javaFunctions="""
formatMulticolumn = function(){
  var s = document.getElementsByTagName('SELECT')[0].options,
      l = 0,
      d = '';
  for(i = 0; i < s.length; i++){
    if(s[i].text.length > l) l = s[i].text.length;
  }
  for(i = 0; i < s.length; i++){
    d = '';
    line = s[i].text.split(';');
    l1 = (l - line[0].length);
    for(j = 0; j < l1; j++){
      d += '\u00a0';
    }
    s[i].text = line[0] + d + line[1];
  }
  $('#ipaselector').css('font-family', '"Courier New", Courier, monospace')
};

function getSelectValues(select) {
  var result = [];
  var options = select && select.options;
  var opt;

  for (var i=0, iLen=options.length; i<iLen; i++) {
    opt = options[i];

    if (opt.selected) {
      result.push(opt.value || opt.text);
    }
  }
  py.run("ffvdb:setipa:" + result);
}
"""

class IpaManager:
    def __init__(self, editor, config):
        self.editor = editor
        self.config = config
        self.webMainFrame = self.editor.web.page().mainFrame()
        self.ipa = {}
        self.loadLanguageCodes()

    def loadLanguageCodes(self):
        self.languageCodes = {}
        fileName = u"{0}/ffvocdeckbuilder/files/iso-639-1-language-codes" \
            .format(self.editor.mw.pm.addonFolder())
        with open(fileName) as f:
            for line in f:
                (key, val) = line.split(',')
                self.languageCodes[key] = val.rstrip('\n')

    def downloadIpa(self, word):
        if not self.ipa.has_key(word):
            found = list()

            #Wiktionary
            url = u'https://en.wiktionary.org/wiki/{0}'.format(word)
            r = urllib.urlopen(url.encode('utf-8')).read()
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

    def buildGallery(self, word, nThumbs=5):
        self.currentNote = self.editor.note
        self.currentWord = word
        if not self.ipa.has_key(word):
            self.downloadIpa(word)
        #Find pos in model & make searchid
        pos=[i for i,sr in enumerate(self.currentNote.model()['flds']) \
                if re.match('IPA transcription',sr['name'])]
        s_id="#f"+str(pos[0])
        #Find IPAs currently in the note
        self.currentIpas = re.findall('\[[^\]]+\]|\/[^\/]+\/', self.currentNote['IPA transcription'])
        gallery = u'<div id="ipagallery">'
        gallery += u'<select onchange="getSelectValues(this)" id="ipaselector" name="ipa" multiple>'
        #Add the current IPAs as red text and selected
        for i, c in enumerate(self.currentIpas):
            gallery += u'<option selected="selected" style="color:red;" value="ipac{2}">{0}; {1}'.format(c, 'Current IPA', i)
        for i, v in enumerate(self.ipa[word]):
            if v.has_key('gender'):
                gallery += u'<option value="ipa{3}">{0}; {2} {1}'.format(v['ipa'], v['provider'], v['gender'], i)
            else:
                gallery += u'<option value="ipa{2}">{0}; {1}'.format(v['ipa'], v['provider'], i)
            if v.has_key('spec'):
                gallery += u', {0}'.format(v['spec'])
            gallery += u'</option>'
        gallery += u'</select></div>'
        self.webMainFrame.findFirstElement(s_id).setOuterXml(gallery)
        self.editor.web.eval(_javaFunctions)
        self.editor.web.eval("formatMulticolumn();")

    def setIpa(self, ipaTxt):
        if re.match("ipa", ipaTxt) is not None:
            self.currentNote['IPA transcription'] = ''
            for i in re.findall("ipac([0-9]+)", ipaTxt):
                self.currentNote['IPA transcription'] += self.currentIpas[int(i)] + ' '
            for i in re.findall("ipa([0-9]+)", ipaTxt):
                self.currentNote['IPA transcription'] += self.ipa[self.currentWord][int(i)]['ipa'] + ' '
                #FIXME: Flush only once at the end from noteeditor
            self.currentNote.flush()
