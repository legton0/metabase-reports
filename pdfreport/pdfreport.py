import pdfkit
import pandas
import sys
from io import StringIO

class PDFReport():
  '''
  Handle pdf report methods
  '''
  def __init__(self, html=""):
    self.html = html

  def add_csv_table(self, csv_table, table_name="", breakline=False):
    df = pandas.read_csv(StringIO(csv_table), delimiter=",")
    if table_name:
      self.html += table_name
    if breakline:
      self.html += "\n<br>\n"
    self.html += df.to_html()
    if breakline:
      self.html += "\n<br>\n"

  def add_html(self, html):
    self.html += html

  def print_to_pdf_file(self, filename="output.pdf"):
    pdfkit.from_string(self.html, filename)

if __name__ == "__main__":
  pass