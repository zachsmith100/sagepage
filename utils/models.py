######
# Rect
######
class Rect:
  def __init__(self, identifier, x=0, y=0, width=0, height=0, color='gray', sort_group=None):
    self.identifier = identifier
    self.x = x
    self.y = y
    self.width = width
    self.height = height
    self.color = color
    self.sort_group = sort_group

  def get_color(self):
    if self.color is None:
      return 'none'
    return self.color

  def set_color(self, color):
    self.color = color

  def __str__(self):
    return 'Rect(id={0}, x={1}, y={2}, w={3}, h={4}), sort_group={5}'.format(self.identifier, self.x, self.y, self.width, self.height, self.sort_group)

  def __repr__(self):
    return self.__str__()

######
# Size
######
class Size:
  def __init__(self, width, height):
    self.width = width
    self.height = height

  def __str__(self):
    return 'Size({0}, {1})'.format(self.width, self.height)

  def __repr__(self):
    return self.__str__()