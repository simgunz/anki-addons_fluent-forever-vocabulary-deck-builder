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
from anki import hooks
from anki.utils import ids2str

import aqt
from aqt import QSettings, QMessageBox
from aqt.editor import Editor

from ffvocdeckbuilder import ffvocdeckbuilder
from ffvocdeckbuilder.gallerymanager import GalleryManager
#from ffvocdeckbuilder.pronunciationmanager import PronunciationManager
from ffvocdeckbuilder.ipamanager import IpaManager

_nPreload = 5
_nGalleryThumbs = 8

class NoteEditor(object):

    def __init__(self, editor):
        self.editor = editor
        self.mw = self.editor.mw
        self.web = editor.web
        self.currentWord = ''
        self.preloadedNotesIds = list()
        self.wordUrls = {}
        self.wordThumbs = {}
        #self.nextNotes = list(_nPreload)
        #self.prevNotes = list(_nPreload)
        self.loadPreferences()
        self.galleryManager = None
        self.pronunciationManager = None
        self.ipaManager = None
        #REENABLE self.galleryManager = GalleryManager(self.editor, self.config, "Bing")
        #REENABLE self.pronunciationManager = PronunciationManager(self.editor, self.config, "Forvo")
        #REENABLE self.ipaManager = IpaManager(self.editor, self.config)
        self.isActive = False
        self.htmlInjected = False

    def __del__(self):
        #FIXME: Call this destructor explicitly somewhere
        if self.galleryManager:
            self.galleryManager.finalizePreviousSelection()
            self.galleryManager.__del__()
        if self.pronunciationManager:
            self.pronunciationManager.__del__()

    def loadPreferences(self):
        #Load user config
        self.user = self.mw.pm.name
        config = QSettings('FFVDB')
        configDict = config.value(self.user)
        if not configDict:
            browser = aqt.dialogs.open("Browser", self.editor) #I don't know better way to retrieve the instance of the browser
            QMessageBox.warning(browser,
                'Missing configuration', 'This is the first time fluent forever vocabulary deck builder is run for the current user.'
                'The preference dialog will now open.')
            ffvocdeckbuilder.openPreferencesDialog(browser)
            config.sync()
            configDict = config.value(self.user)
        self.config = configDict
        
    def loadCssStyleSheet(self):
        webDir = os.path.join(self.mw.pm.addonFolder(), 'ffvocdeckbuilder', 'web', 'noteeditor.css')
        with open(webDir, 'r') as f:
            csssource = ' '.join(f.readlines()).replace('\n', '') #FIXME: How to preserve newlines?
        s = '$("head").append("<style>{0}</style>")'.format(csssource)
        self.web.eval(s)

    def showGallery(self, word):
        self.galleryManager.buildGallery(word, nThumbs=_nGalleryThumbs)

    def showPronunciationGallery(self, word):
        self.pronunciationManager.buildGallery(word)

    def showIpaGallery(self, word):
        self.ipaManager.buildGallery(word)

    def activate(self, html):
        if not self.htmlInjected:
            self.loadCssStyleSheet(html)
            self.htmlInjected = True
        self._loadNoteVanilla = self.editor.loadNote
        self.editor.loadNote = wrap(self.editor, Editor.loadNote, loadNoteWithVoc)
        self._setNoteVanilla = self.editor.setNote
        self.editor.setNote = wrap(self.editor, Editor.setNote, setNoteWithVoc)
        self._bridgeVanilla = self.editor.onBridgeCmd
        self.editor.onBridgeCmd = wrap(self.editor, Editor.onBridgeCmd, extendedBridge)
        #REENABLE self.editor.web.setBridge(self.editor.bridge)
        self.editor.addButtonsToTagBar()
        #REENABLE self.editor.web.setLinkHandler(self.ffNoteEditorLinkHandler)
        self.editor.loadNote()
        self.isActive = True

    def deactivate(self):
        if self.galleryManager:
            self.galleryManager.finalizePreviousSelection()
        self.editor.loadNote = self._loadNoteVanilla
        self.editor.setNote = self._setNoteVanilla
        self.editor.bridge = self._bridgeVanilla
        #REENABLE self.editor.web.setBridge(self.editor.bridge)
        #REENABLE self.editor.ffNoteEditorLinkHandler = ''
        self.editor.loadNote()
        self.isActive = False

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
        return self.mw.col.db.list(u"""
select distinct nid from cards
where id in {0}""".format(ids2str(
    [self.browser.model.cards[idx] for idx in idxs])))

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
        #Limit number of notes to be preloaded if there are not enough in the browser after the current one
        nPreloadEffective = min(self.browser.model.rowCount(None) - selectedRowIdx - 1, nPreload)
        #NOTE: The number of NOTES preloaded may be lower than nPreloadEffective in case more than one card corresponding to
        #the same note is among the ones to be preloaded
        rowIndexesToBePreloaded = range(selectedRowIdx + 1, selectedRowIdx + nPreloadEffective + 1)
        preloadNotesIds = set(self.getNotes(rowIndexesToBePreloaded))
        #We want to keep track of which notes has been preloaded so we save their ids in self.preloadedNotesIds
        currentIds = set(self.preloadedNotesIds)
        newPreloadNotesIds = preloadNotesIds.difference(currentIds)
        newPreloadNotesIds = list(newPreloadNotesIds)
        self.preloadedNotesIds += newPreloadNotesIds
        
        if self.galleryManager:
            #Download each note media by spawning new threads
            newPreloadNotes = list()
            wordDownloadList = list()
            for i in range(len(newPreloadNotesIds)):
                newPreloadNotes.append(self.mw.col.getNote(newPreloadNotesIds[i]))
                wordDownloadList.append(newPreloadNotes[i]['Word'])

                thrImg = threading.Thread(target=self.galleryManager.downloadPictures, args=(newPreloadNotes[i]['Word'], newPreloadNotes[i]['Word'], _nGalleryThumbs), kwargs={})
                thrImg.start()

        if self.pronunciationManager:
            # Put single string args between [] or it is considered as many args as the length of the string
            thrAudio = threading.Thread(target=self.pronunciationManager.downloadAudios, args=([wordDownloadList]), kwargs={})
            thrAudio.start()

        if self.ipaManager:
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
    return types.MethodType(repl, instance)

def loadNoteWithVoc(self):
    if self.vocDeckBuilder.galleryManager:
        self.vocDeckBuilder.galleryManager.finalizePreviousSelection()
        self.vocDeckBuilder.showGallery(self.note['Word'])
    if self.vocDeckBuilder.pronunciationManager:
        self.vocDeckBuilder.showPronunciationGallery(self.note['Word'])
    if self.vocDeckBuilder.ipaManager:
        self.vocDeckBuilder.showIpaGallery(self.note['Word'])
    #self.vocDeckBuilder.preload(_nPreload)

def setNoteWithVoc(self, note, hide=True, focus=False):
    self.vocDeckBuilder.loadCssStyleSheet()

def extendedBridge(self, str):
    ar = str.split(':')
    if ar[1] == 'setpronunciation':
        self.vocDeckBuilder.pronunciationManager.setPronunciation(int(ar[2]))
    elif ar[1] == 'setipa':
        self.vocDeckBuilder.ipaManager.setIpa(ar[2])
