
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
if len(sys.argv) != 5:
  print('Usage: %s <links-csv-file> <svg-file> <inkscape-gen-pdf> <linkified-pdf>'
    % sys.argv[0], file=sys.stderr)
  exit(1)

csv_path = sys.argv[1]
svg_path = sys.argv[2]
pdf_in_path = sys.argv[3]
pdf_out_path = sys.argv[4]

################################################################################
# Load CSV Links
################################################################################
print("Reading links...")
links = {}

with open(csv_path, 'r') as csv_file:
  csv_reader = csv.reader(csv_file)
  links = {'{0}.{1}'.format(link[0].strip(), link[1].strip()):link[3].strip() for link in csv_reader}

print(links)

################################################################################
# Load SVG Rects
################################################################################
print("Loading SVG rects from file: {0}".format(svg_path))
svg_rects = {}

class SVGHTMLParser(HTMLParser):
  def handle_starttag(self, tag, attrs):
    if tag.lower() == "rect":
      rect_data = {i[0]:i[1] for i in attrs}
      if rect_data['id'] in links:
        svg_rects[rect_data['id']] = rect_data
        svg_rects[rect_data['id']]['x'] = float(svg_rects[rect_data['id']]['x'])
        svg_rects[rect_data['id']]['y'] = float(svg_rects[rect_data['id']]['y'])

  def handle_endtag(self, tag):
    pass

  def handle_data(self, data):
    pass

with open(svg_path, 'r') as svg_file:
  parser = SVGHTMLParser()
  parser.feed(svg_file.read())

################################################################################
# Process Rects
################################################################################
print("Extracting rects from PDF...")
in_pdf = None

def set_pdf(pdf):
  global in_pdf
  in_pdf = pdf

parser = PDFParser(set_pdf)
reader = ParserReader()
if reader.read_file(parser.begin, pdf_in_path):
  print("SUCCESS")
else:
  print("FAIL")

for k in in_pdf.objects:
  obj = in_pdf.objects[k]
  with open("{0}.{1}.head".format(obj.name, obj.version), "w") as f:
    f.write(str(obj))
  for v in obj.values:
    decode_filter = None
    if v.type == PDFValue.DICTIONARY:
      if 'Filter' in v.value:
        decode_filter = v.value['Filter']

    decoded = None
    if decode_filter is not None and decode_filter.value == 'FlateDecode':
      decoded = zlib.decompress(obj.stream_data)
      print(decoded)

    if decoded is not None:
      with open("{0}.{1}".format(obj.name, obj.version), "wb") as f:
        f.write(decoded)

class PDFDeviceRGBColor:
  def __init__(self, r=0.0, g=0.0, b=0.0):
    self.r = r
    self.g = g
    self.b = b

  def compare(self, r, g, b):
    a = self.r + (self.g*1000) + (self.b*1000000)
    b = r + (g*1000) + (b*1000000)

    if a > b:
      return -1
    elif a < b:
      return 1
    return 0

class PDFLinkRectsUtils:
  def get_content_objects(pdf):
    root_obj = None
    for key, obj in pdf.objects.items():
      obj_type = None
      if 'Type' in obj.named_values:
        obj_type = obj.named_values['Type']
      if obj_type is not None and obj_type.value == 'Pages':
        root_obj = obj
        break
    if root_obj is None:
      return Result("Expected element 'Pages' missing from PDF")
    if 'Kids' not in root_obj.named_values:
      return Result("Expected element 'Kids' missing from Pages object")
    pages = [o.value for o in root_obj.named_values['Kids'].value]
    content_refs = [pdf.objects[ref.get_key()].named_values['Contents'].value for ref in pages if 'Contents' in pdf.objects[ref.get_key()].named_values]
    content_objects = [pdf.objects[ref.get_key()] for ref in content_refs]
    return Result(None, content_objects)

  def decompress_content_stream(obj):
    decompressed = obj.stream_data
    if 'Filter' in obj.named_values:
      if obj.named_values['Filter'].value == 'FlateDecode':
        decompressed = zlib.decompress(obj.stream_data).decode()
      else:
        return Result("Unsupported Filter type '{0}'".format(obj.named_values['Filter']))
    return Result(None, decompressed)

  def recompress_content_stream(obj):
    compressed = obj.stream_data
    if 'Filter' in obj.named_values:
      if obj.named_values['Filter'].value == 'FlateDecode':
        #del obj.named_values['Filter']
        compressed = zlib.compress(obj.stream_data)
      else:
        return Result("Unsupported Filter type '{0}'".format(obj.named_values['Filter']))
    return Result(None, compressed)

  def parse_content_stream(content_stream):
    commands = []
    def append_command(cmd):
        commands.append(cmd)
    reader = ParserReader()
    parser = PDFContentStreamParser(append_command)
    result = reader.read_string(parser.begin, content_stream)
    if result:
      return Result(None, commands)
    return Result("Content stream parsing failed", commands)

class PDFLinkRects:
  def pull_rects(color, pdf):
    selected_coords = []

    result = PDFLinkRectsUtils.get_content_objects(pdf)
    if result.is_error():
      return result
    content_objects = result.value

    for obj in content_objects:
      result = PDFLinkRectsUtils.decompress_content_stream(obj)
      if result.is_error():
        return result        
      stream_data = result.value
      
      result = PDFLinkRectsUtils.parse_content_stream(stream_data)
      if result.is_error():
        return result

      commands = result.value      
      output_commands = []
      selected_commands = []
      selected_paths = False

      for cmd in commands:
        if cmd.name == 'rg':
          if color.compare(cmd.params[0].value, cmd.params[1].value, cmd.params[2].value) == 0:
            selected_paths = True
          else:
            selected_paths = False
        if selected_paths and cmd.name == 're':
          selected_commands.append(cmd)
        else:
          output_commands.append(cmd)

      obj.stream_data = "\n".join([str(cmd) for cmd in output_commands]).encode()

      result = PDFLinkRectsUtils.recompress_content_stream(obj)
      if result.is_error():
        return result
      obj.stream_data = result.value
      obj.named_values['Length'] = PDFValue(PDFValue.INT, len(obj.stream_data))
      selected_coords.extend([(cmd.params[0].value, cmd.params[1].value) for cmd in selected_commands])
         
    return Result(None, selected_coords)
        
