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

class Graph():
  def __init__(self, name, information):
    self.name = name
    self.information = information
    self.type = self.information["type"]
    self.save_path = "graphs" + os.path.sep + self.name
    self.read_csv()
    self.read_optional_info()
    if (self.sort_asc_by != None):
      self.csv.sort_values(by=[self.sort_asc_by], inplace=True)
    if (self.sort_desc_by != None):
      self.csv.sort_values(by=[self.sort_desc_by], inplace=True, ascending=False)
    if (self.date_columns_to_be_parsed != None):
      self.fix_date()

  def read_csv(self):
    self.csv_path = self.information["csv_path"]
    self.csv_name = self.information["csv_name"]
    self.csv = pandas.read_csv(self.csv_path + self.csv_name, delimiter=",")

  def read_optional_info(self):
    self.description = self.get_optional_value(self.information, "description", default_value="")
    self.colors = self.get_optional_value(self.information, "colors", default_value="#A9C920")
    self.date_columns_to_be_parsed = self.get_optional_value(self.information, "parse_date_columns")
    self.parsed_date_format = self.get_optional_value(self.information, "parsed_date_format")
    self.sort_asc_by = self.get_optional_value(self.information, "sort_asc")
    self.sort_desc_by = self.get_optional_value(self.information, "sort_desc")

  def get_optional_value(self, dictionary, key, default_value=None):
    try:
      return dictionary[key]
    except:
      return default_value
      pass

  def fix_date(self):
    df = self.csv
    date_columns = self.date_columns_to_be_parsed
    date_format = self.parsed_date_format
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

class GraphSubclass(Graph):
  def __init__(self, name, information):
    Graph.__init__(self, name, information)
    self.rotation = self.get_optional_value(self.information, "rotation", default_value=0)
    self.filter = self.get_optional_value(self.information, "filter", default_value=None)
    self.x, self.x_data, self.x_label = GraphGeneratorParser.get_x_data(self, self.csv, self.information)
    if (self.filter != None):
      self.x_data = list(dict.fromkeys(self.x_data))
      self.y, self.y_data, self.y_label = GraphGeneratorParser.filter_y_data(self, self.csv, self.information, self.filter)
    else:
      self.y, self.y_data, self.y_label = GraphGeneratorParser.get_y_data(self, self.csv, self.information)
    #Remover depois:
    self.label_rotation = self.get_optional_value(self.information, "label_rotation", default_value=0)
    self.t_headers = self.get_optional_value(self.information, "headers", default_value=None)
    self.t_invert = self.get_optional_value(self.information, "invert_headers_colors", default_value=None)
    self.p_no_values = self.get_optional_value(self.information, "no_values", default_value=None)

class GraphGeneratorParser(object):

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
  def get_x_data(graph, graph_csv, graph_info):
    x = GraphGeneratorParser.get_x(graph_info)
    x_data = graph_csv[x].tolist()
    label_x = graph.get_optional_value(graph_info, "label_x", default_value=x)
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
  def get_y_data(graph, graph_csv, graph_info):
    y = GraphGeneratorParser.get_y(graph_info)
    if isinstance(y, list):
      label_y = graph.get_optional_value(graph_info, "label_y", default_value=y)
      if not isinstance(label_y, list):
        label_y = label_y.split(',')
      y_data = {}
      i = 0
      while (i < len(y)):
        y_data[label_y[i]] = graph_csv[y[i]].tolist()
        i+=1
    else:
      label_y = graph.get_optional_value(graph_info, "label_y", default_value=y)
      y_data = graph_csv[y].tolist()
    return y, y_data, label_y

  @staticmethod
  def filter_y_data(graph, graph_csv, graph_info, g_filter):
    y, y_data, label_y = GraphGeneratorParser.get_y_data(graph, graph_csv, graph_info)
    f_data = graph_csv[g_filter].tolist()
    label_f = graph.get_optional_value(graph_info, "label_filter", default_value=None)
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
      graph_test = GraphSubclass(graph_name, graph_info)
      print("Generating " + graph_name + " graph")
      GraphGenerator.generate_graph(graph_test)

