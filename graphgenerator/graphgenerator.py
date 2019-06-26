import tkinter
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas
import locale
import sys
import os
import json
from datetime import datetime, date, timedelta
import random
import math

class GraphGeneratorParser(object):

  @staticmethod
  def get_optional_value(dictionary, key, default_value=None):
    try:
      return dictionary[key]
    except:
      return default_value
      pass

  @staticmethod
  def get_x(graph_info):
    # if (graph_info["type"] == "bar"):
    #   x = graph_info["columns"]
    # elif (graph_info["type"] == "line_with_filter"):
    #   x = graph_info["columns"]
    # elif (graph_info["type"] == "line"):
    #   x = graph_info["columns"]
    # elif (graph_info["type"] == "pie"):
    #   x = graph_info["labels"]
    x = graph_info["x"]
    return x

  @staticmethod
  def get_x_data(graph_csv, graph_info):
    x = GraphGeneratorParser.get_x(graph_info)
    x_data = graph_csv[x].tolist()
    label_x = GraphGeneratorParser.get_optional_value(graph_info, "label_x", default_value=x)
    return x, x_data, label_x

  @staticmethod
  def get_y(graph_info):
    # if (graph_info["type"] == "bar"):
    #   y = graph_info["rows"]
    # elif (graph_info["type"] == "line_with_filter"):
    #   y = graph_info["rows"]
    # elif (graph_info["type"] == "line"):
    #   return graph_info["y_columns"].split(',')
    # elif (graph_info["type"] == "pie"):
    #   y = graph_info["data"]
    if (graph_info["type"] == "line"):
      return graph_info["y"].split(',')
    y = graph_info["y"]
    return y

  @staticmethod
  def get_y_data(graph_csv, graph_info):
    y = GraphGeneratorParser.get_y(graph_info)
    if isinstance(y, list):
      label_y = GraphGeneratorParser.get_optional_value(graph_info, "label_y", default_value=y)
      if not isinstance(label_y, list):
        label_y = label_y.split(',')
      y_data = {}
      i = 0
      while (i < len(y)):
        y_data[label_y[i]] = graph_csv[y[i]].tolist()
        i+=1
    else:
      label_y = GraphGeneratorParser.get_optional_value(graph_info, "label_y", default_value=y)
      y_data = graph_csv[y].tolist()
    return y, y_data, label_y

  @staticmethod
  def filter_x_data(graph_csv, graph_info, g_filter):
    x, x_data, label_x = GraphGeneratorParser.get_x_data(graph_csv, graph_info)
    new_x_data = list(dict.fromkeys(x_data))
    return x, new_x_data, label_x

  @staticmethod
  def filter_y_data(graph_csv, graph_info, g_filter):
    y, y_data, label_y = GraphGeneratorParser.get_y_data(graph_csv, graph_info)
    f_data = graph_csv[g_filter].tolist()
    label_f = GraphGeneratorParser.get_optional_value(graph_info, "label_filter", default_value=None)
    if (label_f != None):
      label_f = label_f.split(',')
      label_f.reverse()
    f_values = list(dict.fromkeys(f_data))
    new_y_data = {}
    for y, data in y_data.items():
      for f in f_values:
        if (label_f == None):
          key = y + "_" + g_filter + ":" + str(f)
        else:
          key = y + " " + label_f.pop()
        new_y_data[key] = []
        i = 0
        while i < len(f_data):
          if (f_data[i] == f):
            new_y_data[key].append(data[i])
          i += 1
    return y, new_y_data, label_y

  @staticmethod
  def sort_csv(graph_csv, graph_info):
    sort_asc = GraphGeneratorParser.get_optional_value(graph_info, "sort_asc", default_value=None)
    sort_desc = GraphGeneratorParser.get_optional_value(graph_info, "sort_desc", default_value=None)
    if (sort_asc != None):
      graph_csv.sort_values(by=[sort_asc], inplace=True)
    elif (sort_desc != None):
      graph_csv.sort_values(by=[sort_desc], inplace=True, ascending=False)

  @staticmethod
  def fix_date(df, date_columns, date_format=None):
    locale.setlocale(locale.LC_ALL, '')
    columns = list(df)
    aux_cols = list(df)
    time_diff = timedelta(seconds=0)
    date_columns = date_columns.split(',')

    for col in aux_cols:
      if col in date_columns:
        try:
          df[col] = pandas.to_datetime(df[col])
        except ValueError:
          columns.remove(col)
          pass
      else:
        columns.remove(col)

    for col in columns:
      if (date_format == None):
        print("Trying to automatically parse date...")
        try:
          time0 = df[col][0].replace(tzinfo=None)
          time1 = df[col][1].replace(tzinfo=None)
          time_diff = time1 - time0
        except Exception as e:
          print(e.__class__.__name__ + ":")
          print(str(e))
          print("Using default date format")
          pass
      if (date_format != None):
        print("Date format: " + date_format)
        df[col] = df[col].apply(lambda x: x.strftime(date_format))
      elif (time_diff < timedelta(seconds=60)):
        print("Date format: '%d %b %y %H:%M:%S'")
        df[col] = df[col].apply(lambda x: x.strftime('%d %b %y %H:%M:%S'))
      elif (time_diff < timedelta(minutes=60)):
        print("Date format: '%d %b %y %H:%M'")
        df[col] = df[col].apply(lambda x: x.strftime('%d %b %y %H:%M'))
      elif (time_diff < timedelta(hours=24)):
        print("Date format: '%d %b %y %H'")
        df[col] = df[col].apply(lambda x: x.strftime('%d %b %y %H'))
      elif (time_diff < timedelta(days=28)):
        print("Date format: '%d %b %y'")
        df[col] = df[col].apply(lambda x: x.strftime('%d %b %y'))
      elif (time_diff < timedelta(days=365)):
        print("Date format: '%b %y'")
        df[col] = df[col].apply(lambda x: x.strftime('%b %y'))
      else:
        print("Date format: '%Y'")
        df[col] = df[col].apply(lambda x: x.strftime('%Y'))

