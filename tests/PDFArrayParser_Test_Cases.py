import sys
import os
from context import utils
from utils.pdf import *

class TestCase:
  def __init__(self):
    self.array = None

  def set_array(self, a):
    self.array = a

  def execute(self, expected_array, input_string):
    self.expected_array = expected_array
    parser = PDFArrayParser(self.set_array)
    reader = ParserReader()
    reader.read_string(parser.begin, input_string)

    if self.array is not None and str(self.array) == str(self.expected_array):
      print("PASS: expected '{0}' received '{1}'".format(self.expected_array, self.array))
      return True
    else:
      print("FAIL: expected '{0}' received '{1}'".format(self.expected_array, self.array))
    return False


test_case_params = [
  (PDFValue(PDFValue.ARRAY, [PDFValue(PDFValue.TOKEN, "test"), PDFValue(PDFValue.STRING, "asdf")]), "[test (asdf)] "),
  (PDFValue(PDFValue.ARRAY, [PDFValue(PDFValue.TOKEN, "test"), PDFValue(PDFValue.STRING, "test(parens)")]), "[test (test(parens))] "),
  (PDFValue(PDFValue.ARRAY, [PDFValue(PDFValue.TOKEN, "s")]), "[s] "),
  (PDFValue(PDFValue.ARRAY, [PDFValue(PDFValue.TOKEN, "test"), PDFValue(PDFValue.ARRAY, [PDFValue(PDFValue.TOKEN, "nested")])]), "[test [nested]] "),
  (PDFValue(PDFValue.ARRAY, [PDFValue(PDFValue.HEXSTRING, "asdf"), PDFValue(PDFValue.HEXSTRING, "fdsa")]), "[<asdf><fdsa>] "),
  (PDFValue(PDFValue.ARRAY, [PDFValue(PDFValue.HEXSTRING, "444b5072670d21a1ec33f8bc85d74b3f"), PDFValue(PDFValue.HEXSTRING, "b986190c72322b28310986f8e9343458")]), "[<444b5072670d21a1ec33f8bc85d74b3f><b986190c72322b28310986f8e9343458>] "),
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
