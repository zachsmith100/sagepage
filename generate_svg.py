import math
import cairo
import csv
import sys
import json

class Globals:
  next_element_id = 0

  def get_next_element_id():
    next_id = Globals.next_element_id
    Globals.next_element_id = Globals.next_element_id + 1
    return next_id

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
    self.attributes = {}
    self.children = []
    self.text = ''

  def add_attr(self, n, v):
    self.attributes[n] = HTMLAttribute(n,v)
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
    return "<{0} {1}>\n{2}{3}\n</{0}>\n".format(self.name, ' '.join([str(self.attributes[attr]) for attr in self.attributes]), "\n".join([str(child) for child in self.children]), self.text)

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
  def get_text_dimensions(text, font_name, font_size, bold=False):
    WIDTH, HEIGHT = 1024, 1024
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)
    ctx.scale(WIDTH, HEIGHT)  # Normalizing the canvas
    ctx.set_source_rgb(0.1, 0.1, 0.1)
    if bold:
      ctx.select_font_face(font_name, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    else:
      ctx.select_font_face(font_name, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(font_size)
    extents = ctx.text_extents(text)
    font_extents = ctx.font_extents()
    return (extents.width, extents.height, font_extents[0], font_extents[1], font_extents[2])

  def get_font_extents(font_name, font_size, bold=False):
    WIDTH, HEIGHT = 1024, 1024
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)
    ctx.scale(WIDTH, HEIGHT)  # Normalizing the canvas
    ctx.set_source_rgb(0.1, 0.1, 0.1)            
    if bold:
      ctx.select_font_face(font_name, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    else:
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
# Configurable
##############
class Configurable:
  def load_config(self, config):
    for key in self.__dict__:
      if key in config:
        setattr(self, key, config[key])

##################
# OptimizableRange
##################
class OptimizableRange:
  def __init__(self, name, start, end, step):
    self.name = name
    self.start = int(start)
    self.end = int(end)
    self.step = int(step)
    self.current = int(start)
    print(self.start, self.end)

  def next(self):
    if self.current >= self.end:
      return None
    result = self.current
    self.current = self.current + self.step
    return result

  def reset(self):
    self.current = self.start

######################
# SimpleWordListLayout
######################
class SimpleWordListLayout(Configurable):
  def __init__(self):
    Configurable.__init__(self)
    self.col_count = 0
    self.border_width = 0
    self.row_spacing = 0
    self.col_spacing = 10
    self.font_name = 'sans-serif'
    self.font_size = 10
    self.font_color = 'rgb(0,0,255)'
    self.background_color = 'rgb(236,236,236)'    

  def get_area_params(self, group):
    params = []
    if self.col_count < 1:
      params.append(OptimizableRange('col_count', 1, int(len(group) / 2), 1))
    return params

  def get_col_size(self, column):
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
      col_sizes.append(self.get_col_size(column))
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
        if entry.url is None or len(entry.url.strip()) < 1:
          continue
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().add('fill', 'rgb(255,0,255)').add('fill-opacity', '0.25')
        rect_element = HTMLElement('rect')
        rect_element.add_attr('id', '{0}.{1}'.format(entry.group, entry.identifier))
        rect_element.add_attr('x', str(coord[0])).add_attr('y', str(coord[1]-font_ascent))
        rect_element.add_attr('width', str(coord[2])).add_attr('height', font_height).add_attr('style', style)
        html.add_child(rect_element)
    return html

###############
# GlossaryEntry
###############
class GlossaryEntry:
  def __init__(self, identifier, text, url, font_size, bold):
    self.identifier = identifier
    self.text = text
    self.url = url
    self.font_size = font_size
    self.bold = bold

  def __str__(self):
    return '{0} {1} font_size: {2} bold: {3}'.format(self.text, self.url, self.font_size, self.bold)

  def __repr__(self):
    return self.__str__()

################
# GlossaryLayout
################
class GlossaryLayout(Configurable):
  def __init__(self):
    Configurable.__init__(self)
    self.font_name = 'sans-serif'
    self.font_size = 10
    self.col_count = 0
    self.border_width = 0
    self.row_spacing = 0
    self.col_spacing = 10
    self.background_color = 'rgb(236,236,236)'
    self.font_color = 'rgb(0,0,255)'

  def get_area_params(self, group):
    params = []
    if self.col_count < 1:
      params.append(OptimizableRange('col_count', 1, int(len(group) / 2), 1))
    return params

  def get_glossary_entries(self, group):
    entries = []
    last_letter = ' '
    for link in group:
      if last_letter != link.text[0] and link.text[0].isalpha():
        entries.append(GlossaryEntry(None, link.text[0].upper(), '', self.font_size + 2, True))
        last_letter = link.text[0]
      identifier = '{0}.{1}'.format(link.group, link.identifier)
      entries.append(GlossaryEntry(identifier, link.text, link.url, self.font_size, False))
    return entries

  def get_columns(self, glossary_entries):
    row_count = int(len(glossary_entries) / self.col_count)
    if len(glossary_entries) % self.col_count:
      row_count = row_count + 1
    columns = []
    idx = 0
    for i in range(self.col_count):
      column = []
      for j in range(row_count):
        if (j + 1) == row_count and glossary_entries[idx].bold:
          # Letter header can't be last entry of column
          continue
        column.append(glossary_entries[idx])
        idx = idx + 1
        if idx == len(glossary_entries):
          break
      columns.append(column)
    return columns 

  def get_col_size(self, column):
    width = 0
    height = 0
    first = True
    for entry in column:
      size = TextUtils.get_text_dimensions(entry.text, self.font_name, entry.font_size, entry.bold)
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
    entries = self.get_glossary_entries(group)
    columns = self.get_columns(entries)
    # Get col sizes
    ###############
    col_sizes = []
    for column in columns:
      col_sizes.append(self.get_col_size(column))
    # Get Group Rect
    ################
    layout_rect_size = self.get_group_rect(group, col_sizes)
    # Get text coords
    ###################
    text_coords = []
    x = self.border_width
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      col_width = col_sizes[col_index][0]
      y = self.border_width
      coord_col = []
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index]
        text_rect = TextUtils.get_text_dimensions(entry.text, self.font_name, entry.font_size)
        y = y + text_rect[2]
        coord = (x, y, text_rect[0], text_rect[1])
        coord_col.append(coord)
        y = y + self.row_spacing + text_rect[3]
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
        style = HTMLStyleBuilder().add('font-name', self.font_name).add('font-size', entry.font_size).add('fill', self.font_color)
        if entry.bold:
          style.add('font-weight', 'bold')
        html.add_child(HTMLElement('text').set_text(entry.text).add_attr('x', str(coord[0])).add_attr('y', str(coord[1])).add_attr('style', str(style)))
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index]
        if entry.url is None or len(entry.url.strip()) < 1:
          continue
        font_extents = TextUtils.get_font_extents(self.font_name, entry.font_size, entry.bold)
        font_ascent = font_extents[0]
        font_height = font_extents[2]
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().add('fill', 'rgb(255,0,255)').add('fill-opacity', '0.25')
        rect_element = HTMLElement('rect')
        if entry.identifier is None:
          rect_element.add_attr('id', Globals.get_next_element_id())
        else:
          rect_element.add_attr('id', entry.identifier)
        rect_element.add_attr('x', str(coord[0])).add_attr('y', str(coord[1]-font_ascent))
        rect_element.add_attr('width', str(coord[2])).add_attr('height', font_height).add_attr('style', style)
        html.add_child(rect_element)
    return html

