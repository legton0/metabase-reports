import argparse
import json
import ast
import sys
import os
from metabaseapi.metabaseapi import MetabaseAPI
from pdfreport.pdfreport import PDFReport
from graphgenerator.graphgenerator import GraphGenerator

class Metabase(MetabaseAPI):

  def __init__(self):
    self.path = sys.path[0] + os.path.sep
    self.json_path = None
    self.chosen_method = getattr(self, "no_method")
    self.method_arguments = []
    self.api_url = None
    self.init_config()
    MetabaseAPI.__init__(self, self.api_url, json_path=self.json_path)
    self.graph_generator = GraphGenerator(json_path=self.json_path)
    if hasattr(self.cli_arguments, 'method'):
      self.chosen_method = getattr(self, self.cli_arguments.method)
      self.method_arguments = self.cli_arguments.args
      if ((self.cli_arguments.nargs != 0) and not (self.method_arguments)):
        self.read_args_file()

  def init_config(self):
    self.parser = Parser()
    self.cli_arguments = self.parser.parse_args()
    self.config_json = None
    self.args_json = None

    self.json_path = self.cli_arguments.json_path
    if (self.json_path == None):
      self.json_path = self.path

    try:
      with open(self.json_path + "config.json", "r") as read_file:
        self.config_json = json.load(read_file)
    except FileNotFoundError as e:
      print("Warning:")
      print("  No config.json file found")
      print("  Expecting api_url as an argument...")
      print('')

    self.api_url = self.cli_arguments.api_url
    if (self.api_url == None):
      try:
        self.api_url = self.config_json['api_url']
      except (ValueError, KeyError) as e:
        print("No api_url value found")
        print('')
        raise e
    try:
      with open(self.json_path + "arguments.json", "r") as read_file:
        self.args_json = json.load(read_file)
    except FileNotFoundError as e:
      print("Warning:")
      print("  No arguments.json file found")
      print("  Expecting method arguments in the cli...")
      print('')

  def read_args_file(self):
    print("No arguments found in cli")
    print("Reading arguments from the arguments.json file...")
    self.method_arguments = self.args_json[self.cli_arguments.method]

  def print_collections(self, ids):
    print("")
    self.get_collections()
    print("")

  def print_cards(self, collection_ids):
    print("")
    for collection_id in collection_ids:
      self.get_cards(collection_id)
      print("")

  def create_pdf_report(self, ids):
    print("")
    self.report = PDFReport()
    self.report.add_html('<!DOCTYPE html>\n<html lang="pt">\n<head>\n<meta charset="utf-8">\n')
    self.report.add_html("</head>\n<body>\nRelatorio\n<br>\n")

    card_ids = []
    for item in ids:
      if (isinstance(item, dict)):
        collection_id = item['collection']
        try:
          card_ids = item['cards']
        except:
          card_ids = []
      else:
        collection_id = item
        card_ids = []
      self.print_pdf_report(collection_id, card_ids)

    self.report.add_html("</body>\n</html>")
    if not(os.path.exists(os.getcwd()+os.path.sep+"pdfs")):
      os.mkdir("pdfs")
    self.report.print_to_pdf_file(filename="metabase.pdf", path="pdfs"+os.path.sep)
    print("")

  def print_pdf_report(self, collection_id, card_ids=[]):
    collection = self.get_cards(collection_id, print_info=False)

    for item in collection:
      if (not (card_ids) or (item['id'] in card_ids)):
        card = metabase.get_card(item['id'])
        self.report.add_csv_table(card, table_name=item['name'], breakline=True)

  def create_csv_files(self, ids):
    print("")
    self.report = PDFReport()

    card_ids = []
    for item in ids:
      if (isinstance(item, dict)):
        collection_id = item['collection']
        try:
          card_ids = item['cards']
        except:
          card_ids = []
      else:
        collection_id = item
        card_ids = []
      self.print_csv_files(collection_id, card_ids)

  def print_csv_files(self, collection_id, card_ids=[]):
    collection = self.get_cards(collection_id, print_info=False)
    if not(os.path.exists(os.getcwd()+os.path.sep+"csvs")):
      os.mkdir("csvs")
    for item in collection:
      if (not (card_ids) or (item['id'] in card_ids)):
        metabase_card = metabase.get_card(item['id'])
        card = self.report.read_csv_file(metabase_card)
        self.report.print_csv_file(card, table_name=item['name'] + ".csv", path="csvs"+os.path.sep)

  def generate_graphs(self, args):
    self.graph_generator.generate_graphs()

  def no_method(self, args):
    print("No option was specified.")
    self.parser.print_help()

class ClassAction(argparse.Action):

  def __init__(self, option_strings, dest, nargs, **kwargs):
    super(ClassAction, self).__init__(option_strings, dest, nargs, **kwargs)
    self.method = option_strings[0].replace("--", "")

  def __call__(self, parser, namespace, values, option_string=None):
    l = []
    for item in values:
      l.append(ast.literal_eval(item))
    values = l
    setattr(namespace, "method", self.method)
    setattr(namespace, self.dest, values)
    setattr(namespace, "nargs", self.nargs)


class Parser(argparse.ArgumentParser):

  def __init__(self):
    argparse.ArgumentParser.__init__(self, description='Metabase Interface program')
    self.parser_group = self.add_mutually_exclusive_group()
    self.parser_group.add_argument(
                            '--print_collections', dest="args",
                            action=ClassAction, nargs=0,
                            help='list available metabase collections')
    self.parser_group.add_argument(
                            '--print_cards', dest="args", 
                            action=ClassAction, nargs="*",
                            help='list metabase cards in specified collection(s)')
    self.parser_group.add_argument(
                            '--create_pdf_report', dest="args", 
                            action=ClassAction, nargs="*",
                            help='print specified collection(s) or cards to a pdf file')
    self.parser_group.add_argument(
                            '--create_csv_files', dest="args", 
                            action=ClassAction, nargs="*",
                            help='print specified collection(s) or cards to csv files')
    self.parser_group.add_argument(
                            '--generate_graphs', dest="args", 
                            action=ClassAction, nargs=0,
                            help='generate specified graph(s)')
    self.add_argument('-A', '--api_url', action='store', dest='api_url',
                          help='define api url')
    self.add_argument('-J', '--json_path', action='store', dest='json_path',
                          help='define the path of the json configuration files')

if __name__ == "__main__":
  metabase = Metabase()

  metabase.chosen_method(metabase.method_arguments)