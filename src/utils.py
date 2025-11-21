import os
import pandas as pd
import matplotlib.pyplot as plt

# relative Pfade
git_dir = os.path.dirname(os.getcwd())
data_dir = os.path.join(git_dir, 'data')
docs_dir = os.path.join(git_dir, 'docs')
machine_positions_path = os.path.join(data_dir, "machine_positions.txt")
transport_demand_path = os.path.join(data_dir, "transport_demand.txt")
scores_path = os.path.join(data_dir, "scores.csv")
output_path = os.path.join(docs_dir, "scores_plot.png")
df = pd.read_csv(scores_path)

def read_txt_files():
  machine_positions = pd.read_csv(machine_positions_path, sep=r";", names =["machine_id", "x", "y"], header=0)
  transport_demand = pd.read_csv(transport_demand_path, sep=";")
  return machine_positions, transport_demand

def save_schedule(schedule, filename):
  schedule.to_csv(os.path.join(data_dir, filename), index=False)

def plot_scores():
  scores = pd.read_csv(scores_path)
  plt.bar(scores["num_cars"], scores["score"], width=2)
  plt.xticks(scores["num_cars"])
  plt.title("Heuristic Solution")
  plt.xlabel("Number of Cars")
  plt.ylabel("Score")
  plt.tight_layout()
  plt.savefig(output_path)

#plot_scores()