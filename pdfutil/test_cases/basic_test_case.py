import sys
import os
sys.path.append(os.path.abspath(".."))
from pdf import *

class TestCase:
  def set_pdf(self, pdf):
    print(pdf)

  def execute(self, filename):
    parser = PDFParser(self.set_pdf)
    reader = ParserReader()
    result = reader.read_file(parser.begin, filename)

    if result is True:
      print("PASS")
    else:
      print("FAIL")

test_case = TestCase()
test_case.execute("./pdf/simple.pdf")
