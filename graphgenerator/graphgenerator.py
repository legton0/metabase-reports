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
    time_diff = timedelta(seconds=0)
    date_columns = date_columns.split(',')

    for col in date_columns:
      try:
        df[col] = pandas.to_datetime(df[col])
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
      except Exception as e:
        print(e.__class__.__name__ + ":")
        print(str(e))
        print("Couldn't parse date")
        pass

  def generate_graph(self):
    if (self.name != "" or self.description != ""):
      plt.suptitle(self.name, y=1.1, fontsize=15)
      plt.title(self.description, y=1.1, fontsize=13)
    print("Storing in " + self.save_path + ".png\n")
    plt.savefig(self.save_path, bbox_inches = 'tight', pad_inches = 0.2)
    plt.clf()

class Pie(Graph):
  def __init__(self, name, information):
    Graph.__init__(self, name, information)
    self.start_angle = self.get_optional_value(self.information, "start_angle", default_value=0)
    self.dont_show_values = self.get_optional_value(self.information, "dont_show_values", default_value=None)
    self.labels_csv_column = self.information["labels"]
    self.values_csv_column = self.information["values"]
    self.labels = self.csv[self.labels_csv_column].tolist()
    self.values = self.csv[self.values_csv_column].tolist()

  def generate_graph(self):
    fig, ax = plt.subplots()
    if (self.dont_show_values != None):
      plt.pie(self.values, labels=self.labels, autopct='%1.1f%%', startangle=self.start_angle)
    else:
      plt.pie(self.values, labels=self.labels, autopct=lambda pct: self.display_values_pie(pct, self.values), startangle=self.start_angle)
    plt.axis('equal')
    super(Pie, self).generate_graph()

  def display_values_pie(self, pct, allvals):
    absolute = int(pct/100.*np.sum(allvals))
    return "{:.1f}%\n({:d})".format(pct, absolute)

class Table(Graph):
  def __init__(self, name, information):
    Graph.__init__(self, name, information)
    self.display_header = self.get_optional_value(self.information, "display_header", default_value=None)
    self.invert_header_color = self.get_optional_value(self.information, "invert_header_color", default_value=None)
    self.headers = self.information["headers"].split(',')
    self.table = None

  def generate_graph(self):
    self.table.scale(2, 2)
    #ax.spines['top'].set_visible(False)
    #ax.spines['right'].set_visible(False)
    super(Table, self).generate_graph()

class HorizontalTable(Table):
  def __init__(self, name, information):
    Table.__init__(self, name, information)
    self.columns = []
    self.columns_size = 0
    self.read_columns()
    self.colors = None
    if (self.invert_header_color != None and self.display_header != None):
      self.generate_cell_colors()

  def read_columns(self):
    for header in self.headers:
      column = self.csv[header].tolist()
      if (self.columns_size == 0):
        self.columns_size = len(column)
      if (self.display_header != None):
        column_with_header = [header] + column
        self.columns.append(column_with_header)
      else:
        self.columns.append(column)

  def generate_cell_colors(self):
    n_colors = range(self.columns_size)
    self.colors = [["k"] + ["w" for x in n_colors], ["k"] + ["w" for y in n_colors]]

  def color_cell_text(self):
    n_headers = range(len(self.headers))
    for i in n_headers:
      self.table._cells[(i, 0)]._text.set_color('w')
      i += 1

  def generate_graph(self):
    fig, ax = plt.subplots()
    ax.axis('off')
    fig.set_figheight(2, forward=False)
    figwidth = 3 + (3 * math.ceil(self.columns_size / 5))
    fig.set_figwidth(figwidth, forward=False)
    if (self.colors != None):
      self.table = plt.table(cellText=self.columns, loc='center', cellLoc='center', cellColours=self.colors)
      self.color_cell_text()
    else:
      self.table = plt.table(cellText=self.columns, loc='center', cellLoc='center')
    super(HorizontalTable, self).generate_graph()

