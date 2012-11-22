#!/usr/bin/env python

# Copyright 2012 Akeda Bagus.
#
# This file partial.py is used to generate html files
# of the template-buku.
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

"""Module to construct partial templates
"""

from pystache import TemplateSpec


class Layout(TemplateSpec):

	def __init__(self, renderer, book=None, chapter=None, nav=None):
		"""Construct an instance.
		"""
		self.renderer = renderer
		self.book = book
		self.chapter = chapter
		self.nav = nav

	def book(self):
		return self.book

	def chapter(self):
		return self.chapter

	def nav(self):
		return self.nav
