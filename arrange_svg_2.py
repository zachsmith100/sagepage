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
import random

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
    rect_element = HTMLElement('rect').set_attr('id', str(rect.identifier))
    rect_element.set_attr('x', str(rect.x)).set_attr('y', str(rect.y)).set_attr('width', str(rect.width)).set_attr('height', str(rect.height))
    style = HTMLStyleBuilder().set('fill', rect.get_color()).set('stroke', 'black').set('stroke-width', '1px')
    rect_element.set_attr('style', str(style))
    html.add_child(rect_element)

  with open(filename, 'w') as f:
    f.write(str(html))

######
# Rect
######
class Rect:
  def __init__(self, identifier, x=0, y=0, width=0, height=0, color='gray'):
    self.identifier = identifier
    self.x = x
    self.y = y
    self.width = width
    self.height = height
    self.color = color

  def get_color(self):
    if self.color is None:
      return 'none'
    return self.color

  def set_color(self, color):
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
  def __init__(self, identifier, color=None):
    self.identifier = identifier
    self.color = color

  def set_color(self, color):
    self.color = color

  def is_free(self):
    if self.color is None:
      return True
    return False

  def __str__(self):
    return 'FreeCell({0}, {1}, is_free()=>{0})'.format(self.identifier, self.color, self.is_free())

  def __repr__(self):
    return self.__str__()

############
# AreaMatrix
############
class AreaMatrix:
  def __init__(self, width, height):
    self.width = width
    self.height = height
    self.row_heights = []
    self.column_widths = []
    self.rows = []
    self.columns = []
    self.next_id = 0

    cell = FreeCell(self.get_next_id())
    self.rows.append([cell])
    self.row_heights.append(height)
    self.columns.append([cell])
    self.column_widths.append(width)

  def get_next_id(self):
    next_id = self.next_id
    self.next_id = self.next_id + 1
    return next_id

  def mark_cell(self, col_index, row_index, color):
    self.columns[col_index][row_index].set_color(color)

  def split_row(self, row_index, new_height):
    old_height = self.row_heights[row_index]
    self.row_heights[row_index] = new_height
    new_row_height = old_height - new_height

    new_row = []
    for col_index in range(len(self.columns)):
      cell = FreeCell(self.get_next_id(), self.rows[row_index][col_index].color)
      new_row.append(cell)

    for col_index in range(len(new_row)):
      cell = new_row[col_index]
      self.columns[col_index].insert(row_index + 1, cell)

    self.rows.insert(row_index + 1, new_row)
    self.row_heights.insert(row_index + 1, new_row_height)

  def split_column(self, col_index, new_width):
    old_width = self.column_widths[col_index]
    self.column_widths[col_index] = new_width
    new_col_width = old_width - new_width

    new_col = []
    for row_index in range(len(self.rows)):
      new_col.append(FreeCell(self.get_next_id(), self.columns[col_index][row_index].color))

    for row_index in range(len(self.rows)):
      cell = new_col[row_index]
      self.rows[row_index].insert(col_index + 1, cell)

    self.columns.insert(col_index + 1, new_col)
    self.column_widths.insert(col_index + 1, new_col_width)

  def get_column_free_height(self, origin_col_index, origin_row_index, max_height=-1):
    height = 0
    row_index = origin_row_index
    while row_index < len(self.rows) and self.rows[row_index][origin_col_index].is_free():
      if max_height > -1 and (height + self.row_heights[row_index]) > max_height:
        break
      height = height + self.row_heights[row_index]
      row_index = row_index + 1
    return height

  def list_free_rects_for_cell(self, origin_col_index, origin_row_index):
    rects = []
    last_height = -1
    width = 0
    next_col_index = origin_col_index
    while next_col_index < len(self.columns) and self.columns[next_col_index][origin_row_index].is_free():
      next_height = self.get_column_free_height(next_col_index, origin_row_index, last_height)
      width = width + self.column_widths[next_col_index]
      if next_height != last_height and last_height > -1:    
        next_height = min(last_height, next_height)
        rects.append(Rect(None, origin_col_index, origin_row_index, width, last_height))
      last_height = next_height
      next_col_index = next_col_index + 1

    if last_height > 0:
      rects.append(Rect(None, origin_col_index, origin_row_index, width, last_height))      

    return rects


  def list_free_rects(self):
    free_rects = []
    for row_index in range(len(self.rows)):
      for col_index in range(len(self.columns)):
        cell_free_rects = self.list_free_rects_for_cell(col_index, row_index)
        if cell_free_rects is not None:
          free_rects.extend(cell_free_rects)
    return free_rects

  def select_leftmost_fit(self, test_rect, trial_rects):
    leftmost_rect = None
    for rect in trial_rects:
      if rect.width < test_rect.width or rect.height < test_rect.height:
        continue
      if leftmost_rect is None:
        leftmost_rect = rect
      elif rect.x < leftmost_rect.x:
        leftmost_rect = rect
    return leftmost_rect

  def place_rect(self, origin_col_index, origin_row_index, rect):
    remaining_width = rect.width
    remaining_height = rect.height

    # Split col
    ###########
    split_col_index = origin_col_index
    next_width = self.column_widths[split_col_index]
    while remaining_width > next_width:
      remaining_width = remaining_width - next_width
      split_col_index = split_col_index + 1
      next_width = self.column_widths[split_col_index]

    if remaining_width > 0:
      self.split_column(split_col_index, remaining_width)

    # Split row
    ###########
    split_row_index = origin_row_index
    next_height = self.row_heights[split_row_index]
    while remaining_height > next_height:
      remaining_height = remaining_height - next_height
      split_row_index = split_row_index + 1
      next_height = self.row_heights[split_row_index]

    if remaining_height > 0:
      self.split_row(split_row_index, remaining_height)

    # Mark
    ######
    for col_index in range(origin_col_index, split_col_index + 1):
      for row_index in range(origin_row_index, split_row_index + 1):
        self.rows[row_index][col_index].color = rect.get_color()

  def dump_svg(self, filename):
    rects = []
    y = 0
    for row_index in range(len(self.rows)):
      x = 0
      height = self.row_heights[row_index]
      for col_index in range(len(self.columns)):
        width = self.column_widths[col_index]
        cell = self.rows[row_index][col_index]
        rect = Rect(cell.identifier, x, y, width, height, cell.color)
        rects.append(rect)
        x = x + width
      y = y + height

    write_svg(filename, rects)

  def __str__(self):
    s = 'AreaMatrix(width={0}, height={1}, rows={2}, cols={3})'.format(self.width, self.height, len(self.rows), len(self.columns))
    return s 

  def __repr__(self):
    return self.__str__()


