import math
import cairo
import csv

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
  def __init__(self, community, group, identifier, text, url):
    self.community = community
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
    self.communities = {}

#################
# LayoutCommunity
#################
class LayoutCommunity:
  def __init__(self, name, layout_type):
    self.name = name
    self.layout_type = layout_type
    self.groups = {}

#############
# LayoutGroup
#############
class LayoutGroup:
  def __init__(self, name):
    self.name = name
    self.members = []

###########################
# SimpleWordListLayoutUtils
###########################
class SimpleWordListLayoutUtils:
  def get_col_size(community, col_entries):
    width = 0
    height = 0
    first = True
    for entry in col_entries:
      size = TextUtils.get_text_dimensions(entry.text, community.font_name, community.font_size)
      if size[0] > width:
        width = size[0]
      if first:
        first = False
      else:
        height = height + community.row_spacing
      height = height + size[4]
    return (width, height)

  def get_row_height(community, row_entries):
    extents = TextUtils.get_text_dimensions(entry.text, community.font_name, community.font_size)
    return extents[4]

  def get_community_rect(community, col_sizes):
    width = (2*community.border_width)
    height = 0
    first = True
    for size in col_sizes:    
      if first:
        first = False
      else:
        width = width + community.col_spacing
      width = width + size[0]
      if size[1] > height:
        height = size[1]
    height = height + (2*community.border_width)
    return (width, height)

################
# SimpleWordListLayout
################
class SimpleWordListLayout:
  def __init__(self):
    pass

  def get_svg(self, community):
    # Init Entries
    ##############
    entries = []
    [entries.extend([entry for entry in group.members]) for name, group in community.groups.items()]
    columns = [entries[i:i+community.row_count] for i in range(0, len(entries), community.row_count)]
    rows = []
    for i in range(community.row_count):
      row = []
      for j in range(len(columns)):
        next_index = (j*community.row_count) + i
        if next_index < len(entries):
          row.append(entries[next_index])
      rows.append(row)
    # Get col sizes
    ###############
    col_sizes = []
    for col_entries in columns:
      col_sizes.append(SimpleWordListLayoutUtils.get_col_size(community, col_entries))
    # Get Community Rect
    ####################
    community_size = SimpleWordListLayoutUtils.get_community_rect(community, col_sizes)
    # Get Font Extents
    ##################
    font_extents = TextUtils.get_font_extents(community.font_name, community.font_size)
    font_height = font_extents[2]
    font_ascent = font_extents[0]
    font_descent = font_extents[1]
    print("font_ascent {0}".format(font_ascent))
    # Get text coords
    ###################
    text_coords = []
    x = community.border_width
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      col_width = col_sizes[col_index][0]
      y = community.border_width + font_ascent
      coord_col = []
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index]
        text_rect = TextUtils.get_text_dimensions(entry.text, community.font_name, community.font_size)
        # coord = (x + ((col_width - text_rect[0])/2), y, text_rect[0], text_rect[1])
        coord = (x, y, text_rect[0], text_rect[1])
        coord_col.append(coord)
        y = y + community.row_spacing + font_height
      x = x + col_width + community.col_spacing
      text_coords.append(coord_col)
    # Output SVG
    ############
    html = HTMLElement('svg')
    html.add_attr('width', str(community_size[0])).add_attr('height', str(community_size[1]))
    bg_rect = html.add_child(HTMLElement('rect').add_attr('width', str(community_size[0])).add_attr('height', str(community_size[1])))
    bg_rect.add_attr('style', HTMLStyleBuilder().add('fill', community.background_color))
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index] 
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().add('font-name', community.font_name).add('font-size', community.font_size).add('fill', community.font_color)
        html.add_child(HTMLElement('text').set_text(entry.text).add_attr('x', str(coord[0])).add_attr('y', str(coord[1])).add_attr('style', str(style)))
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index] 
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().add('fill', 'rgb(255,0,255)').add('fill-opacity', '0.25')
        rect_element = HTMLElement('rect')
        rect_element.add_attr('id', entry.identifier).add_attr('x', str(coord[0])).add_attr('y', str(coord[1]-font_ascent))
        rect_element.add_attr('width', str(coord[2])).add_attr('height', font_height).add_attr('style', style)
        html.add_child(rect_element)
    with open('test_out.svg', 'w') as f:
      html.render(f)


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
