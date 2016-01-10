# -*- coding: utf-8 -*-
# Copyright: Simone Gaiarin <simgunz@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/licenses/gpl.html

from aqt.qt import *
#FIXME: Is uic present in default installation?
from PyQt4 import uic

class Preferences(QDialog):

    def __init__(self, mw):
        QDialog.__init__(self, mw)
        #Dynamically loads the ui
        uic.loadUi(mw.pm.addonFolder() + '/ffvocdeckbuilder/ui/preferences.ui', self);
        #These two instructions run the dialog as modal dialog
        self.setModal(True)
        self.exec_()

    def accept(self):
        self.done(0)

    def reject(self):
        self.done(1)
