import math
import cairo
import csv
import sys
import json

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

###########
# TextUtils
###########
class TextUtils:
  def get_text_dimensions(text, font_name, font_size, font_style=cairo.FONT_SLANT_NORMAL, font_weight=cairo.FONT_WEIGHT_NORMAL):
    WIDTH, HEIGHT = 1024, 1024
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)
    ctx.scale(WIDTH, HEIGHT)  # Normalizing the canvas
    ctx.set_source_rgb(0.1, 0.1, 0.1)            
    ctx.select_font_face(font_name, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(font_size)
    extents = ctx.text_extents(text)
    font_extents = ctx.font_extents()
    return (extents.width, extents.height, font_extents[0], font_extents[1], font_extents[2])

  def get_font_extents(font_name, font_size, font_style=cairo.FONT_SLANT_NORMAL, font_weight=cairo.FONT_WEIGHT_NORMAL):
    WIDTH, HEIGHT = 1024, 1024
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)
    ctx.scale(WIDTH, HEIGHT)  # Normalizing the canvas
    ctx.set_source_rgb(0.1, 0.1, 0.1)            
    ctx.select_font_face(font_name, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(font_size)
    extents = ctx.font_extents()
    return extents


###########
# LinkEntry
###########
class LinkEntry:
  def __init__(self, group, identifier, text, url):
    self.group = group
    self.identifier = identifier
    self.text = text
    self.url = url

  def __str__(self):
    return self.text
    #return "{0}.{1}.{2} '{3}' url='{4}'".format(self.community, self.group, self.identifier, self.text, self.url)

  def __repr__(self):
    return self.__str__()

############
# LayoutMeta
############
class LayoutMeta:
  def __init__(self):
    self.groups = {}

#################
# LayoutGroup
#################
class LayoutGroup:
  def __init__(self, name, config):
    self.name = name
    self.config = config
    self.entries = {}

##############
# Layout
##############
class Layout:
  def load_config(self, config):
    for key in self.__dict__:
      if key in config:
        setattr(self, key, config[key])

######################
# SimpleWordListLayout
######################
class SimpleWordListLayout(Layout):
  def __init__(self):
    Layout.__init__(self)
    self.font_name = 'sans-serif'
    self.font_size = 10
    self.col_count = 0
    self.border_width = 0
    self.row_spacing = 0
    self.col_spacing = 10
    self.background_color = 'rgb(236,236,236)'
    self.font_color = 'rgb(0,0,255)'

  def get_col_size(self, config, column):
    width = 0
    height = 0
    first = True
    for entry in column:
      size = TextUtils.get_text_dimensions(entry.text, self.font_name, self.font_size)
      if size[0] > width:
        width = size[0]
      if first:
        first = False
      else:
        height = height + self.row_spacing
      height = height + size[4]
    return (width, height)

  def get_row_height(self, group, row_entries):
    extents = TextUtils.get_text_dimensions(entry.text, self.font_name, self.font_size)
    return extents[4]

  def get_group_rect(self, group, col_sizes):
    width = (2*self.border_width)
    height = 0
    first = True
    for size in col_sizes:
      if first:
        first = False
      else:
        width = width + self.col_spacing
      width = width + size[0]
      if size[1] > height:
        height = size[1]
    height = height + (2*self.border_width)
    return (width, height)

  def get_svg(self, group_name, group):
    # Init Entries
    ##############
    row_count = int(len(group) / self.col_count)
    if len(group) % self.col_count:
      row_count = row_count + 1
    columns = [group[i:i+row_count] for i in range(0, len(group), row_count)]
    rows = []
    for i in range(row_count):
      row = []
      for j in range(len(columns)):
        next_index = (j*row_count) + i
        if next_index < len(group):
          row.append(group[next_index])
      rows.append(row)
    # Get col sizes
    ###############
    col_sizes = []
    for column in columns:
      col_sizes.append(self.get_col_size(self, column))
    # Get Group Rect
    ################
    layout_rect_size = self.get_group_rect(group, col_sizes)
    # Get Font Extents
    ##################
    font_extents = TextUtils.get_font_extents(self.font_name, self.font_size)
    font_height = font_extents[2]
    font_ascent = font_extents[0]
    font_descent = font_extents[1]
    # Get text coords
    ###################
    text_coords = []
    x = self.border_width
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      col_width = col_sizes[col_index][0]
      y = self.border_width + font_ascent
      coord_col = []
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index]
        text_rect = TextUtils.get_text_dimensions(entry.text, self.font_name, self.font_size)
        # coord = (x + ((col_width - text_rect[0])/2), y, text_rect[0], text_rect[1])
        coord = (x, y, text_rect[0], text_rect[1])
        coord_col.append(coord)
        y = y + self.row_spacing + font_height
      x = x + col_width + self.col_spacing
      text_coords.append(coord_col)
    # Output SVG
    ############
    html = HTMLElement('svg')
    html.add_attr('width', str(layout_rect_size[0])).add_attr('height', str(layout_rect_size[1]))
    bg_rect = HTMLElement('rect').add_attr('id', group_name).add_attr('width', str(layout_rect_size[0]))
    bg_rect.add_attr('height', str(layout_rect_size[1]))
    bg_rect.add_attr('style', HTMLStyleBuilder().add('fill', self.background_color))
    html.add_child(bg_rect)
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index] 
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().add('font-name', self.font_name).add('font-size', self.font_size).add('fill', self.font_color)
        html.add_child(HTMLElement('text').set_text(entry.text).add_attr('x', str(coord[0])).add_attr('y', str(coord[1])).add_attr('style', str(style)))
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index] 
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().add('fill', 'rgb(255,0,255)').add('fill-opacity', '0.25')
        rect_element = HTMLElement('rect')
        rect_element.add_attr('id', '{0}.{1}'.format(entry.group, entry.identifier))
        rect_element.add_attr('x', str(coord[0])).add_attr('y', str(coord[1]-font_ascent))
        rect_element.add_attr('width', str(coord[2])).add_attr('height', font_height).add_attr('style', style)
        html.add_child(rect_element)
    return str(html)



