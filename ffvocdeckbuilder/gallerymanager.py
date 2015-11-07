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
from urllib import urlretrieve

from extmodules.tempdir import tempdir

_apikey="YOURKEY"
_countryCode='dk'

class GalleryManager:
    def __init__(self, editor, provider):
        self.editor = editor
        self.webMainFrame = self.editor.web.page().mainFrame()
        self.tempDir = tempdir.TempDir()
        self.wordThumbs = {}
        self.wordUrls = {}
        self.currentImg = ""
        self.chosenImgPath = ""
        self.provider = provider.lower()
        if provider.lower() == "bing":
            from extmodules.bingsearchapi import bingsearchapi
            self.servant = bingsearchapi.BingSearchAPI(_apikey)

    def __del__(self):
        #FIXME: Call this destructor explicitly somewhere
        self.tempDir.dissolve()

    def downloadPictures(self, word, query, nThumbs):
        if not self.wordUrls.has_key(word):
            self.wordThumbs[word] = []
            self.wordUrls[word] = self.getUrls(query, nThumbs)
            for i, th in enumerate(self.wordUrls[word]['thumb']):
                fileName = os.path.join(self.tempDir.name, 'thumb_' + word + '_' + str(i) )
                urlretrieve(th, fileName)
                self.wordThumbs[word].append(fileName)

    def buildGallery(self, word, specterm="", nThumbs=5):
        self.chosenImg = ""
        self.currentNote = self.editor.note
        m = re.match(r'<img src="(.*)" />', self.currentNote['Picture'])
        if m:
            self.currentImg = m.group(1)
        else:
            self.currentImg = ""
        self.currentWord = word
        query = word + " " + specterm
        if not self.wordUrls.has_key(word):
            self.downloadPictures(word, query, nThumbs)
        #Build html gallery
        gallery = '<div style="width:90\% float:left" id="gallery">'
        gallery += '<div id="currentimg">'
        if self.currentImg != "":
            gallery += '<img src="%s"/>' % self.currentImg
        else:
            gallery += '<img src="%s/ffvocdeckbuilder/images/no_image.png"/>' % self.editor.mw.pm.addonFolder()
        gallery += '</div><div id="thumbs">'
        for i, wd in enumerate(self.wordThumbs[word]):
            gallery += '<a href="img%i"><img src="%s" alt="" /></a>\n' % (i, wd)
        gallery += '</div></div>'
        #Keep input field and reduce its size in order to allow drag and drop
        #FIXME: Find a more elegant solution to allow drag and drop
        oxml = self.webMainFrame.findFirstElement("#f4").toOuterXml()
        oxml = oxml.replace('style="','style="width:4%; float:left; ' )
        oxml += gallery
        self.webMainFrame.findFirstElement("#f4").setOuterXml(oxml)
        #FIXME: Use BeautifulSoup?

    def getUrls(self, query, nThumbs):
        imageUrls = {'thumb':[], 'image':[]}
        if self.provider == "bing":
            params = {'$format': 'json',
                      '$top': nThumbs}
            query += u' loc:' + unicode(_countryCode)
            results = self.servant.search('Image', query, params).json()
            for res in results['d']['results']:
                imageUrls['thumb'].append(res['Thumbnail']['MediaUrl'])
                imageUrls['image'].append(res['MediaUrl'])
            #FIXME: Use requests to download the images
        #FIXME: Check how tts download the files in the correct folder
        return imageUrls

    def linkHandler(self, l):
        #FIXME: Why does QUrl add a path??
        if re.match("img[0-9]+", l) is not None:
            idx=int(l.replace("img", ""))
            newThumbnail = '<img src="%s"/>' % (self.wordThumbs[self.currentWord][idx])
            self.webMainFrame.findFirstElement('#currentimg').setInnerXml(newThumbnail)
            name, ext = os.path.splitext(self.wordUrls[self.currentWord]['image'][idx])
            #FIXME Add language prefix
            newImgName = "ipa_dict_%s_%s%s" % (_countryCode, self.currentWord, ext)
            newImgPath = os.path.join(self.tempDir.name, newImgName)
            #fileName = os.path.join(fold, 'thumb_' + word.lower() + '_' + str(i))
            urlretrieve(self.wordUrls[self.currentWord]['image'][idx], newImgPath)
            self.chosenImgPath = newImgPath

    def finalizePreviousSelection(self):
        if self.chosenImgPath != "":
            imgName = self.editor.mw.col.media.addFile(self.chosenImgPath)
            self.currentNote['Picture'] = '<img src="%s" />' % imgName
            self.currentNote.flush()
            self.chosenImgPath = ""
