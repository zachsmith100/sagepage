######
# Rect
######
class Rect:
  def __init__(self, identifier, x=0, y=0, width=0, height=0, color='gray'):
    self.identifier = identifier
    self.x = x
    self.y = y
    self.width = width
    self.height = height
    self.color = color

  def get_color(self):
    if self.color is None:
      return 'none'
    return self.color

  def set_color(self, color):
    self.color = color

  def __str__(self):
    return 'Rect({0}, {1}, {2}, {3})'.format(self.x, self.y, self.width, self.height)

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