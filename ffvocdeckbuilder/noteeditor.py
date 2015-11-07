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

import anki
from anki import hooks
from anki.utils import ids2str
from aqt.editor import Editor
from gallerymanager import GalleryManager
from pronunciationmanager import PronunciationManager

_galleryCss = """
#normal2, #normal3, #normal4, #normal5 {
    display: none;
}
#gallery {
    margin: 0 auto;
}
#currentimg img {
    height: 130px;
    border: 6px solid #0033FF;
    margin: 6px;
    float: left;
}
#thumbs {
    margin: 0px auto 0px auto;
    float: left;
}
#thumbs img {
    height: 130px;
    border: none;
}
#thumbs a:link, #thumbs a:visited {
    color: #EEE;
    height: 130px;
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

_nPreload = 8

class NoteEditor(object):

    def __init__(self, editor):
        self.editor = editor
        self.mw = self.editor.mw
        self.web = editor.web
        self.webMainFrame = self.web.page().mainFrame()
        self.currentWord = ''
        self.wordUrls = {}
        self.wordThumbs = {}
        #self.nextNotes = list(_nPreload)
        #self.prevNotes = list(_nPreload)
        self.galleryManager = GalleryManager(self.editor, "Bing")
        self.pronunciationManager = PronunciationManager(self.editor, "Forvo")

    def __del__(self):
        #FIXME: Call this destructor explicitly somewhere
        self.galleryManager.finalizePreviousSelection()
        self.galleryManager.__del__()
        self.pronunciationManager.__del__()

    def loadCssStyleSheet(self):
        css = str(self.webMainFrame.findFirstElement('style').toInnerXml())
        css += _galleryCss
        self.webMainFrame.findFirstElement('style').setInnerXml(css)

    def showGallery(self, word):
        self.galleryManager.buildGallery(word, nThumbs=_nPreload)

    def showPronunciationGallery(self, word):
        self.pronunciationManager.buildGallery(word)

    def activate(self):
        self.loadCssStyleSheet()
        self._loadNoteVanilla = self.editor.loadNote
        self.editor.loadNote = wrap(self.editor, Editor.loadNote, loadNoteWithVoc)
        self._setNoteVanilla = self.editor.setNote
        self.editor.setNote = wrap(self.editor, Editor.setNote, setNoteWithVoc)
        self._bridgeVanilla = self.editor.bridge
        self.editor.bridge = wrap(self.editor, Editor.bridge, extendedBridge)
        self.editor.web.setBridge(self.editor.bridge)
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

    def ffNoteEditorLinkHandler(self, l):
        l = os.path.basename(l)
        if re.match("img[0-9]+", l) is not None:
            self.galleryManager.linkHandler(l)
        if re.match("sound.*", l) is not None:
            self.pronunciationManager.linkHandler(l)

    def getNotes(self, idxs):
        """
        Return the note ids of the notes corresponding to the browser rows given by idx
        Adapted from aqt.browser.selectedNotes
        """
        return self.mw.col.db.list("""
select distinct nid from cards
where id in %s""" % ids2str(
    [self.browser.model.cards[idx] for idx in idxs]))

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

def setNoteWithVoc(self, note, hide=True, focus=False):
    self.vocDeckBuilder.loadCssStyleSheet()

def extendedBridge(self, str):
    ar = str.split(':')
    if ar[1] == 'setpronunciation':
        self.vocDeckBuilder.pronunciationManager.setPronunciation(int(ar[2]))
