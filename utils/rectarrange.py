import math
from utils.models import Rect
from utils.models import Size
from utils.svg import SVG

# Arrangeable
#############
class Arrangeable:
  def __init__(self, identifier, rects, ratio, matrix_svg_filename=None):
    self.identifier = identifier
    self.ratio = ratio
    self.rects = rects
    self.matrix_svg_filename = matrix_svg_filename
    self.arrange_rects = ArrangeRects()
    self.matrix = AreaMatrix(0,0) 

  def get_rects(self):
    return self.rects

  def list_free_rects(self):
    return self.matrix.list_free_rects()

  def select_fit(self, rect, trial_rects):
    return self.matrix.select_fit(rect, trial_rects)

  def arrange(self):
    self.matrix = self.arrange_rects.arrange(self.rects, self.ratio, ArrangeRects.default_sort_key, self.matrix_svg_filename)

  def get_allocated_size(self):
    return self.matrix.get_allocated_size()

  def overlay_onto_matrix(self, dst_origin_col_index, dst_origin_row_index, dst_matrix):
    self.matrix.overlay_matrix(dst_origin_row_index, dst_origin_col_index, dst_matrix)

  def dump_svg(self):
    if self.matrix_svg_filename:
      self.matrix.dump_svg(self.matrix_svg_filename)

##########
# FreeCell
##########
class FreeCell:
  def __init__(self, identifier, color=None):
    self.identifier = identifier
    self.color = color

  def set_color(self, color):
    self.color = color

  def get_color(self):
    return self.color

  def is_free(self):
    if self.color is None:
      return True
    return False

  def __str__(self):
    return 'FreeCell({0}, {1}, is_free()=>{2})'.format(self.identifier, self.color, self.is_free())

  def __repr__(self):
    return self.__str__()

