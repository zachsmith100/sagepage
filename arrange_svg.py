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

def dump_cell_svg(cell, filename):
  cell_rects = []
  next_cell = cell
  x = 0
  y = 0
  while next_cell:
    rect = Rect(x, y, next_cell.width, next_cell.height)
    if next_cell.is_free() is not True:
      rect.fill = next_cell.color
    else:
      rect.fill = 'none'

    cell_rects.append(rect)

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

  write_svg(filename, cell_rects)

def write_svg(filename, rects):
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
    style = HTMLStyleBuilder().set('fill', rect.fill).set('stroke', 'black').set('stroke-width', '1px')
    rect_element.set_attr('style', str(style))
    html.add_child(rect_element)

  with open(filename, 'w') as f:
    f.write(str(html))

######
# Rect
######
class Rect:
  def __init__(self, x=0, y=0, width=0, height=0, color='gray'):
    self.x = x
    self.y = y
    self.width = width
    self.height = height
    self.color = color

  def __str__(self):
    return 'Rect({0}, {1}, {2}, {3})'.format(self.x, self.y, self.width, self.height)

  def __repr__(self):
    return self.__str__()

######
# Size
######
class Size:
  def __init__(self, width, height):
    self.width = width
    self.height = height

  def __str__(self):
    return 'Size({0}, {1})'.format(self.width, self.height)

  def __repr__(self):
    return self.__str__()

##########
# FreeCell
##########
class FreeCell:
  def __init__(self, free=True, width=0, height=0, color='none'):
    self.free = free
    self.width = width
    self.height = height
    self.north = None
    self.east = None
    self.south = None
    self.west = None
    self.color = color

  def set_free(self, free):
    self.free = free

  def is_free(self):
    if self.free is True:
      return True
    return False

  def split_vertically(self, x):
    new_cell_width = self.width - x
    self.width = x

    new_cell = FreeCell(self.free, new_cell_width, self.height, self.color)
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

    new_cell = FreeCell(self.free, self.width, new_cell_height, self.color)
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

  def __str__(self):
    return 'FreeCell({0}, {1}, {2})'.format(self.is_free(), self.width, self.height)

  def __repr__(self):
    return self.__str__()

############
# AreaMatrix
############
class AreaMatrix:
  def __init__(self, width, height):
    cell = FreeCell(True, width, height)
    self.rows = []
    self.columns = []

    self.rows.append(cell)
    self.columns.append(cell)

##############
# ArrangeRects
##############
class ArrangeRects:
  def __init__(self):
    self.i = 0

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

    return Size(w,h)

  def check_cell_fit(self, cell, rect):
    remaining_width = rect.width
    next_h_cell = cell
    while True:
      if next_h_cell is None:
        return False
      if next_h_cell.is_free() is not True:
        return False
      remaining_height = rect.height
      next_v_cell = next_h_cell
      while True:
        if next_v_cell is None:
          return False
        if next_v_cell.is_free() is not True:
          return False
        if next_v_cell.height >= remaining_height:
          break
        remaining_height = remaining_height - next_v_cell.height
        next_v_cell = next_v_cell.south
      if next_h_cell.width >= remaining_width:
        break
      remaining_width = remaining_width - next_h_cell.width
      next_h_cell = next_h_cell.east
    return True

  def mark_cell_occupied(self, cell):
    cell.color = self.cur_color
    cell.set_free(False)

  def allocate_space(self, cell, rect_id, rect):
    remaining_width = rect.width
    next_h_cell = cell
    while True:

      remaining_height = rect.height
      next_v_cell = next_h_cell
      while True:
        if next_v_cell.height < remaining_height:
          self.mark_cell_occupied(next_v_cell)
        elif next_v_cell.height == remaining_height:
          self.mark_cell_occupied(next_v_cell)
          break
        else:
          new_cell = next_v_cell.split_horizontally(remaining_height)
          self.mark_cell_occupied(next_v_cell)
          new_cell.set_free(True)
          new_cell.color = 'none'
          self.dump_svg()
          break
        remaining_height = remaining_height - next_v_cell.height
        next_v_cell = next_v_cell.south

      if next_h_cell.width < remaining_width:
        self.mark_cell_occupied(next_h_cell)
      elif next_h_cell.width == remaining_width:
        self.mark_cell_occupied(next_h_cell)
        break
      else:
        print("Splitting vertically", remaining_width, next_h_cell.width)
        new_cell = next_h_cell.split_vertically(remaining_width)
        self.mark_cell_occupied(next_h_cell)
        new_cell.set_free(True)
        new_cell.color = 'none'
        self.dump_svg()
        break
      remaining_width = remaining_width - next_h_cell.width
      next_h_cell = next_h_cell.east

    return True


  def place_rect(self, cell, rect_id, rect):
    self.i = self.i + 1
    self.cur_color = rect.color
    next_cell = cell
    x = 0
    y = 0
    while next_cell:
      if self.check_cell_fit(next_cell, rect):
        self.allocate_space(next_cell, rect_id, rect)
        rect.x = x
        rect.y = y
        return True

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
    return False

  def dump_svg(self):
    dump_filename = '{0}.{1}.cells.svg'.format(output_file, self.i)
    dump_cell_svg(self.root_cell, dump_filename)
    self.i = self.i + 1

  def attempt_arrangement(self, cell, rects):
    for rect_id in range(len(rects)):
      if self.place_rect(cell, rect_id, rects[rect_id]) is not True:
        print("Failed", rects[rect_id])
        return False
      else:
        print("Passed", rects[rect_id])
    return True

  def arrange(self, rects, ratio):
    self.ratio = ratio
    self.rows = []
    self.columns = []

    rects.sort(key=lambda r: (r.width * r.height), reverse=True)
    width = 0
    height = 0
    for rect in rects:
      if (rect.x + rect.width) > width:
        width = rect.x + rect.width
      if (rect.y + rect.height) > height:
        height = rect.y + rect.height
    area = width * height

    while True:
      enclosing_rect = self.get_enclosing_rect_for_area(area*10)
      print("Attempting", enclosing_rect.width, enclosing_rect.height)
      cell = FreeCell(True, enclosing_rect.width, enclosing_rect.height)
      self.root_cell = cell
      if self.attempt_arrangement(cell, rects):
        print("Found arrangement", enclosing_rect)
        break
      area = area + int(area * 0.1)

    


rects = []
ratio = 1.618

input_rects = []
input_rects.append(Rect(0,0,100,200, 'red'))
input_rects.append(Rect(0,0,20,20, 'green'))
input_rects.append(Rect(0,0,75,235, 'blue'))
input_rects.append(Rect(0,0,120,235, 'gray'))
#input_rects.append(Rect(0,0,120,10, 'magenta'))
#input_rects.append(Rect(0,0,12,23, 'purple'))
#input_rects.append(Rect(0,0,1200,235))

arrange_rects = ArrangeRects()
arrange_rects.arrange(input_rects, ratio)


#cell = FreeCell(True, 1024, 1024)
#cell.split_vertically(150)
#cell.split_horizontally(25)
#cell.east.south.split_horizontally(100)
#cell.east.south.split_vertically(225)
#cell.south.south.split_horizontally(25)

for r in input_rects:
  r.fill = 'rgb(128,128,128)'



write_svg(output_file, input_rects)

#write_svg('{0}.cells.svg'.format(output_file), cell_rects)