#######################
# SimpleWordTableLayout
#######################
class SimpleWordTableLayout(Configurable):
  def __init__(self):
    Configurable.__init__(self)
    self.col_count = 0
    self.border_width = 0
    self.row_spacing = 0
    self.col_spacing = 10
    self.font_name = 'sans-serif'
    self.font_size = 10
    self.font_color = 'rgb(0,0,255)'
    self.background_color = 'rgb(236,236,236)'
    self.row_color = 'rgb(168, 168, 168'
    self.column_colors = []
    self.column_transparencies = []
    self.row_alt_color = 'rgb(0,0,0)'
    self.row_alt_transparency = 0.1

  def get_area_params(self, group):
    params = []
    if self.col_count < 1:
      params.append(OptimizableRange('col_count', 1, int(len(group) / 2), 1))
    return params

  def get_col_size(self, column):
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
      col_sizes.append(self.get_col_size(column))
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
    # Column Rects
    ##############
    if len(self.column_colors) == len(columns):
      x = self.border_width
      y = 0
      first = True
      for col_index in range(len(col_sizes)):
        size = col_sizes[col_index]
        width = size[0] 
        if first:
          first = False
        else:
          x = x + self.col_spacing
        color = self.column_colors[col_index]
        rect = HTMLElement('rect').add_attr('id', '{0}.column{1}'.format(group_name, col_index))
        rect.add_attr('x', str(x))
        rect.add_attr('y', str(y))  
        rect.add_attr('width', str(width))
        rect.add_attr('height', str(layout_rect_size[1]))
        rect.add_attr('style', HTMLStyleBuilder().add('fill', color).add('fill-opacity', str(self.column_transparencies[col_index])))
        html.add_child(rect)
        x = x + width
    # Row Alts
    ##########
    x = self.border_width
    y = self.border_width
    first = True
    for i in range(len(rows)):
      if first:
          first = False
      else:
        y = y + font_height + self.row_spacing
      if i % 2:
        width = layout_rect_size[0] - (2 * self.border_width)
        height = font_height
        rect = HTMLElement('rect').add_attr('id', '{0}.row_alt{1}'.format(group_name, i))
        rect.add_attr('x', str(x))
        rect.add_attr('y', str(y))  
        rect.add_attr('width', str(width))
        rect.add_attr('height', str(height))
        rect.add_attr('style', HTMLStyleBuilder().add('fill', self.row_alt_color).add('fill-opacity', str(self.row_alt_transparency)))
        html.add_child(rect)
    # Text
    ######
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
        if entry.url is None or len(entry.url.strip()) < 1:
          continue
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().add('fill', 'rgb(255,0,255)').add('fill-opacity', '0.25')
        rect_element = HTMLElement('rect')
        rect_element.add_attr('id', '{0}.{1}'.format(entry.group, entry.identifier))
        rect_element.add_attr('x', str(coord[0])).add_attr('y', str(coord[1]-font_ascent))
        rect_element.add_attr('width', str(coord[2])).add_attr('height', font_height).add_attr('style', style)
        html.add_child(rect_element)
    return html