############
# AreaMatrix
############
class AreaMatrix:
  def __init__(self, width, height):
    self.width = width
    self.height = height
    self.row_heights = []
    self.column_widths = []
    self.rows = []
    self.columns = []
    self.next_id = 0

    cell = FreeCell(self.get_next_id())
    self.rows.append([cell])
    self.row_heights.append(height)
    self.columns.append([cell])
    self.column_widths.append(width)

  def dump_svg(self, filename):
    rects = []
    y = 0
    for row_index in range(len(self.rows)):
      x = 0
      height = self.row_heights[row_index]
      for col_index in range(len(self.columns)):
        width = self.column_widths[col_index]
        cell = self.rows[row_index][col_index]
        rect = Rect(cell.identifier, x, y, width, height, cell.color)
        rects.append(rect)
        x = x + width
      y = y + height

    SVG.dump_rects(filename, rects)

  def get_next_id(self):
    next_id = self.next_id
    self.next_id = self.next_id + 1
    return 'AreaMatrix.internal_cell.{0}'.format(next_id)

  def mark_cell(self, col_index, row_index, color):
    self.columns[col_index][row_index].set_color(color)

  def split_row(self, row_index, new_height):
    old_height = self.row_heights[row_index]
    self.row_heights[row_index] = new_height
    new_row_height = old_height - new_height

    new_row = []
    for col_index in range(len(self.columns)):
      cell = FreeCell(self.get_next_id(), self.rows[row_index][col_index].color)
      new_row.append(cell)

    for col_index in range(len(new_row)):
      cell = new_row[col_index]
      self.columns[col_index].insert(row_index + 1, cell)

    self.rows.insert(row_index + 1, new_row)
    self.row_heights.insert(row_index + 1, new_row_height)

  def split_column(self, col_index, new_width):
    old_width = self.column_widths[col_index]
    self.column_widths[col_index] = new_width
    new_col_width = old_width - new_width

    new_col = []
    for row_index in range(len(self.rows)):
      new_col.append(FreeCell(self.get_next_id(), self.columns[col_index][row_index].color))

    for row_index in range(len(self.rows)):
      cell = new_col[row_index]
      self.rows[row_index].insert(col_index + 1, cell)

    self.columns.insert(col_index + 1, new_col)
    self.column_widths.insert(col_index + 1, new_col_width)

  def get_column_free_height(self, origin_col_index, origin_row_index, max_height=-1):
    height = 0
    row_index = origin_row_index
    while row_index < len(self.rows) and self.rows[row_index][origin_col_index].is_free():
      if max_height > -1 and (height + self.row_heights[row_index]) > max_height:
        break
      height = height + self.row_heights[row_index]
      row_index = row_index + 1
    return height

  def list_free_rects_for_cell(self, origin_col_index, origin_row_index):
    rects = []
    last_height = -1
    width = 0
    next_col_index = origin_col_index
    while next_col_index < len(self.columns) and self.columns[next_col_index][origin_row_index].is_free():
      next_height = self.get_column_free_height(next_col_index, origin_row_index, last_height)
      width = width + self.column_widths[next_col_index]
      if next_height != last_height and last_height > -1:    
        next_height = min(last_height, next_height)
        rects.append(Rect(None, origin_col_index, origin_row_index, width, last_height))
      last_height = next_height
      next_col_index = next_col_index + 1

    if last_height > 0:
      rects.append(Rect(None, origin_col_index, origin_row_index, width, last_height))      

    return rects

  def list_free_rects(self):
    free_rects = []
    for row_index in range(len(self.rows)):
      for col_index in range(len(self.columns)):
        cell_free_rects = self.list_free_rects_for_cell(col_index, row_index)
        if cell_free_rects is not None:
          free_rects.extend(cell_free_rects)
    return free_rects

  def select_fit(self, test_rect, trial_rects):
    selected_rect = None
    for rect in trial_rects:
      if rect.width < test_rect.width or rect.height < test_rect.height:
        continue
      if selected_rect is None:
        selected_rect = rect
      elif rect.y < selected_rect.y:
        if rect.x < selected_rect.x:
          selected_rect = rect
    return selected_rect

  def place_rect(self, origin_col_index, origin_row_index, rect):
    remaining_width = rect.width
    remaining_height = rect.height

    # Split col
    ###########
    split_col_index = origin_col_index
    next_width = self.column_widths[split_col_index]
    while remaining_width > next_width:
      remaining_width = remaining_width - next_width
      split_col_index = split_col_index + 1
      next_width = self.column_widths[split_col_index]

    if remaining_width > 0:
      self.split_column(split_col_index, remaining_width)

    # Split row
    ###########
    split_row_index = origin_row_index
    next_height = self.row_heights[split_row_index]
    while remaining_height > next_height:
      remaining_height = remaining_height - next_height
      split_row_index = split_row_index + 1
      next_height = self.row_heights[split_row_index]

    if remaining_height > 0:
      self.split_row(split_row_index, remaining_height)

    # Mark
    ######
    for col_index in range(origin_col_index, split_col_index + 1):
      for row_index in range(origin_row_index, split_row_index + 1):
        cell = self.rows[row_index][col_index]
        cell.color = rect.get_color()
        cell.identifier = rect.identifier

    return Rect(None, origin_col_index, origin_row_index, split_col_index, split_row_index)

  def update_rects_xy(self, rects):
    rects_xref = {r.identifier:r for r in rects}
    x = 0
    y = 0
    for col_index in range(len(self.columns)):
      for row_index in range(len(self.rows)):
        cell_id = self.rows[row_index][col_index].identifier
        if cell_id not in rects_xref:
          continue
        rect = rects_xref[cell_id]
        rect.x = x
        rect.y = y
        y = y + self.row_heights[row_index]
      x = x + self.column_widths[col_index]

  def overlay_matrix_cells(self, dst_origin_col_index, dst_origin_row_index, dst_matrix):
    src_col_width = 0
    for src_col_index in range(len(self.columns)):
      src_col_width = src_col_width + self.column_widths[src_col_index]
      dst_col_width = 0
      dst_col_index = dst_origin_col_index
      while dst_col_index < len(dst_matrix.columns):
        dst_col_width = dst_col_width + dst_matrix.column_widths[dst_col_index]
        if dst_col_width >= src_col_width:
          break
        dst_col_index = dst_col_index + 1
      
      if dst_col_width > src_col_width:
        split_distance = src_col_width - (dst_col_width - dst_matrix.column_widths[dst_col_index])
        dst_matrix.split_column(dst_col_index, split_distance)
        print("column: split_distance", split_distance, "src_col_index", src_col_index, 'src_col_width', src_col_width, 'dst_col_index', dst_col_index, 'dst_col_width', dst_col_width)
      elif dst_col_width == src_col_width:
        # boundaries already match
        break
      else:
        # src col width covers beyond this dst cell
        break

    src_row_height = 0
    for src_row_index in range(len(self.rows)):
      src_row_height = src_row_height + self.row_heights[src_row_index]
      dst_row_height = 0
      dst_row_index = dst_origin_row_index
      while dst_row_index < len(dst_matrix.rows):
        dst_row_height = dst_row_height + dst_matrix.row_heights[dst_row_index]
        if dst_row_height >= src_row_height:
          break
        dst_row_index = dst_row_index + 1

      if dst_row_height > src_row_height:
        split_distance = src_row_height - (dst_row_height - dst_matrix.row_heights[dst_row_index])
        dst_matrix.split_row(dst_row_index, split_distance)
        print("row: split_distance", split_distance, "src_row_index", src_row_index, 'src_row_height', src_row_height, 'dst_row_index', dst_row_index, 'dst_row_height', dst_row_height)
      elif dst_row_height == src_row_height:
        # boundaries already match
        break
      else:
        # src row covers beyond this dst cell
        break

  def iterate_cells(self, start_col_index, start_row_index, callback_f, **kwargs):
    x = 0
    width = 0
    for col_index in range(start_col_index, len(self.columns)):
      width = self.column_widths[col_index]
      y = 0
      height = 0
      for row_index in range(start_row_index, len(self.rows)):
        height = self.row_heights[row_index]
        cell = self.rows[row_index][col_index]
        if callback_f(col_index, row_index, x, y, width, height, cell, **kwargs) is not True:
          return
        y = y + height
      x = x + width

  def iterate_dump_cb(self, col_index, row_index, x, y, w, h, cell, **kwargs):
    print('x', x, 'y', y, 'w', w, 'h', h, 'cell', cell)
    return True

  def overlapping_cells_cb(self, col_index, row_index, x, y, w, h, cell, **kwargs):
    dst_matrix = kwargs['dst_matrix']
    dst_origin_col_index = kwargs['dst_origin_col_index']
    dst_origin_row_index = kwargs['dst_origin_row_index']
    print('col_index', col_index, 'row_index', row_index, 'x', x, 'y', y, 'w', w, 'h', h, 'cell', cell)
    
    dst_matrix.iterate_cells(dst_origin_col_index, dst_origin_row_index, self.process_overlapping_cells_cb, src_x=x, src_y=y, src_width=w, src_height=h, src_cell=cell)
    return True

  def intersect(self, src_x, src_y, src_width, src_height, dst_x, dst_y, dst_width, dst_height):
        if src_x >= (dst_x + dst_width) or (src_x + src_width) <= (dst_x):
            return False
        if src_y >= (dst_y + dst_height) or (src_y + src_height) <= (dst_y):
            return False
        return True

  def process_overlapping_cells_cb(self, col_index, row_index, dst_x, dst_y, dst_width, dst_height, dst_cell, **kwargs):
    src_x = kwargs['src_x']
    src_y = kwargs['src_y']
    src_width = kwargs['src_width']
    src_height = kwargs['src_height']
    src_cell = kwargs['src_cell']


    if src_cell.is_free():
      return True
    if dst_width == 20 and dst_height == 20 and src_width == 20 and src_height == 20:
      pass
      #print('src_x', src_x, 'src_y', src_y, 'src_width', src_width, 'src_height', src_height, 'dst_x', dst_x, 'dst_y', dst_y, 'dst_width', dst_width, 'dst_height', dst_height, 'src_cell', src_cell, 'dst_cell', dst_cell)
      #if self.intersect(src_x, src_y, src_width, src_height, dst_x, dst_y, dst_width, dst_height):
        #print("DST20")


    #if dst_cell.is_free() is not True:
      #print('src_x', src_x, 'src_y', src_y, 'src_width', src_width, 'src_height', src_height, 'dst_x', dst_x, 'dst_y', dst_y, 'dst_width', dst_width, 'dst_height', dst_height, 'src_cell', src_cell, 'dst_cell', dst_cell)
      #raise ValueError("Destination cell already occupied!")

    if self.intersect(src_x, src_y, src_width, src_height, dst_x, dst_y, dst_width, dst_height):
      print('intersect', src_cell)
      print('src_x', src_x, 'src_y', src_y, 'src_width', src_width, 'src_height', src_height, 'dst_x', dst_x, 'dst_y', dst_y, 'dst_width', dst_width, 'dst_height', dst_height, 'src_cell', src_cell, 'dst_cell', dst_cell)
      dst_cell.color = src_cell.color
      dst_cell.identifier = src_cell.identifier

    return True

  def overlay_matrix(self, dst_origin_col_index, dst_origin_row_index, dst_matrix):
    #print(len(self.rows), len(self.columns), origin_col_index, origin_row_index, len(matrix.rows), len(matrix.columns))

    #dst_matrix.dump_svg('../tmp/debug.dst.999.svg')
    #self.dump_svg('../tmp/debug.src.999.svg')

    self.overlay_matrix_cells(dst_origin_col_index, dst_origin_row_index, dst_matrix)

    #dst_matrix.dump_svg('../tmp/debug.dst.1000.svg')
    #self.dump_svg('../tmp/debug.src.1000.svg')
    
