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
if len(sys.argv) != 2:
  print('Usage: {0} <in-file>'.format(sys.argv[0]))
  exit(1)

in_path = sys.argv[1]

################################################################################
# Load Links
################################################################################
identifiers = []

class MutableSeqOpsHtmlParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.url = None
    self.function_name = ''
    self.process_next_header_link = False

  def handle_starttag(self, tag, attrs):
    data = {i[0]:i[1] for i in attrs}

    if tag == 'dt' and 'id' in data and data['id'].startswith('bytes.'):
      self.function_name = data['id'].split('.')[1]
      self.process_next_header_link = True

    if self.process_next_header_link and tag == 'a':
      print('{0}, {1}{2}'.format(self.function_name, 'library/stdtypes.html?highlight=text%20sequence', data['href']))
      self.process_next_header_link = False

  def handle_endtag(self, tag):
    pass
    
  def handle_data(self, data):
    pass

with open(in_path, 'r') as f:
  parser = MutableSeqOpsHtmlParser()
  parser.feed(f.read())