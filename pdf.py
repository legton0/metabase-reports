import requests
from datetime import datetime, date, timedelta
import json
import csv
import os

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
  except (ValueError, KeyError) as e:
    print("Error: Invalid login_info.json")
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

if __name__ == "__main__":
  credentials_id = set_credentials_id()
  headers = {'Content-Type': 'application/json', 'X-Metabase-Session': credentials_id}
  url = "http://metabase.c3sl.ufpr.br/api/collection/3/items"
  collection = json_request("GET", url, headers).json()
  exists = os.path.isfile('metabase.csv')
  if exists:
    f = open("metabase.csv", "w+")
  f = open("metabase.csv", "a+")
  for item in collection:
    url = "http://metabase.c3sl.ufpr.br/api/card/" + str(item['id']) +"/query/csv"
    f.write(item['name'] + ",\n")
    metabase_csv = json_request("POST", url, headers).text
    f.write(metabase_csv)
    f.write(",\n")
    break
  f.close()
  with open('metabase.csv', "r") as csvfile:
    data = list(csv.reader(csvfile))