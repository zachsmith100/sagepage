import sys
import os
sys.path.append(os.path.abspath(".."))
from pdf import *

class TestCase:
  def __init__(self):
    self.entry = None

  def set_entry(self, a):
    self.entry = a

  def execute(self, expected_entry, input_string):
    self.expected_entry = expected_entry
    parser = PDFXrefEntryParser(self.set_entry)
    reader = ParserReader()
    reader.read_string(parser.begin, input_string)

    if self.entry is not None and str(self.entry) == str(self.expected_entry):
      print("PASS: expected '{0}' received '{1}'".format(self.expected_entry, self.entry))
      return True
    else:
      print("FAIL: expected '{0}' received '{1}'".format(self.expected_entry, self.entry))
    return False


test_case_params = []

entry = PDFXrefEntry(0, 65535, 'f')
input_string = """0000000000 65535 f """
test_case_params.append((entry, input_string))


"""
xref
0 8
0000000000 65535 f 
0000000508 00000 n 
0000000192 00000 n 
0000000015 00000 n 
0000000171 00000 n 
0000000280 00000 n 
0000000573 00000 n 
0000000700 00000 n 
"""

result = True
for params in test_case_params:
  test_case = TestCase()
  if test_case.execute(params[0], params[1]) != True:
    result = False

if result:
  print("PASSED")
else:
  print("FAILED")
