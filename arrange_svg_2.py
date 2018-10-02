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
from utils.rectarrange import AreaMatrix
from utils.models import Rect
from utils.svg import SVG

################################################################################
# Command line
################################################################################
if len(sys.argv) != 2:
  print('Usage: {0} <svg-out-file>'.format(sys.argv[0]))
  exit(1)

output_file = sys.argv[1]

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

#for i in range(15):
  #input_rects.append(Rect(None, 0, 0, random.randint(15, 300), random.randint(15, 300), rand_color.next_color()))

input_rects.append(Rect(0,0,0,50,75, 'red'))
input_rects.append(Rect(1,0,0,20,20, 'green'))
input_rects.append(Rect(2,0,0,75,235, 'blue'))
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


matrix = AreaMatrix(1024, 1024)
matrix.place_rect(0, 0, input_rects[2])
#matrix.split_column(0, 30)
#matrix.split_column(1, 20) # at 50
#matrix.split_column(2, 100) # at 150
#matrix.split_column(3, 175) # at 325

#matrix.split_row(0, 100)
#matrix.split_row(1, 25) # at 125
#matrix.split_row(2, 25) # at 150

overlay_matrix = AreaMatrix(200, 200)
overlay_matrix.place_rect(0, 0, input_rects[0])
overlay_matrix.place_rect(1, 1, input_rects[1])
#overlay_matrix.split_column(0, 100)
#overlay_matrix.split_column(0, 10)
#overlay_matrix.split_row(0, 25)
#overlay_matrix.split_row(0, 15) # at 15
#overlay_matrix.split_row(1, 15) # at 30

matrix.overlay_matrix(0, 1, overlay_matrix)
#overlay_matrix.overlay_matrix(0, 0, matrix, [])

matrix.update_rects_xy(input_rects)

matrix.dump_svg('{0}.matrix.svg'.format(output_file))
overlay_matrix.dump_svg('{0}.overlay_matrix.svg'.format(output_file))


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

#arrange_rects = ArrangeRects()
#arrange_rects.arrange(input_rects, ratio, ArrangeRects.default_sort_key, '{0}.matrix.svg'.format(output_file))

SVG.dump_rects(output_file, input_rects)
