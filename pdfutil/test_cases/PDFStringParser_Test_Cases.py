import sys
import os
sys.path.append(os.path.abspath(".."))
from pdf import *

class TestCase:
  def __init__(self):
    self.string = None

  def set_string(self, s):
    self.string = s

  def execute(self, expected_string, input_string):
    self.expected_string = expected_string
    parser = PDFStringParser(self.set_string)
    reader = ParserReader()
    reader.read_string(parser.begin, input_string)

    if self.string is not None and self.string.type == PDFValue.STRING and self.string.value == self.expected_string.value:
      print("PASS: expected '{0}' received '{1}'".format(self.expected_string, self.string))
      return True
    else:
      print("FAIL: expected '{0}' received '{1}'".format(self.expected_string, self.string))
    return False


test_case_params = [
  (PDFValue(PDFValue.STRING, "asdf"), "(asdf)"),
  (PDFValue(PDFValue.STRING, "test(parens)"), "(test(parens))")
]

result = True
for params in test_case_params:
  test_case = TestCase()
  if test_case.execute(params[0], params[1]) != True:
    result = False

if result:
  print("PASSED")
else:
  print("FAILED")
