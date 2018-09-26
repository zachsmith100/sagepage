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

class GlossaryHtmlParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.url = None

  def handle_starttag(self, tag, attrs):
    data = {i[0]:i[1] for i in attrs}
    if 'id' not in data:
      return

    if data['id'].startswith('term'):
      self.url = "glossary.html#{0}".format(data['id'])

  def handle_endtag(self, tag):
    self.url = None
    
  def handle_data(self, data):
    if self.url is None:
      return
    print("\"{0}\", \"{1}\"".format(data.strip(), self.url))

with open(in_path, 'r') as f:
  parser = GlossaryHtmlParser()
  parser.feed(f.read())