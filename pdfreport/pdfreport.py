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

  def read_csv_file(self, csv_table):
    return pandas.read_csv(StringIO(csv_table), delimiter=",")

  def print_csv_file(self, dataframe, table_name, path="./"):
    dataframe.to_csv(path + table_name, index=False)

  def add_csv_table(self, csv_table, table_name="", breakline=False):
    df = self.read_csv_file(csv_table)
    if table_name:
      self.html += table_name
    if breakline:
      self.html += "\n<br>\n"
    self.html += df.to_html()
    if breakline:
      self.html += "\n<br>\n"

  def add_html(self, html):
    self.html += html

  def print_to_pdf_file(self, filename="output.pdf", path="./"):
    pdfkit.from_string(self.html, path + filename)

if __name__ == "__main__":
  pass