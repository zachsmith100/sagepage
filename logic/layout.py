import cairo
import io
import logic.context
from utils.html import HTMLElement
from utils.html import HTMLStyleBuilder
from utils.permutations import OptimizableRange
from utils.permutations import ParamCombinationGenerator

#########
# Globals
#########
class Globals:
  next_element_id = 0

  def get_next_element_id():
    next_id = Globals.next_element_id
    Globals.next_element_id = Globals.next_element_id + 1
    return next_id

##############
# Configurable
##############
class Configurable:
  def load_config(self, config):
    for key in self.__dict__:
      if key in config:
        setattr(self, key, config[key])

#############
# TextExtents
#############
class TextExtents:
  def __init__(self):
    self.x_bearing = 0
    self.y_bearing = 0
    self.width = 0
    self.height = 0
    self.x_advance = 0
    self.y_advance = 0
    self.font_ascent = 0
    self.font_descent = 0
    self.font_height = 0
    self.font_max_x_advance = 0
    self.font_max_y_advance = 0

###########
# TextUtils
###########
class TextUtils:
  def get_text_dimensions(font_name, font_size, bold=False, text=None):
    extents = TextExtents()
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
    if text is not None and len(text) > 0:
      text_extents = ctx.text_extents(text)
      extents.x_bearing = text_extents.x_bearing
      extents.y_bearing = text_extents.y_bearing
      extents.width = text_extents.width
      extents.height = text_extents.height
      extents.x_advance = text_extents.x_advance
      extents.y_advance = text_extents.y_advance
    font_extents = ctx.font_extents()
    extents.font_ascent = font_extents[0]
    extents.font_descent = font_extents[1]
    extents.font_height = font_extents[2]
    extents.font_max_x_advance = font_extents[3]
    extents.font_max_y_advance = font_extents[4]
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