################################################################################
# Command line
################################################################################
if len(sys.argv) != 4:
  print('Usage: %s <config.json> <links.csv> <output.svg>'
    % sys.argv[0], file=sys.stderr)
  exit(1)

config_path = sys.argv[1]
links_path = sys.argv[2]
output_path = sys.argv[3]

# Load Groups
#############
groups = {}
with open(links_path, 'r') as f: 
  csv_reader = csv.reader(f)
  for line in csv_reader:
    group_name = line[0].strip()
    identifier = line[1].strip()
    text = line[2].strip()
    url = line[3].strip()
    entry = LinkEntry(group_name, identifier, text, url)

    if group_name not in groups:
      groups[group_name] = []
    groups[group_name].append(entry)

# Load Config
#############
config = {}
with open(config_path, 'r') as f:
  config = json.loads(f.read())

# Generate SVG
##############
svg_outputs = {}
for name in groups:
  constructor = globals()[config[name]['layout_class']]
  layout = constructor()
  layout.load_config(config[name])
  svg = layout.get_svg(name, groups[name])
  svg_outputs[name] = svg

# Output
########
for name in svg_outputs:
  fn = '{0}/{1}.svg'.format(output_path, name)
  with open(fn, 'w') as f:
    f.write(svg_outputs[name])

exit(0)

meta = LayoutMeta()
community = LayoutCommunity('builtins', 'SimpleWordList')
community.row_count = 76
community.font_name = "sans-serif"
community.font_size = 10
community.border_width = 3
community.row_spacing = 1
community.col_spacing = 14
community.background_color = 'rgb(236,236,236)'
community.font_color = 'rgb(0,0,255)'
meta.communities[community.name] = community
group = LayoutGroup('a')
community.groups[group.name] = group

with open('builtins.csv', 'r') as f: 
  csv_reader = csv.reader(f)
  for line in csv_reader:
    entry = LinkEntry(line[0], line[1], line[2], line[3], line[4])
    meta.communities[entry.community].groups[entry.group].members.append(entry)

layout = SimpleWordListLayout()
layout.get_svg(meta.communities['builtins'])
