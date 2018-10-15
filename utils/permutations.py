###########################
# ParamCombinationGenerator
###########################
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

  def partition(self, less):
    self.params[self.cur_tail].partition(less)


class BinarySearch:
  def __init__(self, items):
    self.first = 0
    self.last = len(items) - 1
    self.items = items

  def next(self):
    if self.first > self.last:
      return None
    midpoint = (self.first + self.last)//2
    return self.items[midpoint]

  def partition(self, less):
    midpoint = (self.first + self.last)//2
    if less:
      self.last = midpoint-1
    else:
      self.first = midpoint+1


    
##################
# OptimizableRange
##################
class OptimizableRange:
  def __init__(self, name, start, end, step, binary_search=False):
    self.name = name
    self.start = int(start)
    self.end = int(end)
    self.step = int(step)
    self.current = int(start)
    self.binary_search = None
    if binary_search:
      self.binary_search = BinarySearch([i for i in range(self.start, self.end + 1)])

  def next(self):
    if self.binary_search:
      return self.binary_search.next()

    if self.current > self.end:
      return None
    result = self.current
    self.current = self.current + self.step
    return result

  def partition(self, less):
    if self.binary_search:
      self.binary_search.partition(less)

  def reset(self):
    self.current = self.start
    if self.binary_search:
      self.binary_search = BinarySearch([i for i in range(self.start, self.end + 1)])

  def __str__(self):
    return "{0} (start={1} end={2} step={3} binary_search={4}".format(self.name, self.start, self.end, self.step, str(self.binary_search is not None))

  def __repr__(self):
    return self.__str__()

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