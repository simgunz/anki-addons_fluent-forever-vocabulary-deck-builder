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
import itertools
import types
import os
import re
import threading
from collections import OrderedDict
 
import anki
from anki import hooks
from anki.utils import ids2str

import aqt
from aqt import QSettings, QMessageBox
from aqt.editor import Editor

from ffvocdeckbuilder import ffvocdeckbuilder
from .fieldgalleries.ipagallery import IpaGallery
from .fieldgalleries.pronunciationgallery import PronunciationGallery

_nPreload = 5
_nGalleryThumbs = 8

class NoteEditor(object):

    def __init__(self, editor):
        self.editor = editor
        self.mw = self.editor.mw
        self.browser = aqt.dialogs.open("Browser", self.mw)
        self.web = editor.web
        self.currentWord = ''
        self.loadedWords = set()
        self.preloaderRunningThreads = dict()
        #self.nextNotes = list(_nPreload)
        #self.prevNotes = list(_nPreload)
        self.isActive = False
        self.loadPreferences()
        self.initFieldGalleries()

    def cleanUp(self):
        for gallery in self.fieldGalleries.values():
            gallery.cleanUp()

    def initFieldGalleries(self):
        self.fieldGalleries = dict()
        self.fieldGalleries['pronunciation'] = PronunciationGallery(self.editor, self.config, "forvo")
        self.fieldGalleries['ipa'] = IpaGallery(self.editor, self.config)        
    
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

    def waitForPreloader(self, word):
        if word in self.preloaderRunningThreads:
            for t in self.preloaderRunningThreads[word]:
                t.join()
            del self.preloaderRunningThreads[word]
    
    def showFieldGalleries(self, word):
        self.waitForPreloader(word)
        for gallery in self.fieldGalleries.values():
            gallery.showGallery(word)
        self.loadedWords.add(word)

    def activate(self):
        # FIXME: Avoid calling wrap every time, defining new repl methods, just call it once and store repl somewhere
        self.editor.loadNote = wrap(self.editor, Editor.loadNote, loadNoteWithVoc)
        self.editor.onBridgeCmd = wrap(self.editor, Editor.onBridgeCmd, extendedBridge)
        self.web.onBridgeCmd = self.editor.onBridgeCmd
        self.editor.addButtonsToTagBar()
        self.editor.loadNoteKeepingFocus()
        self.isActive = True

    def deactivate(self):
        #if self.galleryManager:
            #self.galleryManager.finalizePreviousSelection()
        self.editor.loadNote = types.MethodType(Editor.loadNote, self.editor)
        self.editor.onBridgeCmd = types.MethodType(Editor.onBridgeCmd, self.editor)
        self.web.onBridgeCmd = self.editor.onBridgeCmd
        self.editor.loadNoteKeepingFocus()
        self.isActive = False

    def getNoteIds(self, idxs):
        """
        Return the note ids of the notes corresponding to the browser rows given by idx
        maintaining the order of idxs. 
        Adapted from aqt.browser.selectedNotes
        """
        # OPTIMIZE: Is there a way to perform a single query to the DB while retrieving the note ids sorted by idxs?
        strids = [str(self.browser.model.cards[idx]) for idx in idxs]
        noteIds = [self.mw.col.db.list('select nid from cards where id is {0}'.format(id)) for id in strids]
        noteIds = list(itertools.chain.from_iterable(noteIds))
        noteIds = list(OrderedDict.fromkeys(noteIds)) # Remove duplicates preserving order
        return noteIds
    
    def preload(self, nNotesToPreload):
        """ Preload media for the next cards in the browser tableView

        Using the preloading the user can proceed to review/create the next card instantly, without
        waiting for the images, pronunciation and so on to be downloaded.
        """
            
        # Multiple cards corresponding to the same note can be shown in the browser, so we fetch
        # MAXCARDSPERNOTE as many cards as the notes to preload to be sure to fetch enough notes.
        # Then we keep only the number of notes to preload.
        MAXCARDSPERNOTE = 10
        selectedRowIdx = self.browser.form.tableView.selectionModel().selectedRows()[0].row()
        nAvailableCardsAfterCurrent = self.browser.model.rowCount(None) - selectedRowIdx - 1
        nCardsToLookup = min(nAvailableCardsAfterCurrent, nNotesToPreload*MAXCARDSPERNOTE)
        rowIndexesToLookup = range(selectedRowIdx + 1, selectedRowIdx + nCardsToLookup + 1)
        preloadNoteIds = self.getNoteIds(rowIndexesToLookup)[:_nPreload]
        wordDownloadList = [self.mw.col.getNote(noteId)['Word'] for noteId in preloadNoteIds 
                            if self.mw.col.getNote(noteId)['Word'] not in self.loadedWords]
        
        # We want to keep track of which notes has been loaded to span less threads 
        self.loadedWords |= set(wordDownloadList)
        
        for word in wordDownloadList:
            self.preloaderRunningThreads[word] = list()
            for gallery in self.fieldGalleries.values():
                thread = threading.Thread(target=gallery.download, args=([word]), kwargs={})
                thread.start()
                self.preloaderRunningThreads[word].append(thread)

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

def loadNoteWithVoc(self, focusTo=None):
    #if self.vocDeckBuilder.galleryManager:
        #self.vocDeckBuilder.galleryManager.finalizePreviousSelection()
    self.vocDeckBuilder.showFieldGalleries(self.note['Word'])
    self.vocDeckBuilder.preload(_nPreload)

def extendedBridge(self, cmd):
    if not cmd.startswith("ffvdb"):
        return
    (_, galleryid, fieldcmd) = tuple(cmd.split(':'))
    self.vocDeckBuilder.fieldGalleries[galleryid].onBridgeCmd(fieldcmd)