class VerticalTable(Table):
  def __init__(self, name, information):
    Table.__init__(self, name, information)
    self.rows = []
    self.rows_size = 0
    self.read_rows()
    self.colors = None
    if (self.invert_header_color != None and self.display_header != None):
      self.generate_cell_colors()

  def read_rows(self):
    rows = []
    for header in self.headers:
      row = self.csv[header].tolist()
      if (self.rows_size == 0):
        self.rows_size = len(row)
      rows.append(row)
    i = 0
    while i < self.rows_size:
      self.rows.append([])
      for row in rows:
        self.rows[i].append(row[i])
      i += 1
    if (self.display_header != None):
      self.rows = [self.headers] + self.rows

  def generate_cell_colors(self):
    n_colors = range(self.rows_size)
    colors = []
    for i in n_colors:
      colors.append(["w", "w"])
    n_headers = range(len(self.headers))
    header_colors = []
    for i in n_headers:
      header_colors.append("k")
    self.colors = [header_colors] + colors

  def color_cell_text(self):
    n_headers = range(len(self.headers))
    for i in n_headers:
      self.table._cells[(0, i)]._text.set_color('w')
      i += 1

  def generate_graph(self):
    fig, ax = plt.subplots()
    ax.axis('off')
    figheight = 1.5 + (1.5 * math.ceil(self.rows_size / 5))
    fig.set_figheight(figheight, forward=False)
    if (self.colors != None):
      self.table = plt.table(cellText=self.rows, loc='center', cellLoc='center', cellColours=self.colors)
      self.color_cell_text()
    else:
      self.table = plt.table(cellText=self.rows, loc='center', cellLoc='center')
    super(VerticalTable, self).generate_graph()

