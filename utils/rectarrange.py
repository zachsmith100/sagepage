import math
from utils.models import Rect
from utils.models import Size
from utils.svg import SVG
from utils.models import GridCoord
from utils.models import XYCoord

# Arrangeable
#############
class Arrangeable:
  def __init__(self, identifier):
    self.identifier = identifier
    self.ratio = 1.618
    self.rects = []
    self.matrix_svg_filename = None
    self.matrix = AreaMatrix(0,0)
    self.children = {}

  def add_child(self, arrangeable):
    self.children[arrangeable.identifier] = arrangeable
    return arrangeable

  def add_rects(self, rects):
    self.rects.extend(rects)

  def get_rects(self):
    return self.matrix.get_rects()

  def list_free_rects(self):
    return self.matrix.list_free_rects()

  def select_fit(self, rect, trial_rects):
    return self.matrix.select_fit(rect, trial_rects)

  def get_allocated_size(self):
    return self.matrix.get_allocated_size()

  def overlay_onto_matrix(self, dst_origin_col_index, dst_origin_row_index, dst_matrix):
    self.matrix.overlay_matrix(dst_origin_col_index, dst_origin_row_index, dst_matrix)

  def dump_svg(self):
    if self.matrix_svg_filename:
      self.matrix.dump_svg(self.matrix_svg_filename)

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

      if rect.identifier in self.children:
        self.children[rect.identifier].overlay_onto_matrix(selected_rect.x, selected_rect.y, matrix)
      else:
        cell_origin = matrix.get_relative_cell_origin_xy(0, 0, selected_rect.x, selected_rect.y)
        matrix.place_rect(cell_origin.x, cell_origin.y, rect)

    return True

  def arrange(self):
    child_rects = []
    for identifier in self.children:
      child = self.children[identifier]
      child.arrange()
      child_size = child.get_allocated_size()
      child_rects.append(Rect(child.identifier, 0, 0, child_size.width, child_size.height, 'blue'))

    arrangeable_rects = []
    arrangeable_rects.extend(self.rects)
    arrangeable_rects.extend(child_rects)
    
    width = 0
    height = 0
    area = 0
    for rect in arrangeable_rects:
      area = area + (rect.width * rect.height)

    arrangeable_rects.sort(key=lambda r: (r.width * r.height), reverse=True)

    while True:
      enclosing_rect = self.get_enclosing_rect_for_area(area)
      matrix = AreaMatrix(enclosing_rect.width, enclosing_rect.height)
      if self.attempt_arrangement(matrix, arrangeable_rects):
        self.matrix = matrix
        break
      area = area + int(area * 0.1)


####################
# EvenRectColumnFlow
####################
class EvenRectColumnFlow:
  def __init__(self, max_col_count):
    self.columns = []
    self.max_col_count = max_col_count

  def get_column(self, index):
    for i in range(len(self.columns), (index + 1)):
      self.columns.append([])
    return self.columns[index]

  def get_column_height(self, index):
    height = 0
    for cell in self.get_column(index):
      height = height + cell.height
    return height

  def get_max_col_height(self):
    height = 0
    for index in range(len(self.columns)):
      next_col_height = self.get_column_height(index)
      if height < next_col_height:
        height = next_col_height
    return height

  def get_last_element_height(self, col_index):
    if len(self.columns[col_index]) < 1:
      return 0
    return self.columns[col_index][-1].height

  def should_wrap(self, col_index):
    if (col_index + 1) >= self.max_col_count:
      return False

    if len(self.get_column(col_index)) < 1:
      return False

    col_height = self.get_column_height(col_index)
    next_col_height = self.get_column_height(col_index + 1)
    last_element_height = self.get_last_element_height(col_index)

    if col_height > (next_col_height + last_element_height):
      return True

    return False

  def push_rect(self, rect, col_index=0):
    self.get_column(col_index).insert(0, rect)
    while self.should_wrap(col_index):
      last_rect = self.get_column(col_index).pop()
      self.push_rect(last_rect, col_index + 1)
    