################
# OptimizeLayout
################
class OptimizeLayout:
  def optimize_layout_for_ratio(layout, group_name, group, ratio):
    params = None
    if callable(getattr(layout, "get_area_params", None)):  
      params = layout.get_area_params(group)
      if len(params) < 1:
        params = None

    if params == None:
      svg = layout.get_svg(group_name, group)
      return svg

    generator = ParamCombinationGenerator(params)

    values = generator.next()

    ratio_diff = 0
    selected_svg = None

    while values is not None:
      layout.load_config(values)

      svg = layout.get_svg(group_name, group)

      w = float(svg.attributes['width'].value)
      h = float(svg.attributes['height'].value)
      new_ratio = h/w
      new_ratio_diff = abs(ratio - new_ratio)
      print(w,h, new_ratio, new_ratio_diff)

      if ratio_diff == 0 or new_ratio_diff < ratio_diff:
        ratio_diff = abs(ratio - new_ratio)
        selected_svg = svg

      values = generator.next()

    return selected_svg

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
      text_extents = TextUtils.get_text_dimensions(self.font_name, self.font_size, False, entry.text)
      if text_extents.width > width:
        width = text_extents.width
      if first:
        first = False
      else:
        height = height + self.row_spacing
      height = height + text_extents.font_height
    return (width, height)

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
    font_extents = TextUtils.get_text_dimensions(self.font_name, self.font_size)
    # Get text coords
    ###################
    text_coords = []
    x = self.border_width
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      col_width = col_sizes[col_index][0]
      y = self.border_width + font_extents.font_ascent
      coord_col = []
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index]
        text_extents = TextUtils.get_text_dimensions(self.font_name, self.font_size, False, entry.text)
        coord = (x, y, text_extents.width, text_extents.height)
        coord_col.append(coord)
        y = y + self.row_spacing + font_extents.font_height
      x = x + col_width + self.col_spacing
      text_coords.append(coord_col)
    # Output SVG
    ############
    html = HTMLElement('svg')
    html.set_attr('width', str(layout_rect_size[0])).set_attr('height', str(layout_rect_size[1]))
    bg_rect = HTMLElement('rect').set_attr('id', group_name).set_attr('width', str(layout_rect_size[0]))
    bg_rect.set_attr('height', str(layout_rect_size[1]))
    bg_rect.set_attr('style', HTMLStyleBuilder().set('fill', self.background_color))
    html.add_child(bg_rect)
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index] 
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().set('font-name', self.font_name).set('font-size', self.font_size).set('fill', self.font_color)
        html.add_child(HTMLElement('text').set_text(entry.text).set_attr('x', str(coord[0])).set_attr('y', str(coord[1])).set_attr('style', str(style)))
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index] 
        if entry.url is None or len(entry.url.strip()) < 1:
          continue
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().set('fill', 'rgb(255,0,255)').set('fill-opacity', '0.25')
        rect_element = HTMLElement('rect')
        rect_element.set_attr('id', '{0}.{1}'.format(entry.group, entry.identifier))
        rect_element.set_attr('x', str(coord[0])).set_attr('y', str(coord[1] - font_extents.font_ascent))
        rect_element.set_attr('width', str(coord[2])).set_attr('height', font_extents.font_height).set_attr('style', style)
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
      entries = self.get_glossary_entries(group)
      params.append(OptimizableRange('col_count', 1, int(len(entries) / 2), 1))
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
        if idx == len(glossary_entries):
          break
        if (j + 1) == row_count and glossary_entries[idx].bold:
          # Letter header can't be last entry of column
          continue
        column.append(glossary_entries[idx])
        idx = idx + 1
      columns.append(column)
    return columns 

  def get_col_size(self, column):
    width = 0
    height = 0
    first = True
    for entry in column:
      text_extents = TextUtils.get_text_dimensions(self.font_name, entry.font_size, entry.bold, entry.text)
      if text_extents.width > width:
        width = text_extents.width
      if first:
        first = False
      else:
        height = height + self.row_spacing
      height = height + text_extents.font_height
    return (width, height)

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
        text_extents = TextUtils.get_text_dimensions(self.font_name, entry.font_size, False, entry.text)
        y = y + text_extents.font_ascent
        coord = (x, y, text_extents.width, text_extents.height)
        coord_col.append(coord)
        y = y + self.row_spacing + text_extents.font_descent
      x = x + col_width + self.col_spacing
      text_coords.append(coord_col)
    # Output SVG
    ############
    html = HTMLElement('svg')
    html.set_attr('width', str(layout_rect_size[0])).set_attr('height', str(layout_rect_size[1]))
    bg_rect = HTMLElement('rect').set_attr('id', group_name).set_attr('width', str(layout_rect_size[0]))
    bg_rect.set_attr('height', str(layout_rect_size[1]))
    bg_rect.set_attr('style', HTMLStyleBuilder().set('fill', self.background_color))
    html.add_child(bg_rect)
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index] 
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().set('font-name', self.font_name).set('font-size', entry.font_size).set('fill', self.font_color)
        if entry.bold:
          style.set('font-weight', 'bold')
        html.add_child(HTMLElement('text').set_text(entry.text).set_attr('x', str(coord[0])).set_attr('y', str(coord[1])).set_attr('style', str(style)))
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index]
        if entry.url is None or len(entry.url.strip()) < 1:
          continue
        extents = TextUtils.get_text_dimensions(self.font_name, entry.font_size, entry.bold, entry.text)
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().set('fill', 'rgb(255,0,255)').set('fill-opacity', '0.25')
        rect_element = HTMLElement('rect')
        if entry.identifier is None:
          rect_element.set_attr('id', Globals.get_next_element_id())
        else:
          rect_element.set_attr('id', entry.identifier)
        rect_element.set_attr('x', str(coord[0])).set_attr('y', str(coord[1]- extents.font_ascent))
        rect_element.set_attr('width', str(coord[2])).set_attr('height', extents.font_height).set_attr('style', style)
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
      extents = TextUtils.get_text_dimensions(self.font_name, self.font_size, False, entry.text)
      if extents.width > width:
        width = extents.width
      if first:
        first = False
      else:
        height = height + self.row_spacing
      height = height + extents.font_height
    return (width, height)

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
    font_extents = TextUtils.get_text_dimensions(self.font_name, self.font_size)
    # Get text coords
    ###################
    text_coords = []
    x = self.border_width
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      col_width = col_sizes[col_index][0]
      y = self.border_width + font_extents.font_ascent
      coord_col = []
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index]
        text_extents = TextUtils.get_text_dimensions(self.font_name, self.font_size, False, entry.text)
        coord = (x, y, text_extents.width, text_extents.height)
        coord_col.append(coord)
        y = y + self.row_spacing + font_extents.font_height
      x = x + col_width + self.col_spacing
      text_coords.append(coord_col)
    # Output SVG
    ############
    html = HTMLElement('svg')
    html.set_attr('width', str(layout_rect_size[0])).set_attr('height', str(layout_rect_size[1]))
    bg_rect = HTMLElement('rect').set_attr('id', group_name).set_attr('width', str(layout_rect_size[0]))
    bg_rect.set_attr('height', str(layout_rect_size[1]))
    bg_rect.set_attr('style', HTMLStyleBuilder().set('fill', self.background_color))
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
        rect = HTMLElement('rect').set_attr('id', '{0}.column{1}'.format(group_name, col_index))
        rect.set_attr('x', str(x))
        rect.set_attr('y', str(y))  
        rect.set_attr('width', str(width))
        rect.set_attr('height', str(layout_rect_size[1]))
        rect.set_attr('style', HTMLStyleBuilder().set('fill', color).set('fill-opacity', str(self.column_transparencies[col_index])))
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
        y = y + font_extents.font_height + self.row_spacing
      if i % 2:
        width = layout_rect_size[0] - (2 * self.border_width)
        height = font_extents.font_height
        rect = HTMLElement('rect').set_attr('id', '{0}.row_alt{1}'.format(group_name, i))
        rect.set_attr('x', str(x))
        rect.set_attr('y', str(y))  
        rect.set_attr('width', str(width))
        rect.set_attr('height', str(height))
        rect.set_attr('style', HTMLStyleBuilder().set('fill', self.row_alt_color).set('fill-opacity', str(self.row_alt_transparency)))
        html.add_child(rect)
    # Text
    ######
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index] 
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().set('font-name', self.font_name).set('font-size', self.font_size).set('fill', self.font_color)
        html.add_child(HTMLElement('text').set_text(entry.text).set_attr('x', str(coord[0])).set_attr('y', str(coord[1])).set_attr('style', str(style)))
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index] 
        if entry.url is None or len(entry.url.strip()) < 1:
          continue
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().set('fill', 'rgb(255,0,255)').set('fill-opacity', '0.25')
        rect_element = HTMLElement('rect')
        rect_element.set_attr('id', '{0}.{1}'.format(entry.group, entry.identifier))
        rect_element.set_attr('x', str(coord[0])).set_attr('y', str(coord[1] - font_extents.font_ascent))
        rect_element.set_attr('width', str(coord[2])).set_attr('height', font_extents.font_height).set_attr('style', style)
        html.add_child(rect_element)
    return html

