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

  def set_attr(self, n, v):
    self.attributes[n] = HTMLAttribute(n,v)
    return self

  def get_attr(self, name, default_value=''):
    if name in self.attributes:
      return self.attributes[name].value
    return default_value

  def add_child(self, e):
    self.children.append(e)
    return e

  def set_text(self, t):
    self.text = t
    return self

  def iterate_children(self, callback_f, **kwargs):
    results = []
    for child in self.children:
      results.append(callback_f(child, **kwargs))
      next_results = child.iterate_children(callback_f, **kwargs)
      results.extend(next_results)
    return results

  def render(self, f):
    f.write(str(self))

  def __str__(self):
    return "<{0} {1}>\n{2}{3}\n</{0}>\n".format(self.name, ' '.join([str(self.attributes[name]) for name in self.attributes]), "\n".join([str(child) for child in self.children]), self.text)

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

  def __str__(self):
    return ';'.join(['{0}:{1}'.format(name, self.styles[name]) for name in self.styles])

  def __repr__(self):
    return self.__str__()