class GraphsGenerator():
  '''
  Handle graph methods
  '''
  def __init__(self, json_path=None):
    self.json_path = json_path
    if (self.json_path == None):
      self.json_path = sys.path[0] + os.path.sep
    with open(self.json_path + "graphs.json", "r") as read_file:
      self.graphs = json.load(read_file)

  def generate_graphs(self):
    if not(os.path.exists(os.getcwd()+os.path.sep+"graphs")):
      os.mkdir("graphs")
    print("")
    for graph_name, graph_info in self.graphs.items():
      graph_csv = pandas.read_csv(graph_info["csv_path"] + graph_info["csv_name"], delimiter=",")
      print("Generating " + graph_name + " graph")
      g_type = graph_info["type"]
      parsed_date_format = GraphGeneratorParser.get_optional_value(graph_info, "parsed_date_format")
      parse_date_columns = GraphGeneratorParser.get_optional_value(graph_info, "parse_date_columns")
      GraphGeneratorParser.sort_csv(graph_csv, graph_info)
      if (parse_date_columns != None):
        GraphGeneratorParser.fix_date(graph_csv, parse_date_columns, date_format=parsed_date_format)
      color = GraphGeneratorParser.get_optional_value(graph_info, "color", default_value="#A9C920")
      rotation = GraphGeneratorParser.get_optional_value(graph_info, "rotation", default_value=0)
      label_rotation = GraphGeneratorParser.get_optional_value(graph_info, "label_rotation", default_value=0)
      description = GraphGeneratorParser.get_optional_value(graph_info, "description", default_value="")
      g_filter = GraphGeneratorParser.get_optional_value(graph_info, "filter", default_value=None)
      t_headers = GraphGeneratorParser.get_optional_value(graph_info, "headers", default_value=None)
      t_invert = GraphGeneratorParser.get_optional_value(graph_info, "invert_headers_colors", default_value=None)
      if (g_filter != None):
        x, x_data, label_x = GraphGeneratorParser.filter_x_data(graph_csv, graph_info, g_filter)
        y, y_data, label_y = GraphGeneratorParser.filter_y_data(graph_csv, graph_info, g_filter)
      else:
        x, x_data, label_x = GraphGeneratorParser.get_x_data(graph_csv, graph_info)
        y, y_data, label_y = GraphGeneratorParser.get_y_data(graph_csv, graph_info)
      path = "graphs" + os.path.sep + graph_name
      GraphGenerator.generate_graph(g_type, x_data, y_data, label_x, label_y, path, title=graph_name, subtitle=description, rotation=rotation, label_rotation=label_rotation, color=color, t_headers=t_headers, t_invert=t_invert)

