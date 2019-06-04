import requests
from datetime import datetime, date, timedelta
import json
import os
import sys

class MetabaseAPI():
  '''
  Handle metabase api methods
  '''
  def __init__(self, api_url, json_path=None):
    self.headers = {'Content-Type': 'application/json'}
    if (not api_url.endswith('/')):
      api_url += "/"
    self.api_url = api_url
    print("API: " + self.api_url)
    self.json_path = json_path
    if (self.json_path == None):
      self.json_path = sys.path[0] + os.path.sep
    self.authenticate()

  def authenticate(self):
    self.credentials_id = self.set_credentials_id()
    self.headers = {'Content-Type': 'application/json', 'X-Metabase-Session': self.credentials_id}

  def json_request(self, method, url, headers="", payload=""):
    if headers == "":
      headers = self.headers
    if method == "GET":
      response = requests.get(url, headers=headers)
    elif method == "POST":
      response = requests.post(url, json=payload, headers=headers)
    if (response.status_code != 200):
      print(response.status_code)
      print(response.text)
      if (response.status_code == 404):
        print("This error was caused because you tried to access an url that doesn't exist.")
      exit(1)

    return response

  def login(self):
    print("Signing in...")
    try:
      with open(self.json_path + "login_info.json", "r") as read_file:
        payload = json.load(read_file)
      username = payload['username']
      password = payload['password']
    except (ValueError, KeyError, FileNotFoundError) as e:
      print("Error: Invalid or missing login_info.json")
      print("")
      raise e

    response = self.json_request("POST", self.api_url + "session", payload=payload)

    return response.json()

  def get_credentials_id(self):
    expired = False
    empty_credentials = False
    invalid_json = False
    exists = os.path.isfile('credentials.json')
    if exists:
      try:
        with open(self.json_path + "credentials.json", "r") as read_file:
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

  def set_credentials_id(self):
    credentials_id = self.get_credentials_id()
    if not credentials_id:
      print("Generating new credentials...")
      expire_date = date.today() + timedelta(days=13)
      credentials = self.login()
      credentials['expire_date'] = expire_date.strftime('%Y-%m-%d')
      with open(self.json_path + "credentials.json", "w") as write_file:
        json.dump(credentials, write_file, indent=4)
      credentials_id = credentials['id']
      print("New credentials expire in  %s" % expire_date)
    
    print("Current credentials id: %s" % credentials_id)

    return credentials_id

  def get_collections(self, print_info=True):
    url = self.api_url + "collection"
    collections = self.json_request("GET", url).json()
    if (print_info):
      print("Your accessible collections:")
      for collection in collections:
        print("Name: %s, id: %s" % (collection["name"], collection["id"]))
    return collections

  def get_cards(self, collection_id, print_info=True):
    url = self.api_url + "collection/" + str(collection_id)
    collection = self.json_request("GET", url).json()
    collection_name = collection["name"]
    url = self.api_url + "collection/" + str(collection_id) +"/items"
    collection = self.json_request("GET", url).json()
    if (print_info):
      print("Cards in the %s collection:" % collection_name)
      for card in collection:
        print("Name: %s, id: %s" % (card["name"], card["id"]))
    return collection

  def get_card(self, card_id, print_info=True):
    url = self.api_url + "card/" + str(card_id) +"/query/csv"
    card = self.json_request("POST", url).text
    return card

if __name__ == "__main__":
  pass