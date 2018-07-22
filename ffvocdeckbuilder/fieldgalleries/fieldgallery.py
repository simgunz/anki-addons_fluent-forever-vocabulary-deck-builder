import os

from abc import ABC, abstractmethod
 
class FieldGallery(ABC):
 
    def __init__(self, name):
        self.name = name
        self.loadJS()
        self.loadCSS()
    
    @abstractmethod
    def showGallery(self):
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
        
    def loadJS(self):
        self._loadTag("js")
    
    def loadCSS(self):
        self._loadTag("css")
        
