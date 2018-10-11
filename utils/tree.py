class BasicTree:
  def __init__(self):
    self.children = []

  def add_child(self, child):
    self.children.append(child)
    return child

  def iterate_children(self, callback_f, **kwargs):
    results = []
    for child in self.children:
      results.append(callback_f(child, **kwargs))
      next_results = child.iterate_children(callback_f, **kwargs)
      results.extend(next_results)
    return results