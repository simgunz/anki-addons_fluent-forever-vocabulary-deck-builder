# -*- coding: utf-8 -*-
#########################################################################
# Copyright (C) 2014 by Simone Gaiarin <simgunz@gmail.com>              #
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
import types
import os
import re
import threading

import anki
import aqt
from anki import hooks
from anki.utils import ids2str
from aqt.editor import Editor
from aqt.qt import QUrl, QDesktopServices

from gallerymanager import GalleryManager
from pronunciationmanager import PronunciationManager
from ipamanager import IpaManager

_galleryCss = """
#normal2, #normal3, #normal4, #normal5 {
    display: none;
}
#gallery {
    margin: 0 auto;
}
#currentimg img {
    height: 70px;
    border: 6px solid #0033FF;
    margin: 6px;
    float: left;
}
#thumbs {
    margin: 0px auto 0px auto;
    float: left;
}
#thumbs img {
    height: 70px;
    border: none;
}
#thumbs a:link, #thumbs a:visited {
    color: #EEE;
    height: 70px;
    border: 6px solid #555;
    margin: 6px;
    float: left;
}
#thumbs a:hover {
    border: 6px solid #888;
}
#audiogallery form {
    float: left;
}
#ipaselector {
    font-size: 20px;
}
"""

_nPreload = 5
_nGalleryThumbs = 8

