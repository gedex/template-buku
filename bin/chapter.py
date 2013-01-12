#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012 Akeda Bagus.
#
# This file, chapter.py, is used to generate html files
# of chapters contained in config.yaml.
#
# template-buku is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# template-buku is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with template-buku. If not, see <http://www.gnu.org/licenses/>.
#

"""Module to construct chapter template
"""

from pystache import TemplateSpec


class Chapter(TemplateSpec):
    def __init__(self, renderer, book=None, chapter=None, chapter_nav=None):
        """Construct an instance.
        """
        self.renderer = renderer
        self.book = book
        self.chapter = chapter
        self.chapter_nav = chapter_nav

    def book(self):
        """Book information, comes from config.yaml
        """
        return self.book

    def chapter(self):
        """Chapter content
        """
        return self.chapter

    def chapter_nav(self):
        """Chapter navigation (prev, toc, next)
        """
        return self.chapter_nav