class GraphGenerator(object):

  @staticmethod
  def generate_graph(graph):

    fig, ax = plt.subplots()

    if (graph.type == 'bar'):
      bars = plt.bar(graph.x_data, graph.y_data, align="center", color=graph.colors)
      plt.xticks(rotation=graph.rotation)
      plt.gcf().subplots_adjust(left=0.3, right=0.7)
      plt.gcf().set_size_inches(30, plt.gcf().get_size_inches()[1])

      plt.xlabel(graph.x_label)
      plt.ylabel(graph.y_label)

      GraphGenerator.display_label_bar(ax, bars, rotation=graph.label_rotation)
    elif (graph.type == 'horizontal_bar'):
      bars = plt.barh(graph.y_data, graph.x_data, align="center", color=graph.colors)
      plt.xticks(rotation=graph.rotation)
      plt.gcf().subplots_adjust(left=0.3, right=0.7)
      plt.gcf().set_size_inches(15, plt.gcf().get_size_inches()[1])

      plt.xlabel(graph.x_label)
      plt.ylabel(graph.y_label)

      GraphGenerator.display_label_barh(ax, bars, rotation=graph.label_rotation)
    elif (graph.type == 'pie'):
      if (graph.p_no_values != None):
        plt.pie(graph.y_data, labels=graph.x_data, autopct='%1.1f%%', startangle=graph.rotation)
      else:
        plt.pie(graph.y_data, labels=graph.x_data, autopct=lambda pct: GraphGenerator.display_values_pie(pct, graph.y_data), startangle=graph.rotation)
      plt.axis('equal')
    elif (graph.type == 'line'):
      random.seed(9000)
      for y, data in graph.y_data.items():
        f1 = random.random()
        f2 = random.random()
        f3 = random.random()
        plt.plot(graph.x_data, data, color=(f1,f2,f3), linewidth=2, label=y, marker='o')
      plt.legend()
      plt.xticks(rotation=graph.rotation)
    elif (graph.type == 'horizontal_table'):
      ax.axis('off')
      fig.set_figheight(2, forward=False)
      figwidth = 3 + (3 * math.ceil(len(graph.x_data) / 5))
      fig.set_figwidth(figwidth, forward=False)
      colors = []
      if (graph.t_headers != None):
        cell_text = [[graph.x_label] + graph.x_data, [graph.y_label] + graph.y_data]
        if (graph.t_invert != None):
          colors = [["k"] + ["w" for x in graph.x_data], ["k"] + ["w" for y in graph.y_data]]
          the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center', cellColours=colors)
          the_table._cells[(0, 0)]._text.set_color('w')
          the_table._cells[(1, 0)]._text.set_color('w')
        else:
          the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center')
      else:
        cell_text = [graph.x_data, graph.y_data]
        the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center')
      the_table.scale(2, 2)
    elif (graph.type == 'vertical_table'):
      ax.axis('off')
      figheight = 1.5 + (1.5 * math.ceil(len(graph.x_data) / 5))
      fig.set_figheight(figheight, forward=False)
      colors = []
      cell_text = []
      i = 0
      while i < len(graph.x_data):
        colors.append(["w", "w"])
        cell_text.append([])
        cell_text[i].append(graph.x_data[i])
        cell_text[i].append(graph.y_data[i])
        i += 1
      if (graph.t_headers != None):
        cell_text = [[graph.x_label, graph.y_label]] + cell_text
        if (graph.t_invert != None):
          colors = [["k", "k"]] + colors
          the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center', cellColours=colors)
          the_table._cells[(0, 0)]._text.set_color('w')
          the_table._cells[(0, 1)]._text.set_color('w')
        else:
          the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center')
      else:
        the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center')
      the_table.scale(2, 2)

    if (graph.name != "" or graph.description != ""):
      plt.suptitle(graph.name, y=1.1, fontsize=15)
      plt.title(graph.description, y=1.1, fontsize=13)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    print("Storing in " + graph.save_path + ".png\n")
    plt.savefig(graph.save_path, bbox_inches = 'tight', pad_inches = 0.2)

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

  @staticmethod
  def display_values_pie(pct, allvals):
    absolute = int(pct/100.*np.sum(allvals))
    return "{:.1f}%\n({:d})".format(pct, absolute)

if __name__ == "__main__":
  generator = GraphsGenerator("/home/legton/pmec/metabase-reports/")
  generator.generate_graphs()
