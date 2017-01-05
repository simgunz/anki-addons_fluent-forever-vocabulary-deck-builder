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

import os
import pdb

from bs4 import BeautifulSoup

from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction

from anki import hooks

from aqt import mw, editor, browser

from . import preferences
from .noteeditor import NoteEditor

iconsDir = os.path.join(mw.pm.addonFolder(), 'ffvocdeckbuilder', 'icons')


#EDITOR
def toggleVocabularyBuilderView(self):
    if not self.vocDeckBuilder:
        self.vocDeckBuilder = NoteEditor(self)
        self.vocDeckBuilder.isActive = False
    if not self.vocDeckBuilder.isActive:
        self.vocDeckBuilder.activate()
        self.vocDeckBuilder.isActive = True
    else:
        self.vocDeckBuilder.deactivate()
        self.vocDeckBuilder.isActive = False

def onSetupEditorButtons(topbuts):
    """Add an a button to the editor to activate the vocabulary deck building
    mode.
    """
    soup = BeautifulSoup(topbuts, 'html.parser')
    topbutsr = soup.find('div', id='topbutsright')
    ffbtn = soup.new_tag('button', tabindex=-1, type="button", onclick="pycmd('ffvoc');return false;", **{'class': 'linkb'})
    imgpath = os.path.join(iconsDir, 'dictionary.png')
    ffbtnimg = soup.new_tag('img', src=imgpath, **{'class': 'topbut'})
    ffbtn.append(ffbtnimg)
    topbutsr.append(ffbtn)
    return soup.prettify()

def enableDeckBuilderButton(self, val=True):
    """Disable the editor button when the note type is not 'FF basic vocabulary'
    """
    if self.note:
        if self.note.model()['name'] == "FF basic vocabulary":
            self._buttons["ffvocdeckbuilder"].setEnabled(True)
        else:
            self._buttons["ffvocdeckbuilder"].setEnabled(False)

def addButtonsToTagBar(self):
    from aqt.qt import QPushButton, QGroupBox
    btnPrev = QPushButton("Previous")
    btnNext = QPushButton("Next")
    #The tag groupbox
    gb = self.widget.findChild(QGroupBox)
    ly = gb.layout()
    ly.addWidget(btnPrev, 1, 2)
    ly.addWidget(btnNext, 1, 3)

    browser = self.parentWindow
    btnPrev.clicked.connect(browser.onPreviousCard)
    btnNext.clicked.connect(browser.onNextCard)

#BROWSER
def closeEvent(self, event):
    if self.editor.vocDeckBuilder:
        self.editor.vocDeckBuilder.__del__()

#LOCAL
def config_menu():
    """
    Adds a menu item to the Tools menu in Anki's main window for
    launching the configuration dialog.
    """
    preferencesAction = QAction(mw)
    mw.form.menuTools.addAction(preferencesAction)
    preferencesAction.setText(_(u"FFVDB.."))
    preferencesAction.triggered.connect(openPreferencesDialog)

def openPreferencesDialog():
    #Creates and show the preferences dialog
    preferences.Preferences(mw)

hooks.addHook("setupEditorButtons", onSetupEditorButtons)
editor.Editor._links['ffvoc'] = toggleVocabularyBuilderView

editor.Editor.enableButtons = hooks.wrap(
    editor.Editor.enableButtons, enableDeckBuilderButton)

editor.Editor.vocDeckBuilder = None

editor.Editor.addButtonsToTagBar = addButtonsToTagBar

browser.Browser.closeEvent = hooks.wrap(
    browser.Browser.closeEvent, closeEvent, "before")

#Add action to open preferences dialog
config_menu()