#    self.iterate_rects(0, 0, self.overlapping_cells_cb, dst_matrix=dst_matrix)


    # this one
    self.iterate_cells(0, 0, self.overlapping_cells_cb, dst_matrix=dst_matrix, dst_origin_col_index=dst_origin_col_index, dst_origin_row_index=dst_origin_row_index)

    #print(len(self.rows), len(self.columns), dst_origin_col_index, origin_row_index, len(matrix.rows), len(matrix.columns))
  
    '''
    src_x = 0
    src_y = 0
    src_width = 0
    for src_col_index in range(len(self.columns)):
      src_width = src_width + self.column_widths[src_col_index]
      src_height = 0
      for src_row_index in range(len(self.rows)):
        src_height = src_height + self.row_heights[src_row_index]

        print(src_x, src_y, src_width, src_height)
        src_cell = self.rows[src_row_index][src_col_index]

        src_y = src_y + src_height
      src_x = src_x + src_width
    '''

        #overlay_row_index = origin_row_index + row_index
        #overlay_cell = matrix.rows[row_index][col_index]
        #self.rows[overlay_row_index][overlay_col_index] = FreeCell(overlay_cell.identifier, overlay_cell.color)

  def get_max_size(self):
    return Size(self.width, self.height)

  def get_allocated_size(self):
    x = 0
    width = 0
    height = 0
    for col_index in range(len(self.columns)):
      y = 0
      x = x + self.column_widths[col_index]
      for row_index in range(len(self.rows)):
        cell = self.rows[row_index][col_index]
        y = y + self.row_heights[row_index]
        if cell.is_free():
          continue
        if width < x:
          width = x
        if height < y:
          height = y
    return Size(width, height)


  def __str__(self):
    s = 'AreaMatrix(width={0}, height={1}, rows={2}, cols={3})'.format(self.width, self.height, len(self.rows), len(self.columns))
    return s 

  def __repr__(self):
    return self.__str__()


