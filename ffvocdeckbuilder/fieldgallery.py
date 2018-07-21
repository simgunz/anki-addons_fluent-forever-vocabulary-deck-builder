import os

from abc import ABC, abstractmethod
 
class FieldGallery(ABC):
 
    def __init__(self, name):
        self.name = name
        self.loadJS()
        self.loadCSS()
    
    @abstractmethod
    def buildGallery(self):
        pass
    
    def loadTag(self, tagtype):
        pass
        
    def loadJS(self):
        self.loadTag("js")
    
    def loadCSS(self):
        self.loadTag("css")
        
