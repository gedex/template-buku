#!/usr/bin/env python

# Copyright 2012 Akeda Bagus.
#
# This file build.py is used to generate build files (html, pdf, etc)
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

"""The main build files generator.
"""


import argparse
import errno
import os
import re
import shutil
import yaml

from layout import Layout
from lxml.html import fragments_fromstring
from markdown2 import markdown_path as md2html
from pystache import Renderer


APPENDIX_DIR = './appendix'
CHAPTERS_DIR  = './chapters'
CHAPTER_TITLES = {} # Key is chapter's filename found in config.yaml and val is the title
NAV_TAGS = ('h2', 'h3', 'h4', 'h5', 'h6')
TARGET_BUILD = './build'
TEMPLATES_DIR = './templates'


RENDERER = Renderer(search_dirs=TEMPLATES_DIR, file_extension='html')


def build():
  parser = argparse.ArgumentParser(description='Build arguments.')
  parser.add_argument('--prefix-chapter-number', action='store_true',
                      help='Generate the chapters toc with prefix number')

  args = parser.parse_args()

  stream = file('./config.yaml', 'r')
  config = yaml.load(stream)

  if not os.path.exists(TARGET_BUILD):
    os.makedirs(TARGET_BUILD)

  chapter_no = 1
  for ch in config['chapters']:
    if os.path.exists(os.path.join(CHAPTERS_DIR, "%s.%s" % (ch, 'md'))):
      if args.prefix_chapter_number:
        build_html_chapter(ch, config=config, chapter_no=chapter_no)
        chapter_no = chapter_no + 1
      else:
        build_html_chapter(ch, config=config)


  # Copy static assets
  static_dir = os.path.join(TEMPLATES_DIR, 'static')
  target_dir = os.path.join(TARGET_BUILD, 'static')
  if os.path.isdir(target_dir):
    shutil.rmtree(target_dir)

  try:
    shutil.copytree(static_dir, target_dir)
  except OSError as exc:
    if exc.errno == errno.ENOTDIR:
      shutil.copy(static_dir, target_dir)
    else: raise


def build_html_chapter(chapter, config=None, chapter_no=None):
  """Build a single-full-page-html chapter
  """

  html, nodes = get_html_chapter(chapter)

  # Get the nav for current chapter
  current_nav = get_nav_from_html_elements(nodes, chapter_no=chapter_no)

  # Merge current nav for chapters nav
  nav = '<ol id="chapter-nav" class="nav">'

  if chapter_no:
    chapter_no = 1

  for ch in config['chapters']:
    # Search for h1 in nodes, otherwise use filename
    ch_title = getattr(CHAPTER_TITLES, ch, None)

    if (ch == chapter):
      if not ch_title:
        ch_title = get_chapter_title(nodes, filename=chapter, chapter_no=chapter_no)

      nav = ''.join([nav, open_li_a(ch_title, href=ch+'.html#book', id_li="current-chapter"), current_nav, close_li()])
    else:
      if not ch_title:
        _html, _nodes = get_html_chapter(ch)
        ch_title = get_chapter_title(_nodes, filename=ch, chapter_no=chapter_no)

      nav = ''.join([nav, open_li_a(ch_title, href=ch+'.html#book'), close_li()])

    CHAPTER_TITLES[chapter] = ch_title
    if chapter_no:
      chapter_no = chapter_no + 1

  nav = ''.join([nav, '</ol>'])

  # Render the mustache
  layout = get_layout_instance(chapter, book=config, chapter=html, nav=nav)
  rendered = RENDERER.render(layout)

  # Writes the resulted html from markdown
  html_chapter = open(os.path.join(TARGET_BUILD, "%s.%s" % (chapter, 'html')),'w')
  html_chapter.write(rendered)
  html_chapter.close()


def get_html_chapter(chapter):
  """Reads markdown's chapter file and converts it to html and DOM representation
  """

  md_filename = os.path.join(CHAPTERS_DIR, "%s.%s" % (chapter, 'md'))
  html = md2html(md_filename, extras=["header-ids", "fenced-code-blocks"])

  # Convert html fragments to node element
  nodes = fragments_fromstring(html)

  return (html, nodes)


def get_chapter_title(nodes, filename=None, chapter_no=None):
  """Get chapter title from html elements that's parsed by fragments_fromstring

  If no h1 found in elements use chapter's filename instead.
  """

  title = None

  for node in nodes:
    if node.tag == 'h1':
      title = node.text

  # Fallback to use filename as a title
  if not title:
    splitted = filename.split('_') # Assuming each chapters is underscore-separated-word named
    if len(splitted) <= 1:
      title = filename
    else:
      title = ' '.join(splitted)

  if chapter_no:
    title = "%d. %s" % (chapter_no, title)

  return title


def get_nav_from_html_elements(elements, chapter_no=None):

  nodes = [el for el in elements if el.tag in NAV_TAGS]
  nodes.reverse()

  # Header stacks to keep how depth indent
  hstack = []

  # Stringify first header into list
  header = nodes.pop()

  if chapter_no:
    chapter_title = "%d. %s" % (chapter_no, header.text)
  else:
    chapter_title = header.text

  nav = '<ol><li><a href="#%s">%s</a>' % (header.get('id'), chapter_title)

  # Append header level, in numeric, to hstack
  hstack.append(int(header.tag[1]))

  while nodes:
    node = nodes.pop()
    header = int(node.tag[1])

    if chapter_no:
      section_title = "%d. %s" % (chapter_no, node.text)
    else:
      section_title = node.text

    if header < hstack[-1]:   # Lower than means the header is more important.
                              # This means `h1` is more important than `h2`
      while hstack and header < hstack.pop():
        nav = ''.join([nav, close_li_ol()]) # close li and ol until met the right indent

      nav = ''.join([nav, close_li(), open_li_a(section_title, href=node.get('id'))])

      hstack.append(header)

    elif header > hstack[-1]: # Greater than means the header is less important

      nav = ''.join([nav, open_ol(), open_li_a(section_title, href=node.get('id'))])

      hstack.append(header)

    else:                     # Same header level
      nav = ''.join([nav, close_li(), open_li_a(section_title, href=node.get('id'))])

  # Close remaining unclosed header level in hstack
  while hstack:
    nav = ''.join([nav, close_li_ol()])
    hstack.pop()

  return nav


def close_ol_li():
  return '</ol></li>'


def close_li_ol():
  return '</li></ol>'


def close_li():
  return '</li>'


def open_ol():
  return '<ol>'


def open_li_a(text, href=None, id_li=None):
  if href is not None:
    filename, ext = os.path.splitext(href)
    if not ext:
      href = '#' + filename
  else:
    href = '#'

  if id_li:
    id_li= ' id="%s"' % id_li
  else:
    id_li = ''

  return '<li%s><a href="%s">%s</a>' % (id_li, href, text)


def get_layout_instance(classname, book=None, chapter=None, nav=None):

  instance = Layout(renderer=RENDERER, book=book, chapter=chapter, nav=nav)

  return instance


if __name__ == '__main__':
  build()