################
# ParseResult
################
class ParseResult:
  def __init__(self, error_msg, peer_parse_func, next_parse_func, stream_bytes=None):
    self.error_msg = error_msg
    self.peer_parse_func = peer_parse_func
    self.next_parse_func = next_parse_func
    self.stream_bytes = stream_bytes

###############
# ParserBase
###############
class ParserBase:
  def __init__(self, set_value):
    self.set_value = set_value

##############
# ParserReader
##############
class ParserReader:
  def __init__(self):
    pass

  def set_pdf(self, pdf):
    self.pdf = pdf


  def read_string(self, parser, input_string):
    result = False
    with io.BytesIO(bytearray(input_string.encode())) as reader:
      result = self.parse(parser, reader)
    return result


  def read_file(self, parser, filename):
    result = False
    with open(filename, 'rb') as f:
      result = self.parse(parser, f)
    return result

  def parse(self, parser, reader):
    stack = []
    stack.append(parser)
    next_byte_index = 0
    bytes = []
    bytes_read = 0
    next_parser = stack.pop()
    flushed = False

    b = reader.read(1)

    if b != b"":
      bytes.append(b[0])

    while bytes_read < len(bytes):
      if next_parser is None:
        break
 
      next_byte = bytes[bytes_read]
      
      bytes_read += 1

      peer_parser = next_parser
     
      while peer_parser is not None:
        #print("byte: {0} byte_index: {1} f: {2}".format(chr(next_byte), next_byte_index, peer_parser.__qualname__))
        result = peer_parser(next_byte, next_byte_index)

        if result.error_msg is not None:
          print("{0}: byte: {1} byte_index: {2} message: {3}".format(peer_parser.__qualname__, next_byte, next_byte_index, result.error_msg))
          return False

        if result.next_parse_func is not None:
          stack.append(result.next_parse_func)
        
        peer_parser = result.peer_parse_func
    
      if result.stream_bytes is not None:
        stream = []
        stream.extend(result.stream_bytes)
        stream.extend(bytes[bytes_read:])
        bytes = stream
        bytes_read = 0
      elif bytes_read == len(bytes):
        bytes = []
        bytes_read = 0
        b = reader.read(1)
        if b == b"":
          if flushed == False:
            flushed = True
            bytes.append(0)
        else:
          bytes.append(b[0])
          next_byte_index += 1

  
      next_parser = None

      if len(stack) > 0:
        next_parser = stack.pop()

    return True

