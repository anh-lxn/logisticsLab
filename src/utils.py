import pandas as pd
import numpy as np
import os

import matplotlib.pyplot as plt


# relative Pfade
git_dir = os.getcwd()
data_dir = os.path.join(git_dir, 'data')
machine_positions_path = os.path.join(data_dir, "machine_positions.txt")
transport_demand_path = os.path.join(data_dir, "transport_demand.txt")

def read_txt_files():
  machine_positions= pd.read_csv(machine_positions_path, sep=r";", names =["machine_id", "x", "y"], header=0)
  transport_demand= pd.read_csv(transport_demand_path, sep=";")
  transport_demand["id"] = transport_demand.index + 1
  transport_demand = transport_demand[["id", "start", "dest", "number"]] # sortiert um, da id am Ende war
  return machine_positions, transport_demand

def get_positions_of_machines():
  machine_positions, _ = read_txt_files()
  ids = machine_positions["machine_id"].values
  x = machine_positions["x"].values
  y = machine_positions["y"].values
  return ids, x, y

def plot_machine_positions():
  ids, x, y = get_positions_of_machines()
  plt.scatter(x, y, s=100, c='red', marker='x')
  plt.xlabel("x")
  plt.ylabel("y")
  plt.xlim([0, 70])
  plt.ylim([0, 45])
  plt.xticks(np.arange(0, 70, 5))
  plt.yticks(np.arange(0, 45, 5))
  plt.title("Maschinenpositionen")
  plt.grid()
  for id, xi, yi in zip(ids, x, y):
      plt.text(xi + 1, yi + 1, id, fontsize=15)
  plt.show()

def calculate_distances(m1, m2):
  machine_positions, _ = read_txt_files()
  cross = machine_positions.merge(machine_positions, how="cross", suffixes=("_i", "_j")) # Kreuzprodukt der Maschinenpositionen
  cross["dist"] = np.sqrt((cross["x_i"] - cross["x_j"])**2 + (cross["y_i"] - cross["y_j"])**2) # euklidische Distanz
  dist_matrix = cross.pivot(index="machine_id_i", columns="machine_id_j", values="dist") # Umwandlung in Matrixform
  return dist_matrix.loc[m1, m2]

#plot_machine_positions()