###################
# ColumnArrangeable
###################
class ColumnArrangeable(Arrangeable):
  def __init__(self, identifier):
    Arrangeable.__init__(self, identifier)
    self.column_count = 1
    self.rects = []
    self.matrix = AreaMatrix(0,0)
    self.columns = []
    self.column_widths = []
    self.column_heights = []

  def index_columns(self):
    flow = EvenRectColumnFlow(self.column_count)
    for rect in reversed(self.rects):
      flow.push_rect(rect)
    self.columns = flow.columns

  def get_col_widths(self):
    col_widths = []
    for column in self.columns:
      width = 0
      for cell in column:
        if cell.width > width:
          width = cell.width
      col_widths.append(width)
    return col_widths

  def get_col_heights(self):
    col_heights = []
    for column in self.columns:
      height = 0
      for cell in column:
        height = height + cell.height
      col_heights.append(height)
    return col_heights

  def arrange(self):
    child_rects = []
    for identifier in self.children:
      child = self.children[identifier]
      child.arrange()
      child_size = child.get_allocated_size()
      child_rects.append(Rect(child.identifier, 0, 0, child_size.width, child_size.height, 'blue'))
    self.add_rects(child_rects)

    self.index_columns()

    self.column_widths = self.get_col_widths()

    self.column_heights = self.get_col_heights()

    width = 0

    for col_width in self.column_widths:
      width = width + col_width

    height = 0

    for col_height in self.column_heights:
      if height < col_height:
        height = col_height

    self.matrix = AreaMatrix(width, height)

    x = 0
    for col_index in range(len(self.columns)):
      y = 0
      column = self.columns[col_index]
      for row_index in range(len(column)):
        cell_rect = column[row_index]
        cell_rect.x = x
        cell_rect.y = y
        if cell_rect.identifier in self.children:
          child = self.children[cell_rect.identifier]
          grid_coord = self.matrix.place_rect(x, y, cell_rect, False)
          child.overlay_onto_matrix(grid_coord.col, grid_coord.row, self.matrix)
        else:
          self.matrix.place_rect(x, y, cell_rect)
        y = y + cell_rect.height
      x = x + self.column_widths[col_index]

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
  next_id = 0
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
    self.cell_rect_xref = {}
    self.rects = {}

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
    next_id = AreaMatrix.next_id
    AreaMatrix.next_id = AreaMatrix.next_id + 1
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
        #if rect.x < selected_rect.x:
        selected_rect = rect
    return selected_rect

  def get_cell_grid_coord_for_xy(self, origin_col_index, origin_row_index, target_x, target_y):
    x = 0
    width = 0
    for col_index in range(origin_col_index, len(self.columns)):
      width = self.column_widths[col_index]
      y = 0
      for row_index in range(origin_row_index, len(self.rows)):
        height = self.row_heights[row_index]
        if x <= target_x and target_x <= (x + width) and y <= target_y and target_y <= (y + height):
          return GridCoord(col_index, row_index)
        y = y + height
      x = x + width
    return None

  def get_relative_cell_origin_xy(self, origin_col_index, origin_row_index, target_col_index, target_row_index):
    x = 0
    width = 0
    for col_index in range(origin_col_index, len(self.columns)):
      width = self.column_widths[col_index]
      y = 0
      for row_index in range(origin_row_index, len(self.rows)):
        height = self.row_heights[row_index]
        if target_col_index == (col_index - origin_col_index) and target_row_index == (row_index - origin_row_index):
          return XYCoord(x, y)
        y = y + height
      x = x + width
    return None

  def place_rect(self, x, y, rect, allocate=True):
    origin_cell_index = self.get_cell_grid_coord_for_xy(0, 0, x, y)

    if origin_cell_index is None:
      return None

    origin_cell_xy = self.get_relative_cell_origin_xy(0, 0, origin_cell_index.col, origin_cell_index.row)

    if origin_cell_xy is None:
      return None

    if x - origin_cell_xy.x > 0:
      self.split_column(origin_cell_index.col, x - origin_cell_xy.x)
      origin_cell_index.col = origin_cell_index.col + 1

    if y - origin_cell_xy.y > 0:
      self.split_row(origin_cell_index.row, y - origin_cell_xy.y)
      origin_cell_index.row = origin_cell_index.row + 1

    origin_cell_xy = self.get_relative_cell_origin_xy(0, 0, origin_cell_index.col, origin_cell_index.row)

    remaining_width = rect.width
    remaining_height = rect.height

    # Split col
    ###########
    split_col_index = origin_cell_index.col
    next_width = self.column_widths[split_col_index]
    while remaining_width > next_width:
      remaining_width = remaining_width - next_width
      if (split_col_index + 1) >= len(self.column_widths):
        # reached the end of the matrix
        break
      split_col_index = split_col_index + 1
      next_width = self.column_widths[split_col_index]

    if remaining_width > 0:
      self.split_column(split_col_index, remaining_width)

    # Split row
    ###########
    split_row_index = origin_cell_index.row
    next_height = self.row_heights[split_row_index]
    while remaining_height > next_height:
      remaining_height = remaining_height - next_height
      if (split_row_index + 1) >= len(self.row_heights):
        # reached the end of the matrix
        break
      split_row_index = split_row_index + 1
      next_height = self.row_heights[split_row_index]

    if remaining_height > 0:
      self.split_row(split_row_index, remaining_height)

    # Mark
    ######
    if allocate:
      for col_index in range(origin_cell_index.col, split_col_index + 1):
        for row_index in range(origin_cell_index.row, split_row_index + 1):
          cell = self.rows[row_index][col_index]
          cell.color = rect.get_color()
          self.cell_rect_xref[cell.identifier] = rect.identifier
          self.rects[rect.identifier] = rect

    return origin_cell_index

  def get_rects(self):
    self.update_rects_xy()
    rects = [self.rects[cell_id] for cell_id in self.rects]
    return rects

  def update_rects_xy(self):
    x = 0
    seen = set()
    for col_index in range(len(self.columns)):
      y = 0
      for row_index in range(len(self.rows)):
        cell = self.rows[row_index][col_index]
        cell_rect_id = None
        if cell.identifier in self.cell_rect_xref:
          cell_rect_id = self.cell_rect_xref[cell.identifier]
        if cell_rect_id is not None and cell_rect_id in self.rects and cell_rect_id not in seen:
          rect = self.rects[cell_rect_id]
          rect.x = x
          rect.y = y
          seen.add(cell_rect_id)
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

  def overlay_matrix(self, dst_origin_col_index, dst_origin_row_index, dst_matrix):
    for rect in self.get_rects():
      dst_cell_origin = dst_matrix.get_relative_cell_origin_xy(0, 0, dst_origin_col_index, dst_origin_row_index)
      dst_matrix.place_rect(dst_cell_origin.x + rect.x, dst_cell_origin.y + rect.y, rect.copy())

  def get_max_size(self):
    return Size(self.width, self.height)

  def get_allocated_size(self):
    width = 0
    height = 0
    for rect in self.get_rects():
      if width < (rect.x + rect.width):
        width = rect.x + rect.width
      if height < (rect.y + rect.height):
        height = rect.y + rect.height
    return Size(width, height)

  def __str__(self):
    s = 'AreaMatrix(width={0}, height={1}, rows={2}, cols={3})'.format(self.width, self.height, len(self.rows), len(self.columns))
    return s 

  def __repr__(self):
    return self.__str__()
