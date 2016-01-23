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

from aqt import QImage, Qt

from extmodules.tempdir import tempdir

_countryCode='dk'

class GalleryManager:
    def __init__(self, editor, config, provider):
        self.editor = editor
        self.config = config
        self.webMainFrame = self.editor.web.page().mainFrame()
        self.tempDir = tempdir.TempDir()
        self.wordThumbs = {}
        self.wordUrls = {}
        self.currentImg = ""
        self.chosenImgPath = ""
        self.provider = provider.lower()
        if provider.lower() == "bing":
            from extmodules.bingsearchapi import bingsearchapi
            if not self.config['APIs']['bing']:
                #Load modal dialog to setup API
                pass
            self.servant = bingsearchapi.BingSearchAPI(self.config['APIs']['bing'])

    def __del__(self):
        #FIXME: Call this destructor explicitly somewhere
        self.tempDir.dissolve()

    def downloadPictures(self, word, query, nThumbs):
        nid = self.currentNote.id
        if not self.wordUrls.has_key(nid):
            self.wordThumbs[nid] = []
            self.wordUrls[nid] = self.getUrls(query, nThumbs)
            for i, th in enumerate(self.wordUrls[nid]['thumb']):
                fileName = os.path.join(self.tempDir.name, 'thumb_' + word + '_' + str(i) )
                urlretrieve(th, fileName)
                self.wordThumbs[nid].append(fileName)

    def buildGallery(self, word, specterm="", nThumbs=5):
        self.chosenImg = ""
        self.currentNote = self.editor.note
        nid = self.currentNote.id
        m = re.match(r'<img src="(.*)" />', self.currentNote['Picture'])
        if m:
            self.currentImg = m.group(1)
        else:
            self.currentImg = ""
        self.currentWord = word
        query = word + " " + specterm
        if not self.wordUrls.has_key(nid):
            self.downloadPictures(word, query, nThumbs)
        #Build html gallery
        gallery = '<div style="width:90\% float:left" id="gallery">'
        gallery += '<div id="currentimg">'
        if self.currentImg != "":
            gallery += u'<img src="{0}"/>'.format(self.currentImg)
        else:
            gallery += u'<img src="{0}/ffvocdeckbuilder/images/no_image.png"/>'.format(self.editor.mw.pm.addonFolder())
        gallery += '</div><div id="thumbs">'
        for i, wd in enumerate(self.wordThumbs[nid]):
            gallery += u'<a href="img{0}"><img src="{1}" alt="" /></a>\n'.format(i, wd)
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
                      #'Market':'"da-DK"',
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
            newThumbnail = u'<img src="{0}"/>'.format(self.wordThumbs[self.currentWord][idx])
            self.webMainFrame.findFirstElement('#currentimg').setInnerXml(newThumbnail)
            name, ext = os.path.splitext(self.wordUrls[self.currentWord]['image'][idx])
            #FIXME Add language prefix
            newImgName = u"ipa_dict_{0}_{1}{2}".format(_countryCode, self.currentWord, ext)
            newImgPath = os.path.join(self.tempDir.name, newImgName)
            #fileName = os.path.join(fold, 'thumb_' + word.lower() + '_' + str(i))
            urlretrieve(self.wordUrls[self.currentWord]['image'][idx], newImgPath)
            self.chosenImgPath = newImgPath

    def resizeImage(self, imgPath, desiredSize=400):
        img = QImage(imgPath)
        if (img.width() > desiredSize) or (img.height() > desiredSize):
            imgScaled = img.scaled(desiredSize, desiredSize, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            #NOTE: Tries to determine the format from the extension in the file name.
            #What happens if the file name doesn't have an extension? Should we manage this case?
            imgScaled.save(imgPath)

    def finalizePreviousSelection(self):
        if hasattr(self, 'currentNote'):
            #Resize the image chosen via the gallery and save it to the note
            if self.chosenImgPath != "":
                imgName = self.editor.mw.col.media.addFile(self.chosenImgPath)
                self.currentNote['Picture'] = self.currentNote['Picture'] + u'<img src="{0}" />'.format(imgName)
                self.currentNote.flush()
                self.chosenImgPath = ""
