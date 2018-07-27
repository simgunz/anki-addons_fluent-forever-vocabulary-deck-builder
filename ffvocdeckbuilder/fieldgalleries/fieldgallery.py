import os

from abc import ABC, abstractmethod

from aqt import QTemporaryDir

class FieldGallery(ABC):
    
    def __init__(self, name):
        self.name = name
        self._temporaryDirectory = None
        self.loadJS()
        self.loadCSS()
    
    @abstractmethod
    def showGallery(self):
        pass
    
    @abstractmethod
    def onBridgeCmd(self, cmd):
        pass
    
    def _loadTag(self, tagtype):
        if tagtype == "css":
            tagname = "style"
        elif tagtype == "js":
            tagname = "script"
            
        jsfile = os.path.join(self.editor.mw.pm.addonFolder(), 'ffvocdeckbuilder', 'web', 'gallery_{0}.{1}'.format(self.name, tagtype))
        if not os.access(jsfile, os.R_OK):
            return
        
        with open(jsfile, 'r') as f:
            tagfile = ' '.join(f.readlines()).replace('\n', '') #FIXME: How to preserve newlines?
        s = '''$('head').append('<{1}>{0}</{1}>')'''.format(tagfile, tagname)
        self.editor.web.eval(s)
      
    def _insertGalleryInHTML(self, field_id, gallery_div):
        self.editor.web.eval('''$('{0}').replaceWith('{1}')'''.format(field_id, gallery_div))
        
    def _tempDir(self):
        if self._temporaryDirectory is None:
            self._temporaryDirectory = QTemporaryDir()
        if self._temporaryDirectory.isValid():
            return self._temporaryDirectory.path()
        
    def cleanUp(self):
        if self._temporaryDirectory is not None:
            self._temporaryDirectory.remove()
            
    def loadJS(self):
        self._loadTag("js")
    
    def loadCSS(self):
        self._loadTag("css")
        
