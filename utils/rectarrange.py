import math
from utils.models import Rect
from utils.models import Size
from utils.svg import SVG

##########
# FreeCell
##########
class FreeCell:
  def __init__(self, identifier, color=None):
    self.identifier = identifier
    self.color = color

  def set_color(self, color):
    self.color = color

  def is_free(self):
    if self.color is None:
      return True
    return False

  def __str__(self):
    return 'FreeCell({0}, {1}, is_free()=>{0})'.format(self.identifier, self.color, self.is_free())

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

  def get_next_id(self):
    next_id = self.next_id
    self.next_id = self.next_id + 1
    return next_id

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

  def select_topmost_fit(self, test_rect, trial_rects):
    selected_rect = None
    for rect in trial_rects:
      if rect.width < test_rect.width or rect.height < test_rect.height:
        continue
      if selected_rect is None:
        selected_rect = rect
      elif rect.y < selected_rect.y:
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
        self.rows[row_index][col_index].color = rect.get_color()

    # Update X,Y
    ############
    x = 0
    y = 0
    for col_index in range(origin_col_index):
      x = x + self.column_widths[col_index]
    for row_index in range(origin_row_index):
      y = y + self.row_heights[row_index]
    rect.x = x
    rect.y = y

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
    self.matrix = AreaMatrix(0,0)

  def get_placement_coord(self, rect):
    x = 0
    y = 0
    
  def get_enclosing_rect_for_area(self, area):
    unit_square = area/self.ratio
    h = math.sqrt(unit_square)
    w = h * self.ratio

    if ((w*100) % 10) > 0:
      w = int(w) + 1
    else:
      w = int(w)

    if ((h*100) % 10) > 0:
      h = int(h) + 1
    else:
      h = int(h)

    return Size(w,h)


  def attempt_arrangement(self, matrix, rects):
    for rect in rects:
      free_rects = matrix.list_free_rects()

      selected_rect = matrix.select_topmost_fit(rect, free_rects)

      if selected_rect is None:
        return False

      matrix.place_rect(selected_rect.x, selected_rect.y, rect)

    return True

  def default_sort_key(r):
    return r.width * r.height

  def arrange(self, rects, ratio, rect_sort_key_f, matrix_svg_filename=None):
    self.ratio = ratio

    rects.sort(key=rect_sort_key_f, reverse=True)

    width = 0
    height = 0
    for rect in rects:
      if (rect.x + rect.width) > width:
        width = rect.x + rect.width
      if (rect.y + rect.height) > height:
        height = rect.y + rect.height
    area = width * height

    while True:
      enclosing_rect = self.get_enclosing_rect_for_area(area)
      print("Attempting enclosing rect", enclosing_rect.width, enclosing_rect.height)
      matrix = AreaMatrix(enclosing_rect.width, enclosing_rect.height)
      if self.attempt_arrangement(matrix, rects):
        print("Found arrangement", enclosing_rect)
        if matrix_svg_filename is not None:
          matrix.dump_svg(matrix_svg_filename)
        break
      area = area + int(area * 0.1)
