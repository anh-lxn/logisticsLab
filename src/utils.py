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

def get_transport_demands():
  _, transport_demand = read_txt_files()
  return transport_demand

def create_dict_of_transport_demands():
  num_machines = transport_demand["start"].nunique()
  dict_transport_demands = {}
  for i in range(num_machines):
    df = transport_demand[transport_demand["start"] == i + 1]
    summe = df["number"].sum()
    dict_transport_demands[i + 1] = summe
  return dict_transport_demands

transport_demand = get_transport_demands()
transport_demands_dict = create_dict_of_transport_demands()

def decrease_transport_demand(start_machine, dest_machine, amount=1):
  condition = (transport_demand["start"] == start_machine) & (transport_demand["dest"] == dest_machine) # Zeile bei der es True ist
  transport_demand.loc[condition, "number"] -= amount

def check_left_transport_demands(location):
  global transport_demands_dict
  if transport_demands_dict[location] > 0:
    return True
  else:
    return False

def check_if_transport_possible(start_machine, dest_machine):
  condition = (transport_demand["start"] == start_machine) & (transport_demand["dest"] == dest_machine)
  demand_row = transport_demand.loc[condition]
  if not demand_row.empty and demand_row.iloc[0]["number"] > 0:
    return True
  else:
    return False


def calculate_total_transport_demands():
  #transport_demand = get_transport_demands()
  total_demands = transport_demand["number"].sum()
  return total_demands

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

# Funktion zum Testen, kann weg dann
def calculate_least_distance_route(start_machine):
  machine_positions, _ = read_txt_files()
  num_machines = len(machine_positions)
  distances = {}
  for i in range(num_machines):
    if calculate_distances(start_machine, i+1) != 0: # Diagonalen auschließen, da Distanz zu sich selbst 0 ist
      distances[i+1] = calculate_distances(start_machine, i+1)
  least_distance = min(distances.values())
  dest_machine = min(distances, key=distances.get)
  return dest_machine, least_distance

schedule = pd.DataFrame(columns=["VehicleId", "Location", "unload", "load"])
count = 0
sum_of_transports_demands = calculate_total_transport_demands()

def calculate_best_route(carID, start_machine, unload, load):
  global count
  global sum_of_transports_demands
  if sum_of_transports_demands > 200:
    schedule.loc[count] = [carID, start_machine, unload, load]
    #transport_demands = get_transport_demands()
    routes_for_start_machine = transport_demand[transport_demand["start"] == start_machine] # alle Routen die am start_machine beginnen
    num_demands = len(routes_for_start_machine)
    distances = {}
    for i in range(num_demands):
      dest_machine = routes_for_start_machine.iloc[i]["dest"]
      if calculate_distances(start_machine, dest_machine) != 0 and check_if_transport_possible(start_machine, dest_machine) and check_left_transport_demands(dest_machine): # falls start = 1 und dest = 1, was aber keinen Sinn ergibt, aber trotzdem Fehler auffangen
        distances[dest_machine] = calculate_distances(start_machine, dest_machine)
    try:
      #least_distance = min(distances.values())
      best_machine = min(distances, key=distances.get)
    except ValueError:
      transport_demand.to_csv("test.csv", index=False)
      print(start_machine)
    decrease_transport_demand(start_machine, best_machine)

    count += 1
    sum_of_transports_demands -= 1
    return calculate_best_route(carID, best_machine, unload, load)
  else:
    print("All transport demands completed.")
    print(schedule)

calculate_best_route(1, 1, False, True)



#plot_machine_positions()