##############
# ArrangeRects
##############
class ArrangeRects:
  def __init__(self):
    self.matrix = AreaMatrix(0,0)

  def get_placement_coord(self, rect):
    x = 0
    y = 0
    
  def get_enclosing_rect_for_area(self, area):
    unit_square = area/self.ratio
    h = math.sqrt(unit_square)
    w = h * self.ratio

    if ((w*100) % 10) > 0:
      w = int(w) + 1
    else:
      w = int(w)

    if ((h*100) % 10) > 0:
      h = int(h) + 1
    else:
      h = int(h)

    return Size(w,h)


  def attempt_arrangement(self, matrix, rects):
    for rect in rects:
      free_rects = matrix.list_free_rects()
      #print(free_rects)
      leftmost_rect = matrix.select_leftmost_fit(rect, free_rects)

      if leftmost_rect is None:
        return False

      matrix.place_rect(leftmost_rect.x, leftmost_rect.y, rect)

    return True

  def arrange(self, rects, ratio):
    self.ratio = ratio

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
      enclosing_rect = self.get_enclosing_rect_for_area(area)
      print("Attempting enclosing rect", enclosing_rect.width, enclosing_rect.height)
      matrix = AreaMatrix(enclosing_rect.width, enclosing_rect.height)
      if self.attempt_arrangement(matrix, rects):
        print("Found arrangement", enclosing_rect)
        matrix.dump_svg(output_file)
        break
      area = area + int(area * 0.1)

    


rects = []
ratio = 1.618

input_rects = []

class NextColor:
  def __init__(self):
    self.colors = ['red', 'green', 'blue', 'yellow', 'purple', 'gray', 'black']
    self.index = 0

  def next_color(self):
    if self.index >= len(self.colors):
      self.index = 0
    c = self.colors[self.index]
    self.index = self.index + 1
    r = random.randint(0,255)
    g = random.randint(0,255)
    b = random.randint(0,255)
    c = 'rgb({0},{1},{2})'.format(r,b,b)
    return c

next_color = NextColor()

for i in range(150):
  input_rects.append(Rect(None, 0, 0, random.randint(15, 300), random.randint(15, 300), next_color.next_color()))

#input_rects.append(Rect(0,0,0,100,200, 'red'))
#input_rects.append(Rect(1,0,0,20,20, 'green'))
#input_rects.append(Rect(2,0,0,75,235, 'blue'))
#input_rects.append(Rect(3,0,0,120,200, 'gray'))
#input_rects.append(Rect(4,0,0,120,100, 'magenta'))
#input_rects.append(Rect(5,0,0,12,23, 'purple'))
#input_rects.append(Rect(6,0,0,1200,235, 'yellow'))

#arrange_rects = ArrangeRects()
#arrange_rects.arrange(input_rects, ratio)


#cell = FreeCell(True, 1024, 1024)
#cell.split_vertically(150)
#cell.split_horizontally(25)
#cell.east.south.split_horizontally(100)
#cell.east.south.split_vertically(225)
#cell.south.south.split_horizontally(25)


#matrix = AreaMatrix(1024, 1024)
#print(matrix)
#matrix.split_row(0, 100)
#matrix.split_column(0, 100)
#matrix.split_column(1, 300)
#matrix.split_column(2, 100)
#matrix.split_row(1, 100)
#matrix.split_row(2, 100)

#matrix.mark_cell(0,0,'red')
#matrix.mark_cell(0,1,'red')
#matrix.mark_cell(1,0,'red')
#free_rects = matrix.list_free_rects()
#print(free_rects)

#rect = matrix.select_leftmost_fit(Rect(None, 0, 0, 800, 800), free_rects)

arrange_rects = ArrangeRects()
arrange_rects.arrange(input_rects, ratio)

#matrix.mark_cell(rect.x, rect.y, 'green')
#print("leftmost fit:", rect)

#matrix.dump_svg(output_file)


#write_svg(output_file, input_rects)

#write_svg('{0}.cells.svg'.format(output_file), cell_rects)
