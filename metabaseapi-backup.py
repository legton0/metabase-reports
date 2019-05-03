import requests
from datetime import datetime, date, timedelta
import json
import os
import pdfkit
import pandas
import sys
import argparse
from io import StringIO

def json_request(method, url, headers, payload=""):
  if method == "GET":
    response = requests.get(url, headers=headers)
  elif method == "POST":
    response = requests.post(url, json=payload, headers=headers)
  if (response.status_code != 200):
    print(response.status_code)
    print(response.text)
    exit(1)

  return response

def login():
  print("Signing in...")
  try:
    with open("login_info.json", "r") as read_file:
      payload = json.load(read_file)
    username = payload['username']
    password = payload['password']
  except (ValueError, KeyError, FileNotFoundError) as e:
    print("Error: Invalid or missing login_info.json")
    print("")
    raise e

  headers = {'Content-Type': 'application/json'}
  response = json_request("POST", "http://metabase.c3sl.ufpr.br/api/session", headers, payload=payload)

  return response.json()

def get_credentials_id():
  expired = False
  empty_credentials = False
  invalid_json = False
  exists = os.path.isfile('credentials.json')
  if exists:
    try:
      with open("credentials.json", "r") as read_file:
        credentials = json.load(read_file)
      expire_date = datetime.strptime(credentials['expire_date'], '%Y-%m-%d').date()
      expired = date.today() >= expire_date
      credentials_id = credentials['id']
      print("Current credentials expire in %s" % expire_date)
    except (ValueError, KeyError):
      invalid_json = True
  else:
    empty_credentials = True

  if expired or empty_credentials or invalid_json:
    print("Expired or invalid credentials.")
    return ""

  return credentials_id

def set_credentials_id():
  credentials_id = get_credentials_id()
  if not credentials_id:
    print("Generating new credentials...")
    expire_date = date.today() + timedelta(days=13)
    credentials = login()
    credentials['expire_date'] = expire_date.strftime('%Y-%m-%d')
    with open("credentials.json", "w") as write_file:
      json.dump(credentials, write_file)
    credentials_id = credentials['id']
    print("New credentials expire in  %s" % expire_date)
  
  print("Current credentials id: %s" % credentials_id)

  return credentials_id

def get_collections(credentials_id, print_info=True):
  print("aaaaaaaa")
  headers = {'Content-Type': 'application/json', 'X-Metabase-Session': credentials_id}
  url = "http://metabase.c3sl.ufpr.br/api/collection"
  collections = json_request("GET", url, headers).json()
  if (print_info):
    print("Your accessible collections:")
    for collection in collections:
      print("Name: %s, id: %s" % (collection["name"], collection["id"]))
  return collections

def get_cards(collection_id, credentials_id, print_info=False):
  headers = {'Content-Type': 'application/json', 'X-Metabase-Session': credentials_id}
  url = "http://metabase.c3sl.ufpr.br/api/collection/" + str(collection_id) +"/items"
  collection = json_request("GET", url, headers).json()
  if (print_info):
    print("Cards in this collection:")
    for card in collection:
      print("Name: %s, id: %s" % (card["name"], card["id"]))
  return collection

class ServiceAction(argparse.Action):
    ''' Action class to set function that must be called when a parameter
    is setted at the command line
    '''
    def __init__(self, function_name, nargs=0, **kw):
        self._function_name = function_name
        super().__init__(nargs=nargs, **kw)

    def __call__(self, parser, namespace, values, option_string=None):
        func_attr = "{}_function".format(self.dest)
        setattr(namespace, func_attr, self._function_name)
        setattr(namespace, self.dest, values)

if __name__ == "__main__":
  #imprimir colecoes e cards;
  #ler ids de um arquivo;
  #generalizar mais ainda o codigo;
  #ter requirements.txt;
  #testar env do python;
  #ter help e readme;
  #criar projeto no gitlab;
  #criar css
  #melhorar o nome
  credentials_id = set_credentials_id()

  get_collections(credentials_id, print_info=True)
  collection = get_cards(3, credentials_id)#, print_info=True)

  headers = {'Content-Type': 'application/json', 'X-Metabase-Session': credentials_id}
  #url = "http://metabase.c3sl.ufpr.br/api/collection/3/items"
  #collection = json_request("GET", url, headers).json()
  relatorio_html = '<!DOCTYPE html>\n<html lang="pt">\n<head>\n<meta charset="utf-8">\n</head>\n<body>\n'
  relatorio_html += "Relatorio\n<br>\n"
  print(collection)
  for item in collection:
    url = "http://metabase.c3sl.ufpr.br/api/card/" + str(item['id']) +"/query/csv"
    csv_table = json_request("POST", url, headers).text
    df = pandas.read_csv(StringIO(csv_table), delimiter=",")
    relatorio_html += (item['name'] + "\n<br>\n")
    relatorio_html += df.to_html()
    relatorio_html += "\n<br>\n"
    #NAO ESQUECER DE RETIRAR:
    #break
  relatorio_html += "</body>\n</html>"
  pdfkit.from_string(relatorio_html, 'metabase.pdf')