###############
# PyTokenParser
###############
class PyTokenParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.token = []

  def is_special(self, c):
    if c.isalpha():
      return False
    if c.isdigit():
      return False
    return True

  def set_token(self):
    self.set_value(''.join(self.token))

  def begin(self, b, n):
    if str(chr(b)).isspace():
      self.token.append(chr(b))
      return ParseResult(None, None, self.read_whitespace)
    return ParseResult(None, self.read, None)

  def read_whitespace(self, b, n):
    if str(chr(b)).isspace():
      self.token.append(chr(b))
      return ParseResult(None, None, self.read_whitespace)
    self.set_token()
    return ParseResult(None, None, None, [b])

  def read(self, b, n):
    if str(chr(b)).isspace():
      self.set_token()
      return ParseResult(None, None, None, [b])

    if self.is_special(str(chr(b))):
      if len(self.token) == 0:
          self.token.append(chr(b))
          self.set_token()
          return ParseResult(None, None, None)
      self.set_token()
      return ParseResult(None, None, None, [b])

    self.token.append(chr(b))
    return ParseResult(None, None, self.read)

############
# PyFragment
############
class PyFragment:
  KEYWORD = 'keyword'
  NUMBER = 'number'
  STRING = 'string'
  COMMENT = 'comment'
  TOKEN = 'token'
  
  def __init__(self, t, v):
    self.type = t
    self.value = v

  def __str__(self):
    return "{0}({1})".format(self.type, self.value)

  def __repr__(self):
    return self.__str__()

