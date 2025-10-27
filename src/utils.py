import os
import pandas as pd

# relative Pfade
git_dir = os.getcwd()
data_dir = os.path.join(git_dir, 'data')
machine_positions_path = os.path.join(data_dir, "machine_positions.txt")
transport_demand_path = os.path.join(data_dir, "transport_demand_smaller.txt")

def read_txt_files():
  machine_positions= pd.read_csv(machine_positions_path, sep=r";", names =["machine_id", "x", "y"], header=0)
  transport_demand= pd.read_csv(transport_demand_path, sep=";")
  return machine_positions, transport_demand
