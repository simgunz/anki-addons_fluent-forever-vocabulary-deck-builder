# -*- coding: utf-8 -*-
# Copyright: Simone Gaiarin <simgunz@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/licenses/gpl.html

from aqt.qt import *
#FIXME: Is uic present in default installation?
from PyQt4 import uic

class Preferences(QDialog):

    def __init__(self, mw):
        QDialog.__init__(self, mw)
        self.mw = mw
        #Dynamically loads the ui
        uic.loadUi(mw.pm.addonFolder() + '/ffvocdeckbuilder/ui/preferences.ui', self);
        #These two instructions run the dialog as modal dialog
        self.loadLanguageCodes()
        languages = sorted(self.languageCodes.values())
        self.cbPreferredLanguage.addItems(languages)
        self.cbSecondaryLanguage.addItems(languages)
        self.setModal(True)
        self.exec_()

    def accept(self):
        self.done(0)

    def reject(self):
        self.done(1)

    def loadLanguageCodes(self):
        self.languageCodes = {}
        fileName = u"{0}/ffvocdeckbuilder/files/iso-639-1-language-codes" \
            .format(self.mw.pm.addonFolder())
        with open(fileName) as f:
            for line in f:
                (key, val) = line.split(',')
                self.languageCodes[key] = val.rstrip('\n')