##############
# ArrangeRects
##############
class ArrangeRects:
  def __init__(self):
    pass

  def get_placement_coord(self, rect):
    x = 0
    y = 0
    
  def get_enclosing_rect_for_area(self, area):
    unit_square = area/self.ratio
    h = math.sqrt(unit_square)
    w = h * self.ratio

    if ((w*1000) % 10) > 0:
      w = int(w) + 1
    else:
      w = int(w)

    if ((h*1000) % 10) > 0:
      h = int(h) + 1
    else:
      h = int(h)

    return Size(w,h)


  def attempt_arrangement(self, matrix, rects):
    for rect in rects:
      free_rects = matrix.list_free_rects()

      selected_rect = matrix.select_fit(rect, free_rects)

      if selected_rect is None:
        return False

      matrix.place_rect(selected_rect.x, selected_rect.y, rect)

    return True

  def default_sort_key(r):
    return r.width * r.height

  def arrange(self, rects, ratio, rect_sort_key_f, matrix_svg_filename=None):
    self.ratio = ratio
    matrix = AreaMatrix(0,0)

    rects.sort(key=rect_sort_key_f, reverse=True)

    width = 0
    height = 0
    area = 0
    for rect in rects:
      area = area + (rect.width * rect.height)

    while True:
      enclosing_rect = self.get_enclosing_rect_for_area(area)
      print("Attempting enclosing rect", enclosing_rect.width, enclosing_rect.height)
      matrix = AreaMatrix(enclosing_rect.width, enclosing_rect.height)
      if self.attempt_arrangement(matrix, rects):
        matrix.update_rects_xy(rects)
        print("Found arrangement", enclosing_rect)
        if matrix_svg_filename is not None:
          matrix.dump_svg(matrix_svg_filename)
        break
      area = area + int(area * 0.1)

    return matrix

  def attempt_arrangeables_arrange(self, matrix, arrangeables):
    i = 0
    for arrangeable in arrangeables:
      size = arrangeable.get_allocated_size()

      print('ARRANGING', arrangeable.identifier, 'arrangeable size', size)

      rect = Rect(arrangeable.identifier, 0, 0, size.width, size.height, 'red')

      free_rects = matrix.list_free_rects()

      selected_rect = matrix.select_fit(rect, free_rects)

      if selected_rect is None:
        return False

      print('selected_rect', selected_rect, 'free_rects', free_rects)

      arrangeable.overlay_onto_matrix(selected_rect.x, selected_rect.y, matrix)

      print(arrangeable.identifier, 'i', i)
      matrix.dump_svg('../tmp/debug.{0}.svg'.format(i))
      i = i + 1
      if i == 2:
        return True

    return True

  def arrange_arrangeables(self, arrangeables, ratio, matrix_svg_filename=None):
    self.ratio = ratio
    arrangeable_sizes = []
    rects = []

    for arrangeable in arrangeables:
      arrangeable.arrange()
      arrangeable_sizes.append(arrangeable.get_allocated_size())
      rects.extend(arrangeable.get_rects())

    width = 0
    height = 0
    area = 0
    for size in arrangeable_sizes:
      area = area + (size.width * size.height)

    arrangeables.sort(key=lambda a: (a.get_allocated_size().width * a.get_allocated_size().height), reverse=True)

    while True:
      enclosing_rect = self.get_enclosing_rect_for_area(area)
      print("Attempting enclosing rect", enclosing_rect.width, enclosing_rect.height)
      matrix = AreaMatrix(enclosing_rect.width, enclosing_rect.height)
      if self.attempt_arrangeables_arrange(matrix, arrangeables):
        matrix.update_rects_xy(rects)
        print("Found arrangement", enclosing_rect)
        if matrix_svg_filename is not None:
          matrix.dump_svg(matrix_svg_filename)
        break
      area = area + int(area * 0.1)
    



