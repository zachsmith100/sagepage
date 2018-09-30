import os
import re
import sys
import math
import csv
import html
import zlib
from html.parser import HTMLParser
from utils.pdf import PDF
from utils.pdf import PDFParser
from utils.pdf import ParserReader
from utils.pdf import PDFValue
from utils.pdf import PDFContentStreamParser
from utils.pdf import PDFWriter

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

################################################################################
# Load SVG Rects
################################################################################
print("Loading SVG rects from file: {0}".format(svg_path))
svg_rects = []

class SVGHTMLParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.origin_x = 0
    self.origin_y = 0

  def handle_starttag(self, tag, attrs):
    if tag.lower() == 'svg':
      data = {i[0]:i[1] for i in attrs}
      if 'x' in data:
        self.origin_x = float(data['x'])
      if 'y' in data:
        self.origin_y = float(data['y'])
      print(self.origin_x, self.origin_y)

    if tag.lower() == "rect":
      rect_data = {i[0]:i[1] for i in attrs}
      if 'id' not in rect_data:
        return
      if rect_data['id'] in links:
        r = dict(rect_data)
        r['x'] = float(r['x']) + self.origin_x
        r['y'] = float(r['y']) + self.origin_y
        svg_rects.append(r)

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
  def get_page_objects(pdf):
    root_obj = None
    for key, obj in pdf.objects.items():
      obj_type = None
      if 'Type' in obj.named_values:
        obj_type = obj.named_values['Type']
      if obj_type is not None and obj_type.value == 'Pages':
        root_obj = obj
        break
    if root_obj is None:
      raise ValueError("Expected element 'Pages' missing from PDF")
    if 'Kids' not in root_obj.named_values:
      raise ValueError("Expected element 'Kids' missing from Pages object")
    pages = [o.value for o in root_obj.named_values['Kids'].value]
    return pages

  def get_content_objects(pdf, page_refs):
    content_refs = [pdf.objects[ref.get_key()].named_values['Contents'].value for ref in page_refs if 'Contents' in pdf.objects[ref.get_key()].named_values]
    content_objects = [pdf.objects[ref.get_key()] for ref in content_refs]
    return content_objects
  
  def decompress_content_stream(obj):
    decompressed = obj.stream_data
    if 'Filter' in obj.named_values:
      if obj.named_values['Filter'].value == 'FlateDecode':
        decompressed = zlib.decompress(obj.stream_data).decode()
      else:
        raise ValueError("Unsupported Filter type '{0}'".format(obj.named_values['Filter']))
    return decompressed

  def recompress_content_stream(obj):
    compressed = obj.stream_data
    if 'Filter' in obj.named_values:
      if obj.named_values['Filter'].value == 'FlateDecode':
        compressed = zlib.compress(obj.stream_data)
      else:
        raise ValueError("Unsupported Filter type '{0}'".format(obj.named_values['Filter']))
    return compressed

  def parse_content_stream(content_stream):
    commands = []
    def append_command(cmd):
        commands.append(cmd)
    reader = ParserReader()
    parser = PDFContentStreamParser(append_command)
    result = reader.read_string(parser.begin, content_stream)
    if result:
      return commands
    raise ValueError("Content stream parsing failed")

class PDFLinkRects:
  def pull_rects(color, pdf):
    selected_coords = []
    # Get 1st Page
    ##############
    pages = PDFLinkRectsUtils.get_page_objects(pdf)
    first_page_ref = pages[0]
    first_page = pdf.objects[first_page_ref.get_key()]
    
    # Get Content Obj
    #################
    content_objects = PDFLinkRectsUtils.get_content_objects(pdf, [first_page_ref])
    content_object = content_objects[0]

    # Get Media Box
    ###############
    mb = first_page.named_values['MediaBox']
    media_box = [mb.value[0].value, mb.value[1].value, mb.value[2].value, mb.value[3].value]

    # Load Commands
    ###############
    stream_data = PDFLinkRectsUtils.decompress_content_stream(content_object)
    commands = PDFLinkRectsUtils.parse_content_stream(stream_data)

    # Filter Commands
    #################
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

    # Update Commands
    #################
    content_object.stream_data = "\n".join([str(cmd) for cmd in output_commands]).encode()
    content_object.stream_data = PDFLinkRectsUtils.recompress_content_stream(content_object)
    content_object.named_values['Length'] = PDFValue(PDFValue.INT, len(content_object.stream_data))

    # Return Results
    ################
    selected_coords.extend([(cmd.params[0].value, cmd.params[1].value, cmd.params[2].value, cmd.params[3].value) for cmd in selected_commands])
    return (media_box, selected_coords)
        
media_box, pdf_rects = PDFLinkRects.pull_rects(PDFDeviceRGBColor(1.0, 0, 1.0), in_pdf)

################################################################################
# Match Rects
################################################################################
print("Matching rects...")

svg_rects.sort(key = lambda r: ( int(r['x']) << 10) & int(r['y']))
pdf_rects.sort(key = lambda r: (int(r[0]) << 10) & int(media_box[3] - r[1]) )

for r in svg_rects:
  print(r['x'], r['y'], 'key', str(r['x']) + str(r['y']))

if len(pdf_rects) < len(svg_rects):
    print("WARNING: Expected {0} rects in PDF '{1}', found {2} instead".format(len(svg_rects), pdf_in_path, len(pdf_rects)))
    exit(-1)

for i in range(len(svg_rects)):
  svg_ratio = float(svg_rects[i]['width']) / float(svg_rects[i]['height'])
  pdf_ratio = pdf_rects[i][0] / pdf_rects[i][1]

  if abs(svg_ratio - pdf_ratio) > 0.1:
    print("WARNING: expected link rect ratio: {0} received: {1}".format(svg_ratio, pdf_ratio))

  svg_rects[i]['pdf_rect'] = pdf_rects[i]

###############
# Gen PDF links
###############
print("Generating PDF Links...")

pdf_links = []
annot_refs = []

for svg_rect in svg_rects:
  if 'pdf_rect' not in svg_rect:
    print("PDF rect missing: {0}".format(svg_rect['id']))
    continue
  url = links[svg_rect['id']]

  if url is None or len(url.strip()) < 1:
    continue

  link_obj = in_pdf.create_new_object()
  annotation_values = {}
  annotation_values['S'] = PDFValue(PDFValue.NAME, 'URI')
  annotation_values['URI'] = PDFValue(PDFValue.STRING, url)
  link_obj.named_values['A'] = PDFValue(PDFValue.DICTIONARY, annotation_values)
  rect_array = []
  rect_array.append(PDFValue(PDFValue.FLOAT, svg_rect['pdf_rect'][0]))
  rect_array.append(PDFValue(PDFValue.FLOAT, svg_rect['pdf_rect'][1]))
  rect_array.append(PDFValue(PDFValue.FLOAT, svg_rect['pdf_rect'][0] + float(svg_rect['pdf_rect'][2])))
  rect_array.append(PDFValue(PDFValue.FLOAT, svg_rect['pdf_rect'][1] - float(abs(svg_rect['pdf_rect'][3]))))
  border_array = []
  border_array.append(PDFValue(PDFValue.INT, 0))
  border_array.append(PDFValue(PDFValue.INT, 0))
  border_array.append(PDFValue(PDFValue.INT, 0))
  border_array.append(PDFValue(PDFValue.INT, 0))
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

