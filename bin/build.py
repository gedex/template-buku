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


import errno
import os
import shutil
import yaml

from chapter import Chapter
from cover import Cover
from lxml.html import fragments_fromstring
from lxml.html import tostring as to_html_string
from markdown2 import markdown_path as md2html
from pystache import Renderer
from toc import Toc


CHAPTERS_DIR  = './chapters'
CHAPTER_NO_BEFORE = 'Chapter'
CHAPTER_NO_AFTER = ':'
CHAPTER_HEADINGS = ('h2', 'h3', 'h4', 'h5', 'h6')
TARGET_BUILD = './build'
TEMPLATES_DIR = './templates'


RENDERER = Renderer(search_dirs=TEMPLATES_DIR, file_extension='html')


def build():

  stream = file('./config.yaml', 'r')
  config = yaml.load(stream)

  if not os.path.exists(TARGET_BUILD):
    os.makedirs(TARGET_BUILD)

  # Cover page
  build_cover_book(config=config)

  # Build toc page
  build_html_toc(config=config)

  # Build chapter in Markdown file into html file
  for idx, chapter in enumerate(config['chapters']):
    chapter_nav = {'prev': 'toc.html', 'next': None}

    # HTML file of previous chapter
    if idx:
      chapter_nav['prev'] = "%s.html#chapter" % config['chapters'][idx-1]

    # HTML file of next chapter
    if idx < (len(config['chapters'])-1):
      chapter_nav['next'] = "%s.html#chapter" % config['chapters'][idx+1]

    chapter_nav['toc'] = "toc.html"

    if os.path.exists(os.path.join(CHAPTERS_DIR, "%s.%s" % (chapter, 'md'))):
      build_html_chapter(chapter, config=config, chapter_no=idx+1, chapter_nav=chapter_nav)

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


def build_cover_book(config=None):
  """Build cover page of the book
  """

  layout = get_cover_layout(book=config)
  rendered = RENDERER.render(layout)

  # Writes to html file
  cover = open(os.path.join(TARGET_BUILD, "cover.html"), 'w')
  cover.write(rendered)
  cover.close()


def build_html_toc(config=None):
  """Build table of content page
  """

  toc = '<ol id="toc-list">'

  for idx, chapter in enumerate(config['chapters']):
    # html string and nodes presentation of current chapter
    html, nodes = get_html_chapter(chapter)

    chapter_title = "%s %d %s %s" % (CHAPTER_NO_BEFORE, idx+1,
                                     CHAPTER_NO_AFTER,
                                     get_chapter_title(nodes, filename=chapter))

    chapter_file = "%s.html" % chapter

    chapter_structure = get_chapter_structure(nodes,
                                              chapter_no=idx+1,
                                              chapter_file=chapter_file)

    toc = ''.join([toc, open_li_a(chapter_title, href="%s#chapter" % chapter_file),
                  chapter_structure, close_li()])

  toc = ''.join([toc, '</ol>'])

  layout = get_toc_layout(book=config, toc=toc)
  rendered = RENDERER.render(layout)

  # Writes toc to html file
  toc = open(os.path.join(TARGET_BUILD, "toc.html"), 'w')
  toc.write(rendered)
  toc.close()


def build_html_chapter(chapter, config=None, chapter_no=None, chapter_nav=None):
  """Build a single-page-html chapter
  """

  html, nodes = get_html_chapter(chapter)

  html = prefix_chapter_title_with_chapter_no(html, chapter_no=chapter_no)

  # Render the mustache
  layout = get_chapter_layout(book=config, chapter=html, chapter_nav=chapter_nav)
  rendered = RENDERER.render(layout)

  # Writes the resulted html from markdown
  html_chapter = open(os.path.join(TARGET_BUILD, "%s.html" % chapter),'w')
  html_chapter.write(rendered)
  html_chapter.close()