class NoteEditor(object):

    def __init__(self, editor):
        self.editor = editor
        self.mw = self.editor.mw
        self.web = editor.web
        self.webMainFrame = self.web.page().mainFrame()
        self.currentWord = ''
        self.preloadedNotesIds = list()
        self.wordUrls = {}
        self.wordThumbs = {}
        #self.nextNotes = list(_nPreload)
        #self.prevNotes = list(_nPreload)
        self.galleryManager = GalleryManager(self.editor, "Bing")
        self.pronunciationManager = PronunciationManager(self.editor, "Forvo")
        self.ipaManager = IpaManager(self.editor)

    def __del__(self):
        #FIXME: Call this destructor explicitly somewhere
        self.galleryManager.finalizePreviousSelection()
        self.galleryManager.__del__()
        self.pronunciationManager.__del__()

    def loadCssStyleSheet(self):
        css = str(self.webMainFrame.findFirstElement('style').toInnerXml())
        css += _galleryCss
        self.webMainFrame.findFirstElement('style').setInnerXml(css)

    def showIFrames(self, word):
        tdElems = self.webMainFrame.findAllElements("td")
        #for i in range(5):
            #oxml = tdElems[i].toOuterXml()
            #oxml = oxml.replace('<td width="100%">', '<td width="30%">')
            #tdElems[i].setOuterXml(oxml)

        fNames = self.webMainFrame.findAllElements(".fname")
        oxml = fNames[0].toOuterXml()
        oxml += '<td rowspan="6"><iframe id="wikitionary" src="https://en.wiktionary.org/wiki/%s#Danish" width="490" height="200" scrolling="yes"></iframe></td>' \
                '<td rowspan="6"><iframe id="ddo" src="http://ordnet.dk/ddo/ordbog?query=%s" width="490" height="200" scrolling="yes"></iframe></td>' \
                    % (word, word)
        self.iframes = ['en.wiktionary.org', 'ordnet.dk']
        fNames[0].setOuterXml(oxml)

        #import requests
        #from lxml import html

        ##storing response
        #response = requests.get('http://ordnet.dk/ddo/ordbog?query=%s' % word)
        ##creating lxml tree from response body
        #tree = html.fromstring(response.text)

        ##Finding all anchor tags in response
        #print tree.xpath('//divass="campaign"]/a/@href'

        #http://ordnet.dk/ddo/ordbog?query=%s
        oxml = tdElems[9].toOuterXml()
        oxml = oxml.replace('<td', '<td colspan="3"')
        tdElems[9].setOuterXml(oxml)


        #oxml = fNames[4].toOuterXml()
        #oxml += '<td rowspan="6"><iframe src="http://ordnet.dk/ddo/ordbog?query=%s" width="800" height="200" scrolling="yes"></iframe></td>' % word
        #fNames[4].setOuterXml(oxml)


    def showGallery(self, word):
        self.galleryManager.buildGallery(word, nThumbs=_nGalleryThumbs)

    def showPronunciationGallery(self, word):
        self.pronunciationManager.buildGallery(word)

    def showIpaGallery(self, word):
        self.ipaManager.buildGallery(word)

    def activate(self):
        self.loadCssStyleSheet()
        self._loadNoteVanilla = self.editor.loadNote
        self.editor.loadNote = wrap(self.editor, Editor.loadNote, loadNoteWithVoc)
        self._setNoteVanilla = self.editor.setNote
        self.editor.setNote = wrap(self.editor, Editor.setNote, setNoteWithVoc)
        self._bridgeVanilla = self.editor.bridge
        self.editor.bridge = wrap(self.editor, Editor.bridge, extendedBridge)
        self.editor.web.setBridge(self.editor.bridge)
        self.editor.addButtonsToTagBar()
        self.editor.web.setLinkHandler(self.ffNoteEditorLinkHandler)
        self.editor.loadNote()

    def deactivate(self):
        self.galleryManager.finalizePreviousSelection()
        self.editor.loadNote = self._loadNoteVanilla
        self.editor.setNote = self._setNoteVanilla
        self.editor.bridge = self._bridgeVanilla
        self.editor.web.setBridge(self.editor.bridge)
        self.editor.ffNoteEditorLinkHandler = ''
        self.editor.loadNote()

    def ffNoteEditorLinkHandler(self, link):
        l = os.path.basename(link)
        if re.match("img[0-9]+", l) is not None:
            self.galleryManager.linkHandler(l)
        elif re.match("sound.*", l) is not None:
            self.pronunciationManager.linkHandler(l)
        else:
            #FIXME: Very bug prone implementation. Change self.iframes to something more robust
            # Manage real web links
            # First try to guess from which IFrame the link comes from by analyzing
            # the destination URL. Open in the same IFrame if the host of the destination link
            # is the same otherwise open is system browser
            linkHandled = False
            for i, childframe in enumerate(self.webMainFrame.childFrames()):
                host = QUrl(link).host()
                if self.iframes[i].find(host) != -1:
                    childframe.setUrl(QUrl(link))
                    linkHandled = True
                    break
            if not linkHandled:
                QDesktopServices.openUrl(QUrl(link))


    def getNotes(self, idxs):
        """
        Return the note ids of the notes corresponding to the browser rows given by idx
        Adapted from aqt.browser.selectedNotes
        """
        return self.mw.col.db.list("""
select distinct nid from cards
where id in %s""" % ids2str(
    [self.browser.model.cards[idx] for idx in idxs]))

    def preload(self, nPreload):
        """ Preload media for the next cards in the browser tableView

        Using the preloading the user can proceed to review/create the next card instantly, without
        waiting for the images, pronunciation and so on to be downloaded.

        A limited number of card is preloaded so that if the user jump far ahead, he still needs
        to wait fo the media to be downloaded.

        #FIXME: Verify the Filter card:1 is active to avoid, otherwise we lose time trying to preload the same note
        and we limit the number of preloaded notes
        """
        self.browser = aqt.dialogs.open("Browser", self.mw)
        #Retrieve row index of card currently selected in the browser. Note that only one row can be selected otherwise the editor
        #would not be visible, so we do need to perform any check on this condition
        selectedRows = self.browser.form.tableView.selectionModel().selectedRows()
        selectedRowIdx = selectedRows[0].row()
        #Generate list of row indexes of the notes to be preloaded and retrieve their ids.
        #Note that if in the browser the filter card:1 is not set in the search bar, on different rows there
        #can be different card of the same note, so we use set() to make the retrieved ids unique
        rowIndexesToBePreloaded = range(selectedRowIdx, selectedRowIdx + nPreload + 1)
        preloadNotesIds = set(self.getNotes(rowIndexesToBePreloaded))
        #We want to keep track of which notes has been preloaded so we save their ids in self.preloadedNotesIds
        currentIds = set(self.preloadedNotesIds)
        newPreloadNotesIds = preloadNotesIds.difference(currentIds)
        newPreloadNotesIds = list(newPreloadNotesIds)
        self.preloadedNotesIds += newPreloadNotesIds
        #Download each note media by spawning new threads
        newPreloadNotes = list()
        wordDownloadList = list()
        for i in range(len(newPreloadNotesIds)):
            newPreloadNotes.append(self.mw.col.getNote(newPreloadNotesIds[i]))
            wordDownloadList.append(newPreloadNotes[i]['Word'])

            thrImg = threading.Thread(target=self.galleryManager.downloadPictures, args=(newPreloadNotes[i]['Word'], newPreloadNotes[i]['Word'], _nGalleryThumbs), kwargs={})
            thrImg.start()

        # Put single string args between [] or it is considered as many args as the length of the string
        thrAudio = threading.Thread(target=self.pronunciationManager.downloadAudios, args=([wordDownloadList]), kwargs={})
        thrAudio.start()

        thrIpa= threading.Thread(target=self.ipaManager.downloadIpas, args=([wordDownloadList]), kwargs={})
        thrIpa.start()

def wrap(instance, old, new, pos='after'):
    "Override an existing function."
    def repl(*args, **kwargs):
        if pos == 'after':
            old(*args, **kwargs)
            return new(*args, **kwargs)
        elif pos == 'before':
            new(*args, **kwargs)
            return old(*args, **kwargs)
        else:
            return new(_old=old, *args, **kwargs)
    return types.MethodType(repl, instance, instance.__class__)

def loadNoteWithVoc(self):
    self.vocDeckBuilder.galleryManager.finalizePreviousSelection()
    self.vocDeckBuilder.showGallery(self.note['Word'])
    self.vocDeckBuilder.showPronunciationGallery(self.note['Word'])
    self.vocDeckBuilder.showIpaGallery(self.note['Word'])
    self.vocDeckBuilder.preload(_nPreload)
    self.vocDeckBuilder.showIFrames(self.note['Word'])

def setNoteWithVoc(self, note, hide=True, focus=False):
    self.vocDeckBuilder.loadCssStyleSheet()

def extendedBridge(self, str):
    ar = str.split(':')
    if ar[1] == 'setpronunciation':
        self.vocDeckBuilder.pronunciationManager.setPronunciation(int(ar[2]))
    elif ar[1] == 'setipa':
        self.vocDeckBuilder.ipaManager.setIpa(ar[2])
