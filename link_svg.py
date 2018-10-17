import sys
import csv
from html.parser import HTMLParser

from utils.html import HTMLElement
from utils.html import HTMLStyleBuilder
from utils.models import LinkEntry


################################################################################
# Command line
################################################################################
if len(sys.argv) != 4:
  print('Usage: {0} <csv-links-file> <input-svg-file> <output-svg-file>'.format(sys.argv[0]))
  exit(1)

links_csv_filename = sys.argv[1]
input_svg_filename = sys.argv[2]
output_svg_filename = sys.argv[3]

################################################################################
# Load CSV
################################################################################
links = {}
with open(links_csv_filename, 'r') as csv_file:
  csv_reader = csv.reader(csv_file)
  for link in csv_reader:
    name = link[0] + '.' + link[1]
    links[name] = LinkEntry(link[0], link[1], link[2], link[3])

################################################################################
# Load Links
################################################################################
identifiers = []

class InputSVGHtmlParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.root_element = None
    self.current_element = None
    self.stack = []
    self.max_len = 0
   
  def handle_starttag(self, tag, attrs):
    global links
    data = {i[0]:i[1] for i in attrs}

    element = HTMLElement(tag)
    for key in data:
      element.set_attr(key, data[key])


    if tag == 'rect':
      style = data['style']
      style_parts = style.split(';')
      pink_rect = False
      style_builder = HTMLStyleBuilder()

      for style_part in style_parts:
        attr_parts = style_part.split(':')
        name = attr_parts[0]
        value = attr_parts[1]
        if name == 'fill' and value == 'rgb(255,0,255)':
          pink_rect = True
        style_builder.set(name, value)

      if pink_rect:
        style_builder.set('fill-opacity', '0.0')
        element.set_attr('style', str(style_builder))
        a_element = HTMLElement('a')
        link_id = data['id']
        link = links[link_id].url
        a_element.set_attr('href', link).set_attr('target', '_blank')
        a_element.add_child(element)
        element = a_element

    
    if self.root_element is None:
      self.root_element = element
      self.current_element = element
    else:
      self.current_element.add_child(element)
    self.stack.append(self.current_element)
    self.current_element = element

    if len(self.stack) > self.max_len:
      self.max_len = len(self.stack)



  def handle_endtag(self, tag):
    self.current_element = self.stack.pop()
    
  def handle_data(self, data):
    if self.current_element:
      self.current_element.set_text(data)
    pass

parser = InputSVGHtmlParser()

with open(input_svg_filename, 'r') as f:
  parser.feed(f.read())

################################################################################
# Output
################################################################################

def test_iterate(element):
  print(element.name)

#parser.root_element.iterate_children(test_iterate)

#print(parser.max_len)

with open(output_svg_filename, 'w') as f:
  f.write(str(parser.root_element))
  pass