################
# PySyntaxParser
################
class PySyntaxParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.fragments = []
    self.keywords = {
      'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 
      'def', 'del', 'elif', 'else', 'except', 'False', 'finally', 'for', 'from',
      'global', 'if', 'import', 'in', 'is', 'lambda', 'None', 'nonlocal',
      'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'with', 'yield'}

  def set_last_token(self, token):
    self.last_token = token

  def begin(self, b, n):
    return ParseResult(None, PyTokenParser(self.set_last_token).begin, self.process_token)

  def process_token(self, b, n):
    if self.last_token in self.keywords:
      self.fragments.append(PyFragment(PyFragment.KEYWORD, self.last_token))
      return ParseResult(None, self.begin, None)
    elif self.last_token == "'":
      self.string_token = []
      self.quote_char = "'"
      return ParseResult(None, self.read_string, None)
    elif self.last_token == '"':
      self.string_token = []
      self.quote_char = '"'
      return ParseResult(None, self.read_string, None)
    elif self.last_token == '#':
      self.comment = []
      self.comment.append('#')
      return ParseResult(None, self.read_comment, None)
    self.fragments.append(PyFragment(PyFragment.TOKEN, self.last_token))
    return ParseResult(None, self.begin, None)

  def read_comment(self, b, n):
    if b == 0:
      self.fragments.append(PyFragment(PyFragment.COMMENT, ''.join(self.comment)))
      return ParseResult(None, None, None)
    self.comment.append(chr(b))
    return ParseResult(None, None, self.read_comment)

  def read_string(self, b, n):
    if chr(b) == self.quote_char:
      self.fragments.append(PyFragment(PyFragment.STRING, "{0}{1}{0}".format(self.quote_char, ''.join(self.string_token))))
      return ParseResult(None, None, self.begin)
    self.string_token.append(chr(b))
    return ParseResult(None, None, self.read_string)


#######################
# PythonSyntaxHilighter
#######################
class PythonSyntaxSVGHilighter:
  def __init__(self, font_name, font_size, font_color, line_spacing):
    self.font_name = font_name
    self.font_size = font_size
    self.font_color = font_color
    self.line_spacing = line_spacing

  def get_hilighted_line_element(self, line, x, y):
    reader = ParserReader()
    parser = PySyntaxParser(None)
    reader.read_string(parser.begin, line)

    spans = []
    cur_token_span = HTMLElement('tspan')
    style = HTMLStyleBuilder().set('font-name', self.font_name).set('font-size', self.font_size).set('fill', self.font_color)
    cur_token_span.set_attr('style', str(style))
    for frag in parser.fragments:
      normalized = frag.value.replace(' ', '&#160;')
      if frag.type == PyFragment.TOKEN:
        cur_token_span.text = cur_token_span.text + normalized
        continue

      spans.append(cur_token_span)
      cur_token_span = HTMLElement('tspan')
      style.set('fill', self.font_color)
      cur_token_span.set_attr('style', str(style))

      if frag.type == PyFragment.KEYWORD:
        style.set('fill', 'rgb(0,0,255)')
        span = HTMLElement('tspan')
        span.set_attr('style', str(style))
        span.set_text(normalized)
        spans.append(span)        
      elif frag.type == PyFragment.STRING:
        style.set('fill', 'rgb(255,0,0)')
        span = HTMLElement('tspan')
        span.set_attr('style', str(style))
        span.set_text(normalized)
        spans.append(span)
      elif frag.type == PyFragment.COMMENT:
        style.set('fill', 'rgb(128,0,128)')
        span = HTMLElement('tspan')
        span.set_attr('style', str(style))
        span.set_text(normalized)
        spans.append(span)

    if len(cur_token_span.text) > 0:
      spans.append(cur_token_span)

    line_element = HTMLElement('tspan')
    style = HTMLStyleBuilder().set('font-name', self.font_name).set('font-size', self.font_size).set('fill', self.font_color)
    line_element.set_attr('style', str(style)).set_attr('x', str(x)).set_attr('y', str(y))
    for span in spans:
      line_element.add_child(span)
    return line_element

    
  def get_text_element(self, text, x, y):
    font_extents = TextUtils.get_text_dimensions(self.font_name, self.font_size)
    lines_element = HTMLElement('text')
    style = HTMLStyleBuilder().set('font-name', self.font_name).set('font-size', self.font_size).set('fill', self.font_color)
    lines_element.set_attr('style', str(style))
    lines = text.split('\n')
    line_x = x
    line_y = y
    first = True
    for line in lines:
      if first:
        first = False
        line_y = line_y + font_extents.font_ascent
      else:
        line_y = line_y + self.line_spacing
        line_y = line_y + font_extents.font_height
      line_element = self.get_hilighted_line_element(line, line_x, line_y)
      lines_element.add_child(line_element)
    return lines_element

###############
# CodeletLayout
###############
class CodeletLayout(Configurable):
  def __init__(self):
    Configurable.__init__(self)
    self.col_count = 0
    self.border_width = 2
    self.row_spacing = 0
    self.col_spacing = 10
    self.header_border_width = 0
    self.header_title_spacing = 0
    self.header_font_name = 'sans-serif'
    self.header_font_size = 10
    self.header_font_color = 'rgb(255,255,255)'
    self.header_background_color = 'rgb(77,77,77)'
    self.header_transparency = 1.0
    self.font_name = 'sans-serif'
    self.font_color = 'rgb(0,0,0)'
    self.font_size = 10
    self.background_color = 'rgb(236,236,236)'
    self.background_transparency = 1.0
    self.line_spacing = 3
    self.entries = {}

  def get_area_params(self, group):
    params = []
    if self.col_count < 1:
      params.append(OptimizableRange('col_count', 1, int(len(group)), 1))
    return params

  def get_text_rect(self, entry):
    lines = entry.text.split('\n')
    width = 100
    for line in lines:
      text_extents = TextUtils.get_text_dimensions(self.font_name, self.font_size, False, line.rstrip())
      test_width = text_extents.x_advance
      if test_width > width:
        width = test_width
    height = (text_extents.font_height * len(lines)) + ((len(lines) - 1) * self.line_spacing)
    return (width, height)

  def get_entry_rect(self, entry):
    header_height = self.get_header_height()
    text_rect = self.get_text_rect(entry)
    width = text_rect[0] + (2 * self.border_width)
    height = text_rect[1] + (2 * self.border_width) + header_height
    return (width, height)

  def get_col_size(self, column):
    width = 0
    height = 0
    for entry in column:
      entry_rect = self.get_entry_rect(entry)
      height = height + entry_rect[1]
      if width < entry_rect[0]:
        width = entry_rect[0]
    return (width, height)

  def get_header_height(self):
    title_extents = TextUtils.get_text_dimensions(self.header_font_name, self.header_font_size, True)
    subtitle_extents = TextUtils.get_text_dimensions(self.header_font_name, self.header_font_size, False)
    height = (title_extents.font_height + subtitle_extents.font_height) + (2 * self.header_border_width) + self.header_title_spacing
    return height

  def get_group_rect(self, group, col_sizes):
    width = 0
    height = 0
    for size in col_sizes:
      width = width + size[0]
      if height < size[1]:
        height = size[1]
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
    font_extents = TextUtils.get_text_dimensions(self.font_name, self.font_size)

    # Build HTML
    ############
    html = HTMLElement('svg')
    html.set_attr('width', str(layout_rect_size[0])).set_attr('height', str(layout_rect_size[1]))
    x = 0
    header_height = self.get_header_height()
    for i in range(len(columns)):
      column = columns[i]
      col_size = col_sizes[i]
      y = 0
      for entry in column:
        # Background Rect
        #################
        entry_size = self.get_entry_rect(entry)
        bg_rect = HTMLElement('rect').set_attr('id', '{0}.{1}.bg_rect'.format(entry.group, entry.identifier))
        bg_rect.set_attr('width', str(col_size[0])).set_attr('height', str(entry_size[1]))
        bg_rect.set_attr('x', str(x)).set_attr('y', str(y))
        bg_rect.set_attr('style', HTMLStyleBuilder().set('fill', self.background_color))
        html.add_child(bg_rect)

        # Header Rect
        #############
        header_rect = HTMLElement('rect').set_attr('id', '{0}.{1}.header_rect'.format(entry.group, entry.identifier))
        header_rect.set_attr('width', str(col_size[0])).set_attr('height', str(header_height))
        header_rect.set_attr('x', str(x)).set_attr('y', str(y))
        header_rect.set_attr('style', HTMLStyleBuilder().set('fill', self.header_background_color))
        html.add_child(header_rect)

        # Title
        #######
        title = self.entries[entry.identifier]['title']
        subtitle = self.entries[entry.identifier]['subtitle']
        title_extents = TextUtils.get_text_dimensions(self.header_font_name, self.header_font_size, True, title)
        title_x = x + (col_size[0] / 2) - (title_extents.width / 2)

        if len(subtitle) > 0:
          title_y = y + self.header_border_width + title_extents.font_ascent
        else:
          title_y = y + (header_height / 2) + title_extents.font_descent


        style = HTMLStyleBuilder().set('fill', self.header_font_color).set('font-weight', 'bold')
        style.set('font-name', self.header_font_name).set('font-size', self.header_font_size)
        title_element = HTMLElement('text').set_attr('x', str(title_x)).set_attr('y', str(title_y)).set_attr('style', style)
        title_element.set_text(title)
        html.add_child(title_element)

        # Subtitle
        ##########
        if len(subtitle) > 0:
          subtitle_extents = TextUtils.get_text_dimensions(self.header_font_name, self.header_font_size, False, subtitle)
          subtitle_x = x + (col_size[0] / 2) - (subtitle_extents.width / 2)
          subtitle_y = title_y + title_extents.font_descent + self.header_title_spacing + subtitle_extents.font_ascent  
          style = HTMLStyleBuilder().set('fill', self.header_font_color)
          style.set('font-name', self.header_font_name).set('font-size', self.header_font_size)
          subtitle_element = HTMLElement('text').set_attr('x', str(subtitle_x)).set_attr('y', str(subtitle_y)).set_attr('style', style)
          subtitle_element.set_text(subtitle)
          html.add_child(subtitle_element)

        # Text Body
        ###########
        hilighter = PythonSyntaxSVGHilighter(self.font_name, self.font_size, self.font_color, self.line_spacing)
        text_element = hilighter.get_text_element(entry.text, x + self.border_width, y + header_height + self.border_width)
        html.add_child(text_element)

        # Pink Link Rect
        ################
        style = HTMLStyleBuilder().set('fill', 'rgb(255,0,255)').set('fill-opacity', '0.25')
        rect_element = HTMLElement('rect')
        rect_element.set_attr('id', '{0}.{1}'.format(entry.group, entry.identifier))
        rect_element.set_attr('x', str(x)).set_attr('y', str(y))
        rect_element.set_attr('width', str(col_size[0])).set_attr('height', str(entry_size[1])).set_attr('style', style)
        html.add_child(rect_element)

        y = y + entry_size[1]
      x = x + col_size[0]

    return html

    # Get text coords
    ###################
    text_coords = []
    x = self.border_width
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      col_width = col_sizes[col_index][0]
      y = self.border_width + font_extents.font_ascent
      coord_col = []
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index]
        text_extents = TextUtils.get_text_dimensions(self.font_name, self.font_size, False, entry.text)
        coord = (x, y, text_extents.width, text_extents.height)
        coord_col.append(coord)
        y = y + self.row_spacing + font_extents.font_height
      x = x + col_width + self.col_spacing
      text_coords.append(coord_col)
    # Output SVG
    ############
    html = HTMLElement('svg')
    html.set_attr('width', str(layout_rect_size[0])).set_attr('height', str(layout_rect_size[1]))
    bg_rect = HTMLElement('rect').set_attr('id', group_name).set_attr('width', str(layout_rect_size[0]))
    bg_rect.set_attr('height', str(layout_rect_size[1]))
    bg_rect.set_attr('style', HTMLStyleBuilder().set('fill', self.background_color))
    html.add_child(bg_rect)

    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index] 
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().set('font-name', self.font_name).set('font-size', self.font_size).set('fill', self.font_color)
        html.add_child(HTMLElement('text').set_text(entry.text).set_attr('x', str(coord[0])).set_attr('y', str(coord[1])).set_attr('style', str(style)))
    for col_index in range(len(columns)):
      col_entries = columns[col_index]
      coord_col = text_coords[col_index]
      for row_index in range(len(col_entries)):
        entry = col_entries[row_index] 
        if entry.url is None or len(entry.url.strip()) < 1:
          continue
        coord = coord_col[row_index]
        style = HTMLStyleBuilder().set('fill', 'rgb(255,0,255)').set('fill-opacity', '0.25')
        rect_element = HTMLElement('rect')
        rect_element.set_attr('id', '{0}.{1}'.format(entry.group, entry.identifier))
        rect_element.set_attr('x', str(coord[0])).set_attr('y', str(coord[1] - font_extents.font_ascent))
        rect_element.set_attr('width', str(coord[2])).set_attr('height', font_extents.font_height).set_attr('style', style)
        html.add_child(rect_element)
    return html    