result = PDFLinkRects.pull_rects(PDFDeviceRGBColor(1.0, 0, 1.0), in_pdf)
pdf_rects = result.value

################################################################################
# Match Rects
################################################################################
print("Matching rects...")

svg_top_x = -1
svg_top_y = -1

for svg_rect_id in svg_rects:
  svg_rect = svg_rects[svg_rect_id]
  if svg_top_x < 0:
    svg_top_x = svg_rect['x']
  elif svg_top_x > svg_rect['x']:
    svg_top_x = svg_rect['x']

  if svg_top_y < 0:
    svg_top_y = svg_rect['y']
  elif svg_top_y > svg_rect['y']:
    svg_top_y = svg_rect['y']

pdf_top_x = -1
pdf_top_y = -1

for pdf_rect in pdf_rects:
  if pdf_top_x < 0:
    pdf_top_x = pdf_rect[0]
  elif pdf_top_x > pdf_rect[0]:
    pdf_top_x = pdf_rect[0]

  if pdf_top_y < 0:
    pdf_top_y = pdf_rect[1]
  elif pdf_top_y > pdf_rect[1]:
    pdf_top_y = pdf_rect[1]

svg_pdf_x_offset = svg_top_x - pdf_top_x
svg_pdf_y_offset = svg_top_y - pdf_top_y

for svg_rect_id in svg_rects:
  for pdf_rect in pdf_rects:
    if 'pdf_rect' in svg_rects[svg_rect_id]:
      cur_pdf_x = float(svg_rects[svg_rect_id]['pdf_rect'][0])
      cur_pdf_y = float(svg_rects[svg_rect_id]['pdf_rect'][1])
      svg_x = float(svg_rects[svg_rect_id]['x'])
      svg_y = float(svg_rects[svg_rect_id]['y'])
      pdf_x = float(pdf_rect[0])
      pdf_y = float(pdf_rect[1])

      dist = math.sqrt(((pdf_x - svg_x + svg_pdf_x_offset)**2) + ((pdf_y - svg_y + svg_pdf_y_offset)**2))
      cur_dist = math.sqrt(((cur_pdf_x - svg_x + svg_pdf_x_offset)**2) + ((cur_pdf_y - svg_y + svg_pdf_y_offset)**2))

      if cur_dist > dist:
        svg_rects[svg_rect_id]['pdf_rect'] = pdf_rect
    else:
      svg_rects[svg_rect_id]['pdf_rect'] = pdf_rect

print(svg_rects)

###############################
# Verify all expected pdf rects
###############################
print("Verifying expected rects")
missing_rects = len(svg_rects)

for svg_id in svg_rects:
  if 'pdf_rect' in svg_rects[svg_id]:
    missing_rects = missing_rects - 1

if missing_rects > 0:
  print('''
    Expected at least {0} rects in PDF '{1}', found {2} instead.
  '''.format(len(svg_rects), pdf_in_path, len(svg_rects) - missing_rects))
  exit(-1)

###############
# Gen PDF links
###############
print("Generating PDF Links...")

pdf_links = []
annot_refs = []

for svg_id in svg_rects:
  svg_rect = svg_rects[svg_id]
  link_obj = in_pdf.create_new_object()
  annotation_values = {}
  annotation_values['S'] = PDFValue(PDFValue.NAME, 'URI')
  annotation_values['URI'] = PDFValue(PDFValue.STRING, links[svg_id])
  link_obj.named_values['A'] = PDFValue(PDFValue.DICTIONARY, annotation_values)
  rect_array = []
  rect_array.append(PDFValue(PDFValue.FLOAT, svg_rect['pdf_rect'][0]))
  rect_array.append(PDFValue(PDFValue.FLOAT, svg_rect['pdf_rect'][1]))
  rect_array.append(PDFValue(PDFValue.FLOAT, svg_rect['pdf_rect'][0] + float(svg_rect['width'])))
  rect_array.append(PDFValue(PDFValue.FLOAT, svg_rect['pdf_rect'][1] - float(svg_rect['height'])))
  border_array = []
  border_array.append(PDFValue(PDFValue.INT, 2))
  border_array.append(PDFValue(PDFValue.INT, 2))
  border_array.append(PDFValue(PDFValue.INT, 2))
  border_array.append(PDFValue(PDFValue.INT, 2))
  link_obj.named_values['Rect'] = PDFValue(PDFValue.ARRAY, rect_array)
  link_obj.named_values['Subtype'] = PDFValue(PDFValue.NAME, 'Link')
  link_obj.named_values['Type'] = PDFValue(PDFValue.NAME, 'Annot')
  link_obj.named_values['Border'] = PDFValue(PDFValue.ARRAY, border_array)
  annot_refs.append(PDFValue(PDFValue.REFERENCE, link_obj.get_ref()))

# ONLY 1 page PDF support for now
for key, obj in in_pdf.objects.items():
  if 'Type' in obj.named_values and obj.named_values['Type'].value == 'Page':
    obj.named_values['Annots'] = PDFValue(PDFValue.ARRAY, annot_refs)

# Write PDF
###########
PDFWriter.write_file(in_pdf, pdf_out_path)

