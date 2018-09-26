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

class BuiltinHtmlParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.url = None
    self.process_data = False

  def handle_starttag(self, tag, attrs):
    data = {i[0]:i[1] for i in attrs}
    if 'class' in data and data['class'] == 'reference internal':
      self.url = data['href']
      return

    if tag == 'span' and 'class' in data and data['class'] == 'pre':
      self.process_data = True

  def handle_endtag(self, tag):
    pass
    
  def handle_data(self, data):
    if self.process_data is not True:
      return

    print('"{0}", "library/functions.html{1}"'.format(data, self.url))
    self.process_data = False

with open(in_path, 'r') as f:
  parser = BuiltinHtmlParser()
  parser.feed(f.read())