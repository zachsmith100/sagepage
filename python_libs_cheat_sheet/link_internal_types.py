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

################################################################################
# Command line
################################################################################
if len(sys.argv) != 4:
  print('Usage: {0} <input_file.html> <output_config_file.json> <output_file.csv>'.format(sys.argv[0]))
  exit(-1)

in_path = sys.argv[1]
out_config_path = sys.argv[2]
out_csv_path = sys.argv[3]

################################################################################
# Load Links
################################################################################
identifiers = []

class TitleLink:
  def __init__(self):
    self.title = None
    self.url = None
    self.links = []
    self.cur_link_url = None

  def on_starttag(self, tag, data):
    if self.title is None:
      if tag == 'a':
        self.url = data['href']
    else:
      if tag == 'a' and self.cur_link_url is None:
        self.cur_link_url = data['href']

  def on_endtag(self, tag):
    pass

  def on_data(self, data):
    normalized = data.strip()
    if self.title is None and self.url is not None and len(normalized) > 0:
      self.title = normalized
    elif self.title is not None and self.url is not None and len(normalized) > 0:
      if self.cur_link_url is not None:
        self.links.append((normalized, self.cur_link_url))
        self.cur_link_url = None

  def __str__(self):
    return '{0}({1}, {2})'.format(self.title, self.url, self.links)

  def __repr__(self):
    return self.__str__()


class InternalTypesHtmlParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.read_title = False
    self.read_link = False
    self.cur_title = None
    self.links = []

  def handle_starttag(self, tag, attrs):
    data = {i[0]:i[1] for i in attrs}

    if tag == 'li' and 'class' in data and data['class'] == 'toctree-l1':
      self.cur_title = TitleLink()
      self.links.append(self.cur_title)

    if self.cur_title:
      self.cur_title.on_starttag(tag, data)
    
  def handle_endtag(self, tag):
    if self.cur_title:
      self.cur_title.on_endtag(tag)

    
  def handle_data(self, data):
    if self.cur_title:
      self.cur_title.on_data(data)



with open(in_path, 'r') as f:
  parser = InternalTypesHtmlParser()
  parser.feed(f.read())

################################################################################
# Output
################################################################################
gui_tpl ='''"{0}":
{{
  "layout_class":"SimpleWordListLayout",
  "layout_ratio":1.618,
  "col_count":1,
  "font_name":"sans-serif",
  "font_size":10,
  "border_width":3,
  "row_spacing":1,
  "col_spacing":14,
  "background_color":"{1}",
  "font_color":"{2}",
  "title":"{3}"
}}'''

base_url = 'https://docs.python.org/3/library'
bg_color = [236, 236, 236]
font_color = [0,0,0]

csv_links = []
configs = []

for group in parser.links:
  if len(group.links) < 2:
    continue

  group_id = group.title.replace('-', '_').replace(' ', '_')

  bg_color_str = 'rgb({0},{1},{2})'.format(bg_color[0], bg_color[1], bg_color[2])
  font_color_str = 'rgb({0},{1},{2})'.format(font_color[0], font_color[1], font_color[2])

  configs.append(gui_tpl.format(group_id, bg_color_str, font_color_str, group.title))

  #next_link_id = 0
  #out_csv_file.write('"{0}", "{1}", "{2}", "{3}/{4}"'.format(group_id, next_link_id, group.title, base_url, group.url))

  next_link_id = 1
  for link in group.links:
    csv_links.append('"{0}", "{1}", "{2}", "{3}/{4}"'.format(group_id, next_link_id, link[0], base_url, link[1]))
    next_link_id = next_link_id + 1

with open(out_config_path, 'w') as f:
  f.write(',\n'.join(configs))

with open(out_csv_path, 'w') as f:
  f.write('\n'.join(csv_links))
