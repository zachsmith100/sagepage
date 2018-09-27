#!/usr/bin/env python

from itertools import count
from subprocess import call, PIPE, Popen
import os
import re
import sys
import tempfile

import math
import csv
import html
from html.parser import HTMLParser
from pdfutil.pdf import *

# HTMLAttribute
###############
class HTMLAttribute:
  def __init__(self, name, value):
    self.name = name
    self.value = value

  def __str__(self):
    return '{0}="{1}"'.format(self.name, self.value)

  def __repr__(self):
    return self.__str__()

#############
# HTMLElement
#############
class HTMLElement:
  def __init__(self, name):
    self.name = name
    self.attributes = []
    self.children = []
    self.text = ''

  def set_attr(self, n, v):
    self.attributes.append(HTMLAttribute(n,v))
    return self

  def add_child(self, e):
    self.children.append(e)
    return e

  def set_text(self, t):
    self.text = t
    return self

  def render(self, f):
    f.write(str(self))

  def __str__(self):
    return "<{0} {1}>\n{2}{3}\n</{0}>\n".format(self.name, ' '.join([str(attr) for attr in self.attributes]), "\n".join([str(child) for child in self.children]), self.text)

  def __repr__(self):
    return self.__str__()

##################
# HTMLStyleBuilder
##################
class HTMLStyleBuilder:
  def __init__(self):
    self.styles = {}

  def set(self, name, value):
    self.styles[name] =value
    return self

  def __str__(self):
    return ';'.join(['{0}:{1}'.format(name, self.styles[name]) for name in self.styles])

  def __repr__(self):
    return self.__str__()

################################################################################
# Command line
################################################################################
if len(sys.argv) != 3:
  print('Usage: {0} <input-dir> <svg-out-file>'.format(sys.argv[0]))
  exit(1)

input_dir = sys.argv[1]
output_file = sys.argv[2]

################################################################################
# Load SVG Rects
################################################################################
global rects
rects = []

class SVGHTMLParser(HTMLParser):
  
  def handle_starttag(self, tag, attrs):
    global rects
    if tag.lower() == 'svg':
      data = {i[0]:i[1] for i in attrs}
      rects.append([float(data['width']), float(data['height'])])

  def handle_endtag(self, tag):
    pass

  def handle_data(self, data):
    pass

'''
for filename in os.listdir(input_dir):
  if filename.endswith(".svg") is not True:
    continue

  full_filename = os.path.join(input_dir, filename)

  with open(full_filename, 'r') as svg_file:
    parser = SVGHTMLParser()
    parser.feed(svg_file.read())
'''

################################################################################
# Arrange
################################################################################
class Rect:
  def __init__(self, x=0, y=0, width=0, height=0):
    self.x = x
    self.y = y
    self.width = width
    self.height = height

class FreeCell:
  def __init__(self, free=True, width=0, height=0):
    self.free = free
    self.width = width
    self.height = height
    self.north = None
    self.east = None
    self.south = None
    self.west = None

  def split_vertically(self, x):
    new_cell_width = self.width - x
    self.width = x

    new_cell = FreeCell(self.free, new_cell_width, self.height)
    original_east = self.east
    self.east = new_cell

    if self.north:
      self.north.south = None
      new_cell.north = self.north.split_vertically(x)
      new_cell.north.south = new_cell
      self.north.south = self

    if self.south:
      self.south.north = None
      new_cell.south = self.south.split_vertically(x)
      new_cell.south.north = new_cell
      self.south.north = self

    new_cell.east = original_east
    new_cell.west = self

    return new_cell

  def split_horizontally(self, y):
    new_cell_height = self.height - y
    self.height = y

    new_cell = FreeCell(self.free, self.width, new_cell_height)
    original_south = self.south
    self.south = new_cell

    if self.west:
      self.west.east = None
      new_cell.west = self.west.split_horizontally(y)
      new_cell.west.east = new_cell
      self.west.east = self

    if self.east:
      self.east.west = None
      new_cell.east = self.east.split_horizontally(y)
      new_cell.east.west = new_cell
      self.east.west = self

    new_cell.north = self
    new_cell.south = original_south

    return new_cell

class AreaMatrix:
  def __init__(self, width, height):
    cell = FreeCell(True, width, height)
    self.rows = []
    self.columns = []

    self.rows.append(cell)
    self.columns.append(cell)


class ArrangeRects:
  def __init__(self, ratio):
    self.ratio = ratio

  def get_placement_coord(self, rect):
    x = 0
    y = 0
    
  def get_enclosing_rect_for_area(self, area):
    unit_square = area/self.ratio
    w = math.sqrt(unit_square)
    h = w * self.ratio

    if ((w*100) % 10) > 0:
      w = int(w) + 1
    else:
      w = int(w)

    if ((h*100) % 10) > 0:
      h = int(h) + 1
    else:
      h = int(h)

    return (w,h)


  def arrange(self, rects):
    self.rows = []
    self.columns = []

    rects.sort(key=lambda r: (r.width * r.height))
    width = 0
    height = 0
    for rect in rects:
      if (rect.x + rect.width) > width:
        width = rect.x + rect.width
      if (rect.y + rect.height) > height:
        height = rect.y + rect.height
    self.enclosing_area = area = width * height
    print(self.get_enclosing_rect_for_area(area))


#arrange_rects = ArrangeRects(ratio)

#arrange_rects.arrange(rects)

rects = []
ratio = 1.618

cell = FreeCell(True, 1024, 1024)
cell.split_vertically(150)
cell.split_horizontally(25)
cell.east.south.split_horizontally(100)
cell.east.south.split_vertically(225)

cell.south.south.split_horizontally(25)


next_cell = cell
x = 0
y = 0
while next_cell:
  rect = Rect(x, y, next_cell.width, next_cell.height)
  rects.append(rect)

  if next_cell.east:
    x = x + next_cell.width
    next_cell = next_cell.east
  elif next_cell.south:
    x = 0
    y = y + next_cell.height
    next_cell = next_cell.south
    while next_cell.west:
      next_cell = next_cell.west
  else:
    next_cell = None

width = 0
height = 0
for rect in rects:
  if (rect.x + rect.width) > width:
    width = rect.x + rect.width
  if (rect.y + rect.height) > height:
    height = rect.y + rect.height

html = HTMLElement('svg')
html.set_attr('x', str(0)).set_attr('y', str(0)).set_attr('width', str(width)).set_attr('height', str(height))

for rect in rects:
  rect_element = HTMLElement('rect')
  rect_element.set_attr('x', str(rect.x)).set_attr('y', str(rect.y)).set_attr('width', str(rect.width)).set_attr('height', str(rect.height))
  style = HTMLStyleBuilder().set('fill', 'none').set('stroke', 'black').set('stroke-width', '2px')
  rect_element.set_attr('style', str(style))
  html.add_child(rect_element)

with open(output_file, 'w') as f:
  f.write(str(html))