class OptimizeLayoutParams:
  def __init__(self, layout):
    self.params = layout.get_area_params()

  def overlay_next(self, config):
    pass

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

class ParamCombinationGenerator:
  def __init__(self, params):
    self.params = params
    self.values = None
    self.cur_tail = 0

  def next(self):
    if self.cur_tail >= len(self.params):
      return None

    if self.values is None:
      self.cur_tail = 0
      self.values = {}
      for param in self.params:
        value = param.next()
        self.values[param.name] = value
      if len(self.values) < 1:
        return None
      return self.values

    value = self.params[0].next()

    if value is not None:
      self.values[self.params[0].name] = value
      return self.values

    for param_index in range(self.cur_tail + 1):
      value = self.params[param_index].next()

      if value is not None:
        self.values[self.params[param_index].name] = value
        return self.values

      self.params[param_index].reset()
      self.values[self.params[param_index].name] = self.params[param_index].next()
    
    self.cur_tail = self.cur_tail + 1

    if self.cur_tail < len(self.params):
      tail_name = self.params[self.cur_tail].name
      self.values[tail_name] = self.params[self.cur_tail].next()
      return self.values

    return None

''''
params = []
params.append(OptimizableRange('t0', 0, 3, 1))
params.append(OptimizableRange('t1', 0, 4, 1))
params.append(OptimizableRange('t2', 0, 3, 1))
cg = ParamCombinationGenerator(params)

values = cg.next()

while values is not None:
  print(values)
  values = cg.next()
'''

def optimize_layout(layout, group_name, group):
  params = None
  if callable(getattr(layout, "get_area_params", None)):  
    params = layout.get_area_params(group)
    if len(params) < 1:
      params = None

  if params == None:
    svg = layout.get_svg(name, group)
    return svg

  generator = ParamCombinationGenerator(params)

  values = generator.next()

  ratio = 1.618
  ratio_diff = 0
  selected_svg = None

  while values is not None:
    layout.load_config(values)

    svg = layout.get_svg(name, group)

    w = float(svg.attributes['width'].value)
    h = float(svg.attributes['height'].value)
    new_ratio = h/w
    new_ratio_diff = abs(ratio - new_ratio)
    print(w,h, new_ratio, new_ratio_diff)

    if ratio_diff == 0 or new_ratio_diff < ratio_diff:
      ratio_diff = abs(ratio - new_ratio)
      selected_svg = svg

    values = generator.next()

  print(str(selected_svg))

  return selected_svg


for name in groups:
  constructor = globals()[config[name]['layout_class']]
  layout = constructor()
  layout.load_config(config[name])
  svg = optimize_layout(layout, name, groups[name])
  svg_outputs[name] = str(svg)

# Output
########
for name in svg_outputs:
  fn = '{0}/{1}.svg'.format(output_path, name)
  with open(fn, 'w') as f:
    f.write(svg_outputs[name])