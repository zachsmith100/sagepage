import html
from utils.tree import BasicTree

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

class Frame:
  def __init__(self, element):
    self.element = element
    self.next_child_index = -1

#############
# HTMLElement
#############
class HTMLElement(BasicTree):
  def __init__(self, name):
    BasicTree.__init__(self)
    self.name = name
    self.attributes = {}
    self.text = ''

  def set_attr(self, n, v):
    self.attributes[n] = HTMLAttribute(n,v)
    return self

  def get_attr(self, name, default_value=''):
    if name in self.attributes:
      return self.attributes[name].value
    return default_value

  def set_text(self, t):
    self.text = t
    return self

  def render(self, f):
    f.write(str(self))

  def __str__(self):
    escaped = html.escape(self.text)
    escaped = escaped.replace(' ', '&#160;') # do not eat trailing/leading spaces
    return "<{0} {1}>\n{2}{3}\n</{0}>\n".format(self.name, ' '.join([str(self.attributes[name]) for name in self.attributes]), "\n".join([str(child) for child in self.children]), escaped)

    '''
    stack = []
    cur_frame = Frame(self)
    stack.append(cur_frame)
    result = ''

    while len(stack) > 0:
      if cur_frame.next_child_index < 0:
        cur_frame.next_child_index = 0
        result = result + '<' + cur_frame.element.name
        if len(cur_frame.element.attributes) > 0:
          result = result + ' ' + ' '.join([name + '="' + cur_frame.element.attributes[name].value + '"' for name in cur_frame.element.attributes])
        result = result + ">\n"

      if cur_frame.next_child_index < len(cur_frame.element.children):
        next_frame = Frame(cur_frame.element.children[cur_frame.next_child_index])
        cur_frame.next_child_index = cur_frame.next_child_index + 1
        stack.append(next_frame)
        cur_frame = next_frame        
      else:
          cur_frame = stack.pop()
          if len(self.text) < 1:
            result = result + '</' + cur_frame.element.name + '>'
          else:
            result = result + "\n" + cur_frame.element.text + "\n" + '</' + cur_frame.element.name + '>'
          result = result + "\n"
    return result
    '''


  def __repr__(self):
    return self.__str__()

##################
# HTMLStyleBuilder
##################
class HTMLStyleBuilder:
  def __init__(self):
    self.styles = {}

  def set(self, name, value):
    self.styles[name] =value
    return self

  def get(self, name, default_value=''):
    if name in self.styles:
      return self.styles[name]
    return default_value

  def __str__(self):
    return ';'.join(['{0}:{1}'.format(name, self.styles[name]) for name in self.styles])

  def __repr__(self):
    return self.__str__()