class GraphSubclass(Graph):
  def __init__(self, name, information):
    Graph.__init__(self, name, information)
    self.rotation = self.get_optional_value(self.information, "rotation", default_value=0)
    self.filter = self.get_optional_value(self.information, "filter", default_value=None)
    self.x, self.x_data, self.x_label = self.get_x_data()
    if (self.filter != None):
      self.x_data = list(dict.fromkeys(self.x_data))
      self.y, self.y_data, self.y_label = self.filter_y_data()
    else:
      self.y, self.y_data, self.y_label = self.get_y_data()
    #Remover depois:
    self.label_rotation = self.get_optional_value(self.information, "label_rotation", default_value=0)
    self.t_headers = self.get_optional_value(self.information, "headers", default_value=None)
    self.t_invert = self.get_optional_value(self.information, "invert_headers_colors", default_value=None)
    self.p_no_values = self.get_optional_value(self.information, "no_values", default_value=None)

  def generate_graph(self):
    fig, ax = plt.subplots()
    if (self.type == 'bar'):
      bars = plt.bar(self.x_data, self.y_data, align="center", color=self.colors)
      plt.xticks(rotation=self.rotation)
      plt.gcf().subplots_adjust(left=0.3, right=0.7)
      plt.gcf().set_size_inches(30, plt.gcf().get_size_inches()[1])

      plt.xlabel(self.x_label)
      plt.ylabel(self.y_label)

      self.display_label_bar(ax, bars, rotation=self.label_rotation)
    elif (self.type == 'horizontal_bar'):
      bars = plt.barh(self.y_data, self.x_data, align="center", color=self.colors)
      plt.xticks(rotation=self.rotation)
      plt.gcf().subplots_adjust(left=0.3, right=0.7)
      plt.gcf().set_size_inches(15, plt.gcf().get_size_inches()[1])

      plt.xlabel(self.x_label)
      plt.ylabel(self.y_label)

      self.display_label_barh(ax, bars, rotation=self.label_rotation)
    elif (self.type == 'pie'):
      if (self.p_no_values != None):
        plt.pie(self.y_data, labels=self.x_data, autopct='%1.1f%%', startangle=self.rotation)
      else:
        plt.pie(self.y_data, labels=self.x_data, autopct=lambda pct: self.display_values_pie(pct, self.y_data), startangle=self.rotation)
      plt.axis('equal')
    elif (self.type == 'line'):
      random.seed(9000)
      for y, data in self.y_data.items():
        f1 = random.random()
        f2 = random.random()
        f3 = random.random()
        plt.plot(self.x_data, data, color=(f1,f2,f3), linewidth=2, label=y, marker='o')
      plt.legend()
      plt.xticks(rotation=self.rotation)
    elif (self.type == 'horizontal_table'):
      ax.axis('off')
      fig.set_figheight(2, forward=False)
      figwidth = 3 + (3 * math.ceil(len(self.x_data) / 5))
      fig.set_figwidth(figwidth, forward=False)
      colors = []
      if (self.t_headers != None):
        cell_text = [[self.x_label] + self.x_data, [self.y_label] + self.y_data]
        if (self.t_invert != None):
          colors = [["k"] + ["w" for x in self.x_data], ["k"] + ["w" for y in self.y_data]]
          the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center', cellColours=colors)
          the_table._cells[(0, 0)]._text.set_color('w')
          the_table._cells[(1, 0)]._text.set_color('w')
        else:
          the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center')
      else:
        cell_text = [self.x_data, self.y_data]
        the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center')
      the_table.scale(2, 2)
    elif (self.type == 'vertical_table'):
      ax.axis('off')
      figheight = 1.5 + (1.5 * math.ceil(len(self.x_data) / 5))
      fig.set_figheight(figheight, forward=False)
      colors = []
      cell_text = []
      i = 0
      while i < len(self.x_data):
        colors.append(["w", "w"])
        cell_text.append([])
        cell_text[i].append(self.x_data[i])
        cell_text[i].append(self.y_data[i])
        i += 1
      if (self.t_headers != None):
        cell_text = [[self.x_label, self.y_label]] + cell_text
        if (self.t_invert != None):
          colors = [["k", "k"]] + colors
          the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center', cellColours=colors)
          the_table._cells[(0, 0)]._text.set_color('w')
          the_table._cells[(0, 1)]._text.set_color('w')
        else:
          the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center')
      else:
        the_table = plt.table(cellText=cell_text, loc='center', cellLoc='center')
      the_table.scale(2, 2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    super(GraphSubclass, self).generate_graph()

  def display_label_bar(self, ax, bars, rotation=0):
    max_y_value = ax.get_ylim()[1]
    distance = max_y_value * 0.01
    for bar in bars:
      text = bar.get_height()
      text_x = bar.get_x() + bar.get_width() / 2
      text_y = bar.get_height() + distance
      ax.text(text_x, text_y, text, ha='center', va='bottom', rotation=rotation)

  def display_label_barh(self, ax, bars, rotation=0):
    max_x_value = ax.get_xlim()[1]
    distance = max_x_value * 0.0025
    for bar in bars:
      text = bar.get_width()
      text_y = bar.get_y() + bar.get_height() / 2
      text_x = bar.get_width() + distance
      ax.text(text_x, text_y, text, va='center', rotation=rotation)

  def display_values_pie(self, pct, allvals):
    absolute = int(pct/100.*np.sum(allvals))
    return "{:.1f}%\n({:d})".format(pct, absolute)

  def get_x(self):
    # if (self.information["type"] == "bar"):
    #   x = self.information["columns"]
    # elif (self.information["type"] == "line_with_filter"):
    #   x = self.information["columns"]
    # elif (self.information["type"] == "line"):
    #   x = self.information["columns"]
    # elif (self.information["type"] == "pie"):
    #   x = self.information["labels"]
    x = self.information["x"]
    return x

  def get_x_data(self):
    x = self.get_x()
    x_data = self.csv[x].tolist()
    label_x = self.get_optional_value(self.information, "label_x", default_value=x)
    return x, x_data, label_x

  def get_y(self):
    # if (self.information["type"] == "bar"):
    #   y = self.information["rows"]
    # elif (self.information["type"] == "line_with_filter"):
    #   y = self.information["rows"]
    # elif (self.information["type"] == "line"):
    #   return self.information["y_columns"].split(',')
    # elif (self.information["type"] == "pie"):
    #   y = self.information["data"]
    if (self.information["type"] == "line"):
      return self.information["y"].split(',')
    y = self.information["y"]
    return y

  def get_y_data(self):
    y = self.get_y()
    if isinstance(y, list):
      label_y = self.get_optional_value(self.information, "label_y", default_value=y)
      if not isinstance(label_y, list):
        label_y = label_y.split(',')
      y_data = {}
      i = 0
      while (i < len(y)):
        y_data[label_y[i]] = self.csv[y[i]].tolist()
        i+=1
    else:
      label_y = self.get_optional_value(self.information, "label_y", default_value=y)
      y_data = self.csv[y].tolist()
    return y, y_data, label_y

  def filter_y_data(self):
    y, y_data, label_y = self.get_y_data()
    f_data = self.csv[self.filter].tolist()
    label_f = self.get_optional_value(self.information, "label_filter", default_value=None)
    if (label_f != None):
      label_f = label_f.split(',')
      label_f.reverse()
    f_values = list(dict.fromkeys(f_data))
    new_y_data = {}
    for y, data in y_data.items():
      for f in f_values:
        if (label_f == None):
          key = y + "_" + self.filter + ":" + str(f)
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
      graph_type = graph_info["type"]
      print("Generating " + graph_name + " graph")
      if (graph_type == "pie"):
        graph_test = Pie(graph_name, graph_info)
      elif (graph_type == "horizontal_table"):
        graph_test = HorizontalTable(graph_name, graph_info)
      elif (graph_type == "vertical_table"):
        graph_test = VerticalTable(graph_name, graph_info)
      else:
        graph_test = GraphSubclass(graph_name, graph_info)
      graph_test.generate_graph()

if __name__ == "__main__":
  generator = GraphsGenerator("/home/legton/pmec/metabase-reports/")
  generator.generate_graphs()
