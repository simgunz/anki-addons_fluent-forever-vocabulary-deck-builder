# -*- coding: utf-8 -*-
#########################################################################
# Copyright (C) 2015 by Simone Gaiarin <simgunz@gmail.com>              #
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

from extmodules.tempdir import tempdir
from extmodules.downloadaudio.downloaders import forvo


class PronunciationManager:
    def __init__(self, editor, provider):
        self.editor = editor
        self.webMainFrame = self.editor.web.page().mainFrame()
        self.tempDir = tempdir.TempDir()
        self.provider = provider.lower()
        if self.provider == "forvo":
            self.servant = forvo.ForvoDownloader()

    def __del__(self):
        self.servant.__del__()
        self.tempDir.dissolve()