class GraphGenerator(object):

  @staticmethod
  def generate_graph(type, x_data, y_data, x_label, y_label, path, title="", subtitle="", rotation=0, label_rotation=0, color=None, t_headers=None, t_invert=None):

    fig, ax = plt.subplots()

    if (type == 'bar'):
      bars = plt.bar(x_data, y_data, align="center", color=color)
      plt.xticks(rotation=rotation)
      plt.gcf().subplots_adjust(left=0.3, right=0.7)
      plt.gcf().set_size_inches(30, plt.gcf().get_size_inches()[1])

      plt.xlabel(x_label)
      plt.ylabel(y_label)

      GraphGenerator.display_label_bar(ax, bars, rotation=label_rotation)
    elif (type == 'horizontal_bar'):
      bars = plt.barh(y_data, x_data, align="center", color=color)
      plt.xticks(rotation=rotation)
      plt.gcf().subplots_adjust(left=0.3, right=0.7)
      plt.gcf().set_size_inches(15, plt.gcf().get_size_inches()[1])

      plt.xlabel(x_label)
      plt.ylabel(y_label)

      GraphGenerator.display_label_barh(ax, bars, rotation=label_rotation)
    elif (type == 'pie'):
      plt.pie(y_data, labels=x_data, autopct='%1.1f%%', shadow=True, startangle=90)
      plt.axis('equal')
    elif (type == 'line'):
      random.seed(9000)
      for y, data in y_data.items():
        f1 = random.random()
        f2 = random.random()
        f3 = random.random()
        plt.plot(x_data, data, color=(f1,f2,f3), linewidth=2, label=y, marker='o')
      plt.legend()
      plt.xticks(rotation=rotation)
    elif (type == 'horizontal_table'):
      ax.axis('off')
      fig.set_figheight(2, forward=False)
      figwidth = 3 + (3 * math.ceil(len(x_data) / 5))
      fig.set_figwidth(figwidth, forward=False)
      colors = []
      if (t_headers != None):
        cell_text = [[x_label] + x_data, [y_label] + y_data]
        if (t_invert != None):
          colors = [["k"] + ["w" for x in x_data], ["k"] + ["w" for y in y_data]]
          the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center', cellColours=colors)
          the_table._cells[(0, 0)]._text.set_color('w')
          the_table._cells[(1, 0)]._text.set_color('w')
        else:
          the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center')
      else:
        cell_text = [x_data, y_data]
        the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center')
      the_table.scale(2, 2)
    elif (type == 'vertical_table'):
      ax.axis('off')
      figheight = 1.5 + (1.5 * math.ceil(len(x_data) / 5))
      fig.set_figheight(figheight, forward=False)
      colors = []
      cell_text = []
      i = 0
      while i < len(x_data):
        colors.append(["w", "w"])
        cell_text.append([])
        cell_text[i].append(x_data[i])
        cell_text[i].append(y_data[i])
        i += 1
      if (t_headers != None):
        cell_text = [[x_label, y_label]] + cell_text
        if (t_invert != None):
          colors = [["k", "k"]] + colors
          the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center', cellColours=colors)
          the_table._cells[(0, 0)]._text.set_color('w')
          the_table._cells[(0, 1)]._text.set_color('w')
        else:
          the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center')
      else:
        the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center')
      the_table.scale(2, 2)

    if (title != "" or subtitle != ""):
      plt.suptitle(title, y=1.1, fontsize=15)
      plt.title(subtitle, y=1.1, fontsize=13)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    print("Storing in " + path + ".png\n")
    plt.savefig(path, bbox_inches = 'tight', pad_inches = 0.2)

    plt.clf()

  @staticmethod
  def display_label_bar(ax, bars, rotation=0):
    max_y_value = ax.get_ylim()[1]
    distance = max_y_value * 0.01
    for bar in bars:
      text = bar.get_height()
      text_x = bar.get_x() + bar.get_width() / 2
      text_y = bar.get_height() + distance
      ax.text(text_x, text_y, text, ha='center', va='bottom', rotation=rotation)

  @staticmethod
  def display_label_barh(ax, bars, rotation=0):
    max_x_value = ax.get_xlim()[1]
    distance = max_x_value * 0.0025
    for bar in bars:
      text = bar.get_width()
      text_y = bar.get_y() + bar.get_height() / 2
      text_x = bar.get_width() + distance
      ax.text(text_x, text_y, text, va='center', rotation=rotation)

if __name__ == "__main__":
  generator = GraphsGenerator("/home/legton/pmec/metabase-reports/")
  generator.generate_graphs()
