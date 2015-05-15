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

class GalleryManager:
    def __init__(self, editor, provider):
        self.editor = editor
        self.webMainFrame = self.editor.web.page().mainFrame()
        self.tempDir = tempdir.TempDir()
        self.wordThumbs = {}
        self.wordUrls = {}
        self.currentImg = dict()
        self.provider = provider.lower()
        if provider.lower() == "bing":
            from extmodules.bingsearchapi import bingsearchapi
            self.servant = bingsearchapi.BingSearchAPI(_apikey)

    def __del__(self):
        #FIXME: Call this destructor explicitly somewhere
        self.tempDir.dissolve()

    def buildGallery(self, word, specterm="", nThumbs=5):
        self.currentWord = word
        query = word + " " + specterm
        if not self.wordUrls.has_key(word):
            self.wordThumbs[word] = []
            self.wordUrls[word] = self.getUrls(query, nThumbs)
            for i in range(nThumbs-1):
                fileName = os.path.join(self.tempDir.name, 'thumb_' + word + '_' + str(i) )
                urlretrieve(self.wordUrls[word]['thumb'][i], fileName)
                self.wordThumbs[word].append(fileName)
        #Build html gallery
        gallery = '<div id="gallery">'
        gallery += '<div id="currentimg">'
        if self.currentImg.has_key(self.currentWord):
            gallery += '<img src="%s"/>' % self.currentImg[self.currentWord]
        else:
            gallery += '<img src="%s/ffvocdeckbuilder/images/no_image.png"/>' % self.editor.mw.pm.addonFolder()
        gallery += '</div><div id="thumbs">'
        for i in range(nThumbs-1):
            gallery += '<a href="img%i"><img src="%s" alt="" /></a>\n' % (i, self.wordThumbs[word][i])
        gallery += '</div></div>'
        self.webMainFrame.findFirstElement("#f3").setOuterXml(gallery)
        #FIXME: Use BeautifulSoup?

    def getUrls(self, query, nThumbs):
        imageUrls = {'thumb':[], 'image':[]}
        if self.provider == "bing":
            params = {'$format': 'json',
                      '$top': nThumbs}
            results = self.servant.search('Image', query, params).json()
            for i in range(1, nThumbs):
                imageUrls['thumb'].append(results['d']['results'][i]['Thumbnail']['MediaUrl'])
                imageUrls['image'].append(results['d']['results'][i]['MediaUrl'])
            #FIXME: Use requests to download the images
        #FIXME: Check how tts download the files in the correct folder
        return imageUrls