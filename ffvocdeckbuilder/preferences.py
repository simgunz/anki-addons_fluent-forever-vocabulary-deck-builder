# -*- coding: utf-8 -*-
# Copyright: Simone Gaiarin <simgunz@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/licenses/gpl.html

from aqt import QDialog, QSettings

#FIXME: Is uic present in default installation?
from PyQt5 import uic

class Preferences(QDialog):

    def __init__(self, mw):
        QDialog.__init__(self, mw)
        self.mw = mw
        #Dynamically loads the ui
        uic.loadUi(mw.pm.addonFolder() + '/ffvocdeckbuilder/ui/preferences.ui', self);
        #These two instructions run the dialog as modal dialog
        self.loadLanguageCodes()
        languages = sorted(self.languageCodesForward.values())
        self.cbPreferredLanguage.addItems(languages)
        self.cbSecondaryLanguage.addItems(languages)
        self.setModal(True) #Shade the parent window and prevent interaction with it

        #Load user config
        self.user = self.mw.pm.name
        self.config = QSettings('FFVDB')
        configDict = self.config.value(self.user)
        if configDict:
            self.leApiForvo.setText(configDict['APIs']['forvo'])
            self.leApiBing.setText(configDict['APIs']['bing'])
            self.cbPreferredLanguage.lineEdit().setText(self.languageCodesForward[configDict['Languages']['Primary']])
            self.cbSecondaryLanguage.lineEdit().setText(self.languageCodesForward[configDict['Languages']['Secondary']])
        self.exec_()

    def accept(self):
        configDict = {}
        configDict['APIs'] = {}
        configDict['APIs']['forvo'] = self.leApiForvo.text()
        configDict['APIs']['bing'] = self.leApiBing.text()
        configDict['Languages'] = {}
        configDict['Languages']['Primary'] = self.languageCodesBackward[self.cbPreferredLanguage.currentText()]
        configDict['Languages']['Secondary'] = self.languageCodesBackward[self.cbSecondaryLanguage.currentText()]
        self.config.setValue(self.user, configDict)
        self.done(0)

    def reject(self):
        self.done(1)

    def loadLanguageCodes(self):
        self.languageCodesForward = {}
        self.languageCodesBackward = {}
        fileName = u"{0}/ffvocdeckbuilder/files/iso-639-1-language-codes" \
            .format(self.mw.pm.addonFolder())
        with open(fileName) as f:
            for line in f:
                (code, language) = line.split(',')
                code = code.rstrip('\n')
                self.languageCodesForward[code] = language
                self.languageCodesBackward[language] = code
