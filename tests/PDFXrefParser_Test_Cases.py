import sys
import os
from context import utils
from utils.pdf import *

class TestCase:
  def __init__(self):
    self.xref = None

  def set_xref(self, a):
    self.xref = a

  def execute(self, expected_xref, input_string):
    self.expected_xref = expected_xref
    parser = PDFXrefParser(self.set_xref)
    reader = ParserReader()
    reader.read_string(parser.begin, input_string)

    if self.xref is not None and str(self.xref) == str(self.expected_xref):
      print("PASS: expected '{0}' received '{1}'".format(self.expected_xref, self.xref))
      return True
    else:
      print("FAIL: expected '{0}' received '{1}'".format(self.expected_xref, self.xref))
    return False


test_case_params = []

xref = PDFXref()
xref.initial_object_id = 0
xref.object_count = 3
xref.entries.append(PDFXrefEntry(0, 65535, 'f'))
xref.entries.append(PDFXrefEntry(508, 0, 'n'))
xref.entries.append(PDFXrefEntry(192, 0, 'n'))
input_string ="""
xref
0 3
0000000000 65535 f 
0000000508 00000 n 
0000000192 00000 n 
"""
test_case_params.append((xref, input_string))

result = True
for params in test_case_params:
  test_case = TestCase()
  if test_case.execute(params[0], params[1]) != True:
    result = False

if result:
  print("PASSED")
else:
  print("FAILED")