def get_html_chapter(chapter):
  """Reads markdown's chapter file and converts it to html and DOM representation
  """

  md_filename = os.path.join(CHAPTERS_DIR, "%s.md" % chapter)
  if not os.path.exists(md_filename):
    return (None, None)

  html = md2html(md_filename, extras=["header-ids", "fenced-code-blocks"])

  # Convert html fragments to node element
  nodes = fragments_fromstring(html)

  return (html, nodes)


def get_chapter_title(nodes, filename=None, chapter_no=None):
  """Get chapter title from html elements that's parsed by fragments_fromstring

  If no h1 found in elements use chapter's filename instead.
  """

  title = None
  try:
    nodes = iter(nodes)
    for node in nodes:
      if node.tag == 'h1':
        title = node.text
        break

  finally:
    # Fallback to use filename as a title.
    # Assuming each chapter is underscore-separated-word named
    if not title:
      splitted = filename.split('_')
      if len(splitted) <= 1:
        title = filename
      else:
        title = ' '.join(splitted)

  if chapter_no:
    title = "%d. %s" % (chapter_no, title)

  return title


def prefix_chapter_title_with_chapter_no(html, chapter_no=None):
  """Return the html string with first header prefixed with

  chapter number.
  """

  if not chapter_no:
    return html

  # Convert html fragments to node element
  nodes = fragments_fromstring(html)

  # Apply to first important header
  for node in nodes:
    if node.tag in ['h1', 'h2']:
      node.text = "%s %d %s %s" % (CHAPTER_NO_BEFORE, chapter_no, CHAPTER_NO_AFTER, node.text)
      break

  return ''.join([to_html_string(node) for node in nodes])


def get_chapter_structure(elements, chapter_no=None, chapter_file=None):
  """Return partial html string containing nested-header

  structure found in chapter. Used by toc builder.
  """

  try:
    nodes = [el for el in elements if el.tag in CHAPTER_HEADINGS]
    nodes.reverse()
  except TypeError, te:
    return ""

  if not nodes:
    return ""

  # Header stacks to keep how depth indent
  hstack = []

  # Stringify first header into list
  header = nodes.pop()

  chapter_title = header.text

  nav = '<ol><li><a href="%s#%s">%s</a>' % (chapter_file,
                                            header.get('id'), chapter_title)

  # Append header level, in numeric, to hstack
  hstack.append(int(header.tag[1]))

  while nodes:
    node = nodes.pop()
    header = int(node.tag[1])

    section_title = node.text

    if header < hstack[-1]:   # Lower than means the header is more important.
                              # This means `h1` is more important than `h2`
      while hstack and header < hstack.pop():
        nav = ''.join([nav, close_li_ol()]) # close li and ol until met the right indent

      nav = ''.join([nav, close_li(), open_li_a(section_title,
                    href="%s#%s" % (chapter_file, node.get('id')))])

      hstack.append(header)

    elif header > hstack[-1]: # Greater than means the header is less important

      nav = ''.join([nav, open_ol(), open_li_a(section_title,
                    href="%s#%s" % (chapter_file, node.get('id')))])

      hstack.append(header)

    else:                     # Same header level
      nav = ''.join([nav, close_li(), open_li_a(section_title,
                    href="%s#%s" % (chapter_file, node.get('id')))])

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


def open_li_a(text, href=None):
  if href is not None:
    filename, ext = os.path.splitext(href)
    if not ext:
      href = '#' + filename
  else:
    href = '#'

  return '<li><a href="%s">%s</a>' % (href, text)


def get_chapter_layout(book=None, chapter=None, chapter_nav=None):

  instance = Chapter(renderer=RENDERER, book=book,
                     chapter=chapter, chapter_nav=chapter_nav)

  return instance


def get_toc_layout(book=None, toc=None):

  return Toc(renderer=RENDERER, book=book, toc=toc)


def get_cover_layout(book=None):

  return Cover(renderer=RENDERER, book=book)


if __name__ == '__main__':
  build()
