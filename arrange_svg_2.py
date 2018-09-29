import os
import sys
import math
import random
import csv
import html
from html.parser import HTMLParser
from utils.html import HTMLElement
from utils.html import HTMLStyleBuilder
from utils.rectarrange import ArrangeRects
from utils.models import Rect
from utils.svg import SVG

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

rects = []
ratio = 1.618

input_rects = []

class RandomColor:
  def __init__(self):
    self.index = 0

  def next_color(self):
    r = random.randint(0,255)
    g = random.randint(0,255)
    b = random.randint(0,255)
    c = 'rgb({0},{1},{2})'.format(r,b,b)
    return c

rand_color = RandomColor()

for i in range(15):
  input_rects.append(Rect(None, 0, 0, random.randint(15, 300), random.randint(15, 300), rand_color.next_color()))

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
arrange_rects.arrange(input_rects, ratio, '{0}.matrix.svg'.format(output_file))

SVG.dump_rects(output_file, input_rects)

#matrix.mark_cell(rect.x, rect.y, 'green')
#print("leftmost fit:", rect)

#matrix.dump_svg(output_file)


#write_svg(output_file, input_rects)

#write_svg('{0}.cells.svg'.format(output_file), cell_rects)
