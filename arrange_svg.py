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

  def add_attr(self, n, v):
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
    self.styles = []

  def add(self, name, value):
    self.styles.append((name,value))
    return self

  def __str__(self):
    return ';'.join(['{0}:{1}'.format(style[0],style[1]) for style in self.styles])

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

for filename in os.listdir(input_dir):
  if filename.endswith(".svg") is not True:
    continue

  full_filename = os.path.join(input_dir, filename)

  with open(full_filename, 'r') as svg_file:
    parser = SVGHTMLParser()
    parser.feed(svg_file.read())

################################################################################
# Arrange
################################################################################
def get_smallest_bounding_golden_rect(rects):
  area = 0
  scale_width = 1
  scale_height = 1.618

  for rect in rects:
    area = area + (rect[0] * rect[1])

  width = scale_width
  height = scale_height

  while (width * height) < area:
    width = width + scale_width
    height = height + scale_height

  return (width, height)


html = HTMLElement("svg")

x = 0
y = 0
width = 50
height = 1.618 * width
style = HTMLStyleBuilder().add('stroke', 'rgb(0,0,255)').add('stroke-width', '2').add('fill-opacity', '0')
rect_element = HTMLElement('rect')
rect_element.add_attr('width', str(width)).add_attr('height', str(height))
rect_element.add_attr('style', str(style))
html.add_child(rect_element)


for i in range(10):
  prev_width = width
  prev_height = height
  width = height
  height = prev_width + height

  if i % 4 == 0:
    x = x + prev_width
  elif i % 4 == 1:
    y = y + prev_width
    x = x + prev_width - width
  elif i % 4 == 2:
    x = x - width
    y = y - (width - prev_width)
  elif i % 4 == 3:
    y = y - width
  
  print(x, y, width, height)

  style = HTMLStyleBuilder().add('stroke', 'rgb(0,0,0)').add('stroke-width', '2').add('fill-opacity', '0')
  rect_element = HTMLElement('rect')
  rect_element.add_attr('x', str(x)).add_attr('y', str(y))
  rect_element.add_attr('width', str(width)).add_attr('height', str(width))
  rect_element.add_attr('style', str(style))
  html.add_child(rect_element)

with open(output_file, 'w') as f:
  f.write(str(html))


bounding_rect = get_smallest_bounding_golden_rect(rects)

print(bounding_rect)

exit(0)