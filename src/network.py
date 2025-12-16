import pandas as pd
import numpy as np
from IPython.display import display


class Network:
  def __init__(self, machine_positions, transport_demand):
    self.machine_positions = machine_positions.copy()
    self.transport_demand = transport_demand.copy()
    self.dist_matrix = self.calculate_distance_matrix()
    self.time_matrix = self.calculate_time_matrix()

  # Distances
  def calculate_distance_matrix(self, display_distance_matrix=False):
    cross = self.machine_positions.merge(self.machine_positions, how="cross", suffixes=("_i", "_j")) # Crossproduct of Machine Positions
    cross["dist"] = np.sqrt((cross["x_i"] - cross["x_j"])**2 + (cross["y_i"] - cross["y_j"])**2) # Euclidean Distance
    self.dist_matrix = cross.pivot(index="machine_id_i", columns="machine_id_j", values="dist") # Conversion to matrix form
    if display_distance_matrix:
      display(self.dist_matrix.round(2))
    return self.dist_matrix.round(2)

  def get_distance_between(self, start_machine, dest_machine):
    return self.dist_matrix.loc[start_machine, dest_machine]

  # Time
  def calculate_time_matrix(self, velocity=1, display_time_matrix=False):
    self.time_matrix = self.dist_matrix / velocity
    if display_time_matrix:
      display(self.time_matrix.round(2))
    return self.time_matrix

  def get_time_between(self, start_machine, dest_machine):
    return self.time_matrix.loc[start_machine, dest_machine]

  # Helpers
  def decrease_transport_demand(self, start_machine, dest_machine, amount=1):
    condition = (self.transport_demand["start"] == start_machine) & (self.transport_demand["dest"] == dest_machine)
    self.transport_demand.loc[condition, "number"] -= amount
    self._update_transport_demand()

  def get_total_transport_demands(self):
    return self.transport_demand["number"].sum()

  def _update_transport_demand(self): # static
    self.transport_demand = self.transport_demand[self.transport_demand["number"] != 0].reset_index(drop=True) # updating so there is no 0 demand in the dataframe

  # Prints
  def display_network(self):
    self.calculate_distance_matrix(display_distance_matrix=True)
    self.calculate_time_matrix(display_time_matrix=True)
    display(self.transport_demand)

