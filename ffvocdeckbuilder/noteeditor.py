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
import anki
from anki import hooks
from aqt.editor import Editor

_exRootPath="/media/dataHD/development/anki/anki-addons_fluent-forever-vocabulary-deck-builder/_anki-addons_fluent-forever-vocabulary-deck-builder/ffvocdeckbuilder"

_galleryHtml = """
<div id="gallery">
    <div id="currentimg">
        <img src="{_exRootPath}/images/no_image.png"/>
    </div>
    <div id="thumbs">
        <a href="javascript: changeImage(1);"><img src="{_exRootPath}/images/IMGNAME1.png" alt="" /></a>
        <a href="javascript: changeImage(2);"><img src="{_exRootPath}/images/IMGNAME2.png" alt="" /></a>
        <a href="javascript: changeImage(3);"><img src="{_exRootPath}/images/IMGNAME3.png" alt="" /></a>
        <a href="javascript: changeImage(4);"><img src="{_exRootPath}/images/IMGNAME4.png" alt="" /></a>
        <a href="javascript: changeImage(5);"><img src="{_exRootPath}/images/IMGNAME5.png" alt="" /></a>
    </div>
</div>
""".format(**locals())

class NoteEditor(object):

    def __init__(self, editor):
        self.editor = editor
        self.web = editor.web
        self.webMainFrame = self.web.page().mainFrame()

    def showGallery(self, word):
        gallery = _galleryHtml.replace('IMGNAME', word.lower())
        #FIXME: Use BeautifulSoup?
        self.webMainFrame.findFirstElement("#f3").setOuterXml(gallery)

    def activate(self):
        self._loadNoteVanilla = self.editor.loadNote
        self.editor.loadNote = wrap(self.editor, Editor.loadNote, loadNoteWithVoc)
        self._setNoteVanilla = self.editor.setNote
        self.editor.setNote = wrap(self.editor, Editor.setNote, setNoteWithVoc)
        self.editor.loadNote()

    def deactivate(self):
        self.editor.loadNote = self._loadNoteVanilla
        self.editor.setNote = self._setNoteVanilla
        self.editor.loadNote()

def wrap(instance, old, new, pos="after"):
    "Override an existing function."
    def repl(*args, **kwargs):
        if pos == "after":
            old(*args, **kwargs)
            return new(*args, **kwargs)
        elif pos == "before":
            new(*args, **kwargs)
            return old(*args, **kwargs)
        else:
            return new(_old=old, *args, **kwargs)
    return types.MethodType(repl, instance, instance.__class__)

def loadNoteWithVoc(self):
    self.vocDeckBuilder.showGallery(self.note['Word'])

def setNoteWithVoc(self, note, hide=True, focus=False):
    pass
