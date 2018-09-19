import sys
import os
sys.path.append(os.path.abspath(".."))
from pdf import *

class TestCase:
  def __init__(self):
    self.dictionary = {}

  def set_dictionary(self, d):
    self.dictionary = d

  def execute(self, expected_dictionary, input_string):
    self.expected_dictionary = expected_dictionary
    parser = PDFDictionaryParser(self.set_dictionary)
    reader = ParserReader()
    reader.read_string(parser.begin, input_string)

    if self.dictionary is not None and str(self.dictionary) == str(self.expected_dictionary):
      print("PASS: expected '{0}' received '{1}'".format(self.expected_dictionary, self.dictionary))
      return True
    else:
      print("FAIL: expected '{0}' received '{1}'".format(self.expected_dictionary, self.dictionary))
    return False


test_case_params = [
  (PDFValue(PDFValue.DICTIONARY, {"test":PDFValue(PDFValue.TOKEN, "value"), "test1":PDFValue(PDFValue.NAME, "value2")}), "<</test value /test1 /value2